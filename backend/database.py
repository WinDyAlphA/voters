import sqlite3
from datetime import datetime

class VotingDatabase:
    def __init__(self, db_file="voting.db"):
        self.db_file = db_file
        self.init_database()

    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Table des utilisateurs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            voter_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Table des élections
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS elections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending',
            public_key_x TEXT,
            public_key_y TEXT
        )
        ''')

        # Table des candidats/options de vote
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (election_id) REFERENCES elections(id)
        )
        ''')

        # Table des votants autorisés
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            voter_id TEXT UNIQUE NOT NULL,
            has_voted BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (election_id) REFERENCES elections(id)
        )
        ''')

        # Table des votes chiffrés
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS encrypted_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            election_id INTEGER,
            r_x TEXT NOT NULL,
            r_y TEXT NOT NULL,
            c_x TEXT NOT NULL,
            c_y TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (election_id) REFERENCES elections(id)
        )
        ''')

        # Table des codes d'invitation
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS invitation_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP,
            used_by INTEGER,
            FOREIGN KEY (used_by) REFERENCES users(id)
        )
        ''')

        conn.commit()
        conn.close()

    def create_election(self, title, description, start_date, end_date, public_key_x, public_key_y):
        """Crée une nouvelle élection"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO elections (title, description, start_date, end_date, public_key_x, public_key_y)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, start_date, end_date, public_key_x, public_key_y))
        
        election_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return election_id

    def add_candidate(self, election_id, name, description):
        """Ajoute un candidat à une élection"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO candidates (election_id, name, description)
        VALUES (?, ?, ?)
        ''', (election_id, name, description))
        
        candidate_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return candidate_id

    def register_voter(self, election_id, voter_id):
        """Enregistre un votant pour une élection"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO voters (election_id, voter_id)
            VALUES (?, ?)
            ''', (election_id, voter_id))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def store_vote(self, election_id, r_x, r_y, c_x, c_y):
        """Enregistre un vote chiffré"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO encrypted_votes (election_id, r_x, r_y, c_x, c_y)
        VALUES (?, ?, ?, ?, ?)
        ''', (election_id, r_x, r_y, c_x, c_y))
        
        vote_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return vote_id

    def get_election_votes(self, election_id):
        """Récupère tous les votes chiffrés pour une élection"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT r_x, r_y, c_x, c_y FROM encrypted_votes
        WHERE election_id = ?
        ''', (election_id,))
        
        votes = cursor.fetchall()
        conn.close()
        return votes

    def mark_voter_as_voted(self, election_id, voter_id):
        """Marque un votant comme ayant voté"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE voters SET has_voted = TRUE
        WHERE election_id = ? AND voter_id = ?
        ''', (election_id, voter_id))
        
        conn.commit()
        conn.close()

    def has_voter_voted(self, election_id, voter_id):
        """Vérifie si un votant a déjà voté"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT has_voted FROM voters
        WHERE election_id = ? AND voter_id = ?
        ''', (election_id, voter_id))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else False 