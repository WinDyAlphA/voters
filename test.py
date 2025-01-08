import requests

headers = {"Authorization": f"Bearer {admin_token}"}
response = requests.post(
    "http://localhost:8000/admin/generate-invitation",
    headers=headers
)
invitation_code = response.json()["invitation_code"]