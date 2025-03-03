from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timedelta
from database import VotingDatabase
from ecelgamal import EC_KeyGen, EC_Encrypt, EC_Decrypt, bruteECLog, p
from rfc7748 import add
import sqlite3
import json
from jose import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import secrets
import string

app = FastAPI()

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines exactes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation de la base de données
db = VotingDatabase("/app/data/voting.db")

# Configuration de la sécurité
SECRET_KEY = "votre_clé_secrète_très_longue_et_complexe"  # À changer en production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Modèles Pydantic pour la validation des données
class Vote(BaseModel):
    election_id: int
    voter_id: str
    chosen_candidate: int

class Election(BaseModel):
    title: str
    description: str
    start_date: datetime
    end_date: datetime

class Candidate(BaseModel):
    name: str
    description: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    invitation_code: str  # Ajout du code d'invitation

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Fonctions utilitaires
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
        
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise credentials_exception
    return {"id": user[0], "username": user[1], "email": user[2]}

def generate_voter_id():
    """Génère un voter_id unique de 32 caractères"""
    alphabet = string.ascii_letters + string.digits
    return 'voter_' + ''.join(secrets.choice(alphabet) for _ in range(32))

def count_votes(election_id, secret_key, encrypted_votes):
    """Compte les votes en utilisant la propriété homomorphique d'El Gamal
    Pour chaque position i du vecteur (0-4), additionne tous les votes chiffrés
    à cette position, puis déchiffre la somme pour obtenir le nombre total de votes
    pour le candidat i.
    """
    # Initialiser les compteurs pour les 5 candidats
    vote_counts = [0] * 5
    
    # Regrouper les votes par position dans le vecteur
    votes_by_position = {i: [] for i in range(5)}
    
    # Organiser les votes chiffrés (chaque vote génère 5 chiffrements)
    for i in range(0, len(encrypted_votes), 5):
        for pos in range(5):
            if i + pos < len(encrypted_votes):
                vote = encrypted_votes[i + pos]
                votes_by_position[pos].append(vote)
    
    # Pour chaque position, additionner les votes chiffrés et déchiffrer la somme
    for position, encrypted_values in votes_by_position.items():
        if not encrypted_values:
            continue
            
        # Commencer avec le premier vote chiffré
        r_sum = (int(encrypted_values[0][0], 16), int(encrypted_values[0][1], 16))
        c_sum = (int(encrypted_values[0][2], 16), int(encrypted_values[0][3], 16))
        
        # Additionner les votes chiffrés suivants (propriété homomorphique)
        for vote in encrypted_values[1:]:
            r = (int(vote[0], 16), int(vote[1], 16))
            c = (int(vote[2], 16), int(vote[3], 16))
            # Addition homomorphique sur la courbe elliptique
            r_sum = add(r_sum[0], r_sum[1], r[0], r[1], p)
            c_sum = add(c_sum[0], c_sum[1], c[0], c[1], p)
        
        # Déchiffrer la somme
        decrypted_sum_point = EC_Decrypt(r_sum, c_sum, secret_key)
        # Convertir le point en nombre (logarithme discret)
        vote_count = bruteECLog(decrypted_sum_point)
        vote_counts[position] = vote_count
    
    return vote_counts

@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API de vote électronique"}

@app.get("/elections")
async def get_elections():
    """Récupère la liste des élections"""
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, title, description, start_date, end_date, status, public_key_x, public_key_y 
            FROM elections
        """)
        
        elections = cursor.fetchall()
        
        return [{
            "id": e[0],
            "title": e[1],
            "description": e[2],
            "start_date": e[3],
            "end_date": e[4],
            "status": e[5],
            "public_key": {"x": e[6], "y": e[7]}
        } for e in elections]
    finally:
        conn.close()

@app.get("/elections/{election_id}/candidates")
async def get_candidates(election_id: int):
    """Récupère la liste des candidats pour une élection"""
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, description 
            FROM candidates 
            WHERE election_id = ?
        """, (election_id,))
        
        candidates = cursor.fetchall()
        
        return [{
            "id": c[0],
            "name": c[1],
            "description": c[2]
        } for c in candidates]
    finally:
        conn.close()

