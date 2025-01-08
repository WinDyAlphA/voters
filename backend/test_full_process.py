import requests
import json
import time

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
    
    try:
        response = requests.post(f"{base_url}/register", json=register_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Échec de l'inscription: {response.text}")
            
        user_token = response.json()["access_token"]
        print("Compte créé et token obtenu")
    except Exception as e:
        raise Exception(f"Erreur lors de l'inscription: {str(e)}")
    
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
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{base_url}/elections/{election_id}/results", headers=headers)
    print(f"Status récupération résultats: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print("\nRésultats du vote:")
        for result in results:
            print(f"{result['candidate_name']}: {result['votes']} votes")
    else:
        print("Erreur lors de la récupération des résultats")

if __name__ == "__main__":
    try:
        test_full_process()
        print("\n✅ Test complet terminé avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {str(e)}") 