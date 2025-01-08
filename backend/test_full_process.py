import requests
import json
import time
from ecelgamal import EC_Decrypt, bruteECLog, p
from rfc7748 import add

def count_votes(election_id, secret_key, nb_candidates, encrypted_votes):
    """Compte les votes pour chaque candidat en utilisant la clé secrète"""
    # Initialiser les compteurs pour chaque candidat
    vote_counts = [0] * nb_candidates
    
    # Regrouper les votes par candidat
    votes_by_candidate = {}
    for i in range(nb_candidates):
        votes_by_candidate[i] = []
    
    # Organiser les votes chiffrés par candidat
    for i in range(0, len(encrypted_votes), nb_candidates):
        for j in range(nb_candidates):
            if i + j < len(encrypted_votes):
                vote = encrypted_votes[i + j]
                votes_by_candidate[j].append(vote)
    
    # Déchiffrer et compter les votes pour chaque candidat
    for candidate_id, candidate_votes in votes_by_candidate.items():
        # Pour chaque candidat, additionner tous ses votes chiffrés
        if not candidate_votes:
            continue
            
        r_sum = (int(candidate_votes[0][0], 16), int(candidate_votes[0][1], 16))
        c_sum = (int(candidate_votes[0][2], 16), int(candidate_votes[0][3], 16))
        
        for vote in candidate_votes[1:]:
            r = (int(vote[0], 16), int(vote[1], 16))
            c = (int(vote[2], 16), int(vote[3], 16))
            r_sum = add(r_sum[0], r_sum[1], r[0], r[1], p)
            c_sum = add(c_sum[0], c_sum[1], c[0], c[1], p)
        
        # Déchiffrer la somme
        decrypted_sum_point = EC_Decrypt(r_sum, c_sum, secret_key)
        vote_count = bruteECLog(decrypted_sum_point)
        vote_counts[candidate_id] = vote_count
    
    return vote_counts

def test_full_process():
    base_url = "http://localhost:8000"
    
    # 1. Login en tant qu'admin
    print("\n=== 1. Login Admin ===")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{base_url}/login", json=login_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")  # Ajout pour debug
        
        if response.status_code != 200:
            raise Exception(f"Échec du login: {response.text}")
            
        admin_token = response.json()["access_token"]
        print("Token admin obtenu")
    except Exception as e:
        raise Exception(f"Erreur lors du login admin: {str(e)}")
    
    # 2. Générer un code d'invitation
    print("\n=== 2. Génération code d'invitation ===")
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        response = requests.post(f"{base_url}/admin/generate-invitation", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")  # Ajout pour debug
        
        if response.status_code != 200:
            raise Exception(f"Échec de la génération du code: {response.text}")
            
        invitation_code = response.json()["invitation_code"]
        print(f"Code d'invitation: {invitation_code}")
    except Exception as e:
        raise Exception(f"Erreur lors de la génération du code: {str(e)}")
    
    # 3. Créer un nouveau compte
    print("\n=== 3. Création compte utilisateur ===")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "invitation_code": invitation_code
    }
    
    response = requests.post(f"{base_url}/register", json=register_data)
    print(f"Status: {response.status_code}")
    user_token = response.json()["access_token"]
    print("Compte créé et token obtenu")
    
    # 4. Récupérer les informations de l'utilisateur (notamment son voter_id)
    print("\n=== 4. Récupération infos utilisateur ===")
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{base_url}/users/me", headers=headers)
    print(f"Status: {response.status_code}")
    user_info = response.json()
    voter_id = user_info["voter_id"]
    print(f"Voter ID: {voter_id}")
    
    # 5. Récupérer la liste des élections
    print("\n=== 5. Liste des élections ===")
    response = requests.get(f"{base_url}/elections")
    print(f"Status: {response.status_code}")
    elections = response.json()
    if elections:
        election_id = elections[0]["id"]
        print(f"ID de l'élection: {election_id}")
        
        # 6. Voter
        print("\n=== 6. Soumission du vote ===")
        vote_data = {
            "election_id": election_id,
            "voter_id": voter_id,
            "chosen_candidate": 0  # Vote pour le premier candidat
        }
        
        response = requests.post(f"{base_url}/vote", json=vote_data)
        print(f"Status: {response.status_code}")
        print(f"Réponse: {response.json()}")
    else:
        print("Aucune élection disponible")

    # 7. Récupérer et compter les votes (admin seulement)
    print("\n=== 7. Décompte des votes ===")
    # Récupérer la clé secrète depuis le fichier de configuration ou l'environnement
    with open("backend/election_keys.json", "r") as f:
        keys = json.load(f)
        secret_key = int(keys["secret_key"], 16)
    
    # Récupérer les votes chiffrés
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{base_url}/elections/{election_id}/encrypted-votes", headers=headers)
    print(f"Status récupération votes: {response.status_code}")
    
    if response.status_code == 200:
        encrypted_votes = response.json()
        
        # Récupérer le nombre de candidats
        response = requests.get(f"{base_url}/elections/{election_id}/candidates")
        candidates = response.json()
        nb_candidates = len(candidates)
        
        # Compter les votes
        vote_counts = count_votes(election_id, secret_key, nb_candidates, encrypted_votes)
        
        print("\nRésultats du vote:")
        for i, count in enumerate(vote_counts):
            candidate_name = candidates[i]["name"]
            print(f"{candidate_name}: {count} votes")
    else:
        print("Erreur lors de la récupération des votes")

if __name__ == "__main__":
    try:
        test_full_process()
        print("\n✅ Test complet terminé avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}") 