@app.post("/vote")
async def submit_vote(vote: Vote):
    """Soumet un vote pour une élection
    Pour un vote pour le candidat i, crée un vecteur de 5 valeurs (0 ou 1)
    où seule la position i contient 1. Chaque valeur est chiffrée séparément.
    """
    if db.has_voter_voted(vote.election_id, vote.voter_id):
        raise HTTPException(status_code=400, detail="Vous avez déjà voté pour cette élection")
    
    if not (0 <= vote.chosen_candidate <= 4):
        raise HTTPException(status_code=400, detail="Candidat invalide (doit être entre 0 et 4)")
    
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        # Récupérer la clé publique
        cursor.execute("""
            SELECT public_key_x, public_key_y 
            FROM elections 
            WHERE id = ?
        """, (vote.election_id,))
        
        key_data = cursor.fetchone()
        if not key_data:
            raise HTTPException(status_code=404, detail="Élection non trouvée")
        
        pk = (int(key_data[0], 16), int(key_data[1], 16))
        
        # Créer et chiffrer le vecteur de vote [0,0,0,0,0] avec un 1 à la position choisie
        vote_vector = [1 if i == vote.chosen_candidate else 0 for i in range(5)]
        encrypted_votes = []
        
        # Chiffrer chaque composante du vecteur séparément
        for value in vote_vector:
            r, c = EC_Encrypt(value, pk)
            encrypted_votes.append((r, c))
            
            # Stocker le vote chiffré
            db.store_vote(
                vote.election_id,
                str(hex(r[0])),
                str(hex(r[1])),
                str(hex(c[0])),
                str(hex(c[1]))
            )
        
        # Marquer l'électeur comme ayant voté
        db.mark_voter_as_voted(vote.election_id, vote.voter_id)
        
        return {
            "message": "Vote enregistré avec succès",
            "vote_vector": vote_vector,
            "encrypted_votes": [
                {
                    "r": (hex(r[0]), hex(r[1])),
                    "c": (hex(c[0]), hex(c[1]))
                } for r, c in encrypted_votes
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du vote: {str(e)}")
    finally:
        conn.close()

@app.get("/elections/{election_id}/status")
async def get_election_status(election_id: int):
    """Récupère le statut d'une élection et les résultats si elle est terminée"""
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT status, end_date 
            FROM elections 
            WHERE id = ?
        """, (election_id,))
        
        election_data = cursor.fetchone()
        if not election_data:
            raise HTTPException(status_code=404, detail="Élection non trouvée")
        
        status = election_data[0]
        end_date = datetime.fromisoformat(election_data[1])
        
        # Vérifier si l'élection est terminée
        is_finished = datetime.now() > end_date
        
        response = {
            "status": status,
            "is_finished": is_finished,
            "end_date": end_date.isoformat()
        }
        
        return response
    finally:
        conn.close()

@app.post("/register", response_model=Token)
async def register_user(user: UserCreate):
    """Enregistrement d'un nouvel utilisateur"""
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT username FROM users WHERE username = ? OR email = ?", 
                      (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Username or email already registered"
            )
        
        # Vérifier le code d'invitation
        cursor.execute("""
            SELECT id, used 
            FROM invitation_codes 
            WHERE code = ?
        """, (user.invitation_code,))
        
        invitation = cursor.fetchone()
        print(f"Code d'invitation trouvé: {invitation}")  # Debug
        
        if not invitation:
            raise HTTPException(
                status_code=400,
                detail="Invalid invitation code"
            )
        
        if invitation[1]:  # Si le code a déjà été utilisé
            raise HTTPException(
                status_code=400,
                detail="This invitation code has already been used"
            )
        
        # Générer un voter_id unique
        voter_id = generate_voter_id()
        print(f"Voter ID généré: {voter_id}")  # Debug
        
        # Hasher le mot de passe
        hashed_password = get_password_hash(user.password)
        
        try:
            # Insérer le nouvel utilisateur avec son voter_id
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, voter_id)
                VALUES (?, ?, ?, ?)
            """, (user.username, user.email, hashed_password, voter_id))
            
            user_id = cursor.lastrowid
            print(f"Utilisateur créé avec ID: {user_id}")  # Debug
            
            # Marquer le code d'invitation comme utilisé
            cursor.execute("""
                UPDATE invitation_codes 
                SET used = TRUE, 
                    used_at = CURRENT_TIMESTAMP,
                    used_by = ?
                WHERE id = ?
            """, (user_id, invitation[0]))
            
            conn.commit()
            
            # Créer le token d'accès
            access_token = create_access_token(
                data={"sub": user.username}
            )
            return {"access_token": access_token, "token_type": "bearer"}
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Database error: {str(e)}"
            )
            
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Erreur lors de l'inscription: {str(e)}")  # Debug
        raise HTTPException(
            status_code=400,
            detail=f"Registration error: {str(e)}"
        )
    finally:
        conn.close()

@app.post("/login", response_model=Token)
async def login_json(user: UserLogin):
    """Login utilisateur avec JSON"""
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        print(f"Tentative de connexion pour: {user.username}")  # Debug
        
        # Vérifier les credentials
        cursor.execute("""
            SELECT id, password_hash 
            FROM users 
            WHERE username = ?
        """, (user.username,))
        
        user_data = cursor.fetchone()
        print(f"Données utilisateur trouvées: {user_data}")  # Debug
        
        if not user_data or not verify_password(user.password, user_data[1]):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Créer le token d'accès
        access_token = create_access_token(
            data={"sub": user.username}
        )
        
        response = {"access_token": access_token, "token_type": "bearer"}
        print(f"Réponse login: {response}")  # Debug
        return response
        
    finally:
        conn.close()

@app.get("/users/me")
async def read_users_me(current_user = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur connecté"""
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT voter_id FROM users WHERE id = ?", (current_user["id"],))
        voter_data = cursor.fetchone()
        
        if voter_data:
            current_user["voter_id"] = voter_data[0]
        
        return current_user
    finally:
        conn.close()

@app.post("/admin/generate-invitation", response_model=dict)
async def generate_invitation(current_user: dict = Depends(get_current_user)):
    """Génère un nouveau code d'invitation (réservé aux admins)"""
    # Générer un code aléatoire de 32 caractères
    alphabet = string.ascii_letters + string.digits
    code = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        # Vérifier si l'utilisateur est admin (à implémenter selon vos besoins)
        # Pour l'instant, on suppose que l'utilisateur ID 1 est admin
        if current_user["id"] != 1:
            raise HTTPException(
                status_code=403,
                detail="Only administrators can generate invitation codes"
            )
        
        # Insérer le nouveau code
        cursor.execute("""
            INSERT INTO invitation_codes (code)
            VALUES (?)
        """, (code,))
        
        conn.commit()
        return {"invitation_code": code}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

@app.get("/admin/invitation-codes")
async def list_invitation_codes(current_user: dict = Depends(get_current_user)):
    """Liste tous les codes d'invitation (réservé aux admins)"""
    if current_user["id"] != 1:  # Vérification admin simplifiée
        raise HTTPException(
            status_code=403,
            detail="Only administrators can view invitation codes"
        )
    
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT ic.code, ic.used, ic.created_at, ic.used_at, u.username
            FROM invitation_codes ic
            LEFT JOIN users u ON ic.used_by = u.id
            ORDER BY ic.created_at DESC
        """)
        
        codes = cursor.fetchall()
        return [{
            "code": c[0],
            "used": c[1],
            "created_at": c[2],
            "used_at": c[3],
            "used_by": c[4]
        } for c in codes]
        
    finally:
        conn.close()

@app.get("/elections/{election_id}/encrypted-votes")
async def get_encrypted_votes(
    election_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Récupère tous les votes chiffrés d'une élection (admin seulement)"""
    if current_user["id"] != 1:  # Vérification admin simplifiée
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access encrypted votes"
        )
    
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT r_x, r_y, c_x, c_y
            FROM encrypted_votes
            WHERE election_id = ?
            ORDER BY id ASC
        """, (election_id,))
        
        votes = cursor.fetchall()
        return votes
        
    finally:
        conn.close()

@app.get("/elections/{election_id}/results")
async def get_election_results(
    election_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Récupère et déchiffre les résultats d'une élection (admin seulement)"""
    if current_user["id"] != 1:
        raise HTTPException(
            status_code=403,
            detail="Only administrators can access election results"
        )
    
    conn = sqlite3.connect("/app/data/voting.db")
    cursor = conn.cursor()
    
    try:
        # Récupérer les votes chiffrés
        cursor.execute("""
            SELECT r_x, r_y, c_x, c_y
            FROM encrypted_votes
            WHERE election_id = ?
            ORDER BY id ASC
        """, (election_id,))
        
        encrypted_votes = cursor.fetchall()
        
        # Récupérer les candidats
        cursor.execute("""
            SELECT name
            FROM candidates
            WHERE election_id = ?
            ORDER BY id ASC
        """, (election_id,))
        
        candidates = [row[0] for row in cursor.fetchall()]
        
        if len(candidates) != 5:
            raise HTTPException(
                status_code=400,
                detail="Cette élection n'a pas exactement 5 candidats"
            )
        
        # Charger la clé secrète
        with open("/app/data/election_keys.json", "r") as f:
            keys = json.load(f)
            secret_key = int(keys["secret_key"], 16)
        
        # Compter les votes
        vote_counts = count_votes(election_id, secret_key, encrypted_votes)
        
        # Préparer les résultats
        results = [{
            "candidate_name": candidates[i],
            "votes": count
        } for i, count in enumerate(vote_counts)]
        
        return results
        
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 