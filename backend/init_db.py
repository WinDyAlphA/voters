from database import VotingDatabase
from datetime import datetime, timedelta
from ecelgamal import EC_KeyGen
from passlib.context import CryptContext
import random
import secrets
import string
import sqlite3
import json

# Configuration du hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(db_path: str):
    """Crée un utilisateur administrateur par défaut"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Générer un code d'invitation pour l'admin
    alphabet = string.ascii_letters + string.digits
    admin_code = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    # Générer un voter_id pour l'admin
    admin_voter_id = 'voter_' + ''.join(secrets.choice(alphabet) for _ in range(32))
    
    try:
        # Créer le code d'invitation
        cursor.execute("""
            INSERT INTO invitation_codes (code)
            VALUES (?)
        """, (admin_code,))
        
        # Créer l'utilisateur admin
        admin_password = "admin123"  # À changer en production !
        hashed_password = pwd_context.hash(admin_password)
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, voter_id)
            VALUES (?, ?, ?, ?)
        """, ("admin", "admin@example.com", hashed_password, admin_voter_id))
        
        admin_id = cursor.lastrowid
        
        # Marquer le code comme utilisé par l'admin
        cursor.execute("""
            UPDATE invitation_codes 
            SET used = TRUE, 
                used_at = CURRENT_TIMESTAMP,
                used_by = ?
            WHERE code = ?
        """, (admin_id, admin_code))
        
        conn.commit()
        
        print("\n=== Informations de l'administrateur ===")
        print("Username: admin")
        print("Password: admin123")
        print("Email: admin@example.com")
        print("⚠️  Changez ces informations en production !")
        
    except sqlite3.IntegrityError:
        print("\n⚠️  L'utilisateur admin existe déjà")
    finally:
        conn.close()

def init_test_database():
    """Initialise la base de données avec des données de test"""
    db = VotingDatabase("backend/voting.db")
    
    # Créer l'utilisateur admin
    create_admin_user("backend/voting.db")
    
    # Génération d'une paire de clés pour l'élection
    sk, pk = EC_KeyGen()
    
    # Création d'une élection de test
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    election_id = db.create_election(
        title="Élection du représentant étudiant",
        description="Élection du représentant étudiant pour l'année 2024",
        start_date=start_date,
        end_date=end_date,
        public_key_x=str(hex(pk[0])),
        public_key_y=str(hex(pk[1]))
    )
    
    # Ajout des candidats
    candidates = [
        ("Alice Martin", "Étudiante en 3ème année d'informatique"),
        ("Bob Dupont", "Étudiant en 2ème année de mathématiques"),
        ("Charlie Garcia", "Étudiant en 4ème année de physique")
    ]
    
    for name, description in candidates:
        db.add_candidate(election_id, name, description)
    
    # Ajout de votants de test
    voters = [f"voter_{i}" for i in range(1, 21)]  # 20 votants
    for voter_id in voters:
        db.register_voter(election_id, voter_id)
    
    # Sauvegarder les clés pour le décompte ultérieur
    keys = {
        "secret_key": hex(sk),
        "public_key": {
            "x": hex(pk[0]),
            "y": hex(pk[1])
        }
    }
    with open("backend/election_keys.json", "w") as f:
        json.dump(keys, f, indent=4)
    
    print("=== Initialisation de la base de données terminée ===")
    print(f"Élection créée avec l'ID: {election_id}")
    print(f"Nombre de candidats: {len(candidates)}")
    print(f"Nombre de votants: {len(voters)}")
    print(f"Clé publique de l'élection: ({hex(pk[0])}, {hex(pk[1])})")
    print(f"⚠️ Clé privée (à conserver secrètement): {hex(sk)}")
    
    return election_id, sk, pk

def simulate_some_votes(db, election_id, pk):
    """Simule quelques votes pour tester"""
    from ecelgamal import EC_Encrypt
    
    # Simulation de 10 votes aléatoires
    voters = [f"voter_{i}" for i in range(1, 11)]
    for voter_id in voters:
        if not db.has_voter_voted(election_id, voter_id):
            # Choisir un candidat au hasard (0, 1, ou 2)
            chosen_candidate = random.randint(0, 2)
            
            # Créer un vote pour chaque candidat
            for candidate_index in range(3):
                # 1 pour le candidat choisi, 0 pour les autres
                vote = 1 if candidate_index == chosen_candidate else 0
                
                # Chiffrement du vote
                r, c = EC_Encrypt(vote, pk)
                
                # Stockage du vote
                db.store_vote(
                    election_id,
                    str(hex(r[0])),
                    str(hex(r[1])),
                    str(hex(c[0])),
                    str(hex(c[1]))
                )
            
            # Marquer le votant comme ayant voté
            db.mark_voter_as_voted(election_id, voter_id)
    
    print("\n=== Simulation des votes ===")
    print(f"10 votes aléatoires ont été simulés")

if __name__ == "__main__":
    try:
        # Initialisation de la base de données
        election_id, sk, pk = init_test_database()
        
        # Simulation de quelques votes
        db = VotingDatabase("backend/voting.db")
        simulate_some_votes(db, election_id, pk)
        
        print("\n✅ Base de données initialisée avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {str(e)}") 