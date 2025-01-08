from database import VotingDatabase
from datetime import datetime, timedelta
from ecelgamal import EC_KeyGen
from passlib.context import CryptContext
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

def init_database():
    """Initialise la base de données avec la structure minimale"""
    db = VotingDatabase("backend/voting.db")
    
    # Créer l'utilisateur admin
    create_admin_user("backend/voting.db")
    
    # Génération d'une paire de clés pour l'élection
    sk, pk = EC_KeyGen()
    
    # Création d'une élection vide
    start_date = datetime.now()
    end_date = start_date + timedelta(days=7)
    
    election_id = db.create_election(
        title="Nouvelle élection",
        description="Description de l'élection",
        start_date=start_date,
        end_date=end_date,
        public_key_x=str(hex(pk[0])),
        public_key_y=str(hex(pk[1]))
    )
    
    # Ajout des trois candidats
    candidates = [
        ("Alice Martin", "Candidate #1"),
        ("Bob Dupont", "Candidate #2"),
        ("Charlie Garcia", "Candidate #3")
    ]
    
    for name, description in candidates:
        db.add_candidate(election_id, name, description)
    
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
    
    print("\n=== Initialisation de la base de données terminée ===")
    print(f"Élection créée avec l'ID: {election_id}")
    print(f"Nombre de candidats: {len(candidates)}")
    print(f"Clé publique de l'élection: ({hex(pk[0])}, {hex(pk[1])})")
    print(f"⚠️ Clé privée (à conserver secrètement): {hex(sk)}")

if __name__ == "__main__":
    try:
        init_database()
        print("\n✅ Base de données initialisée avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {str(e)}") 