from ecelgamal import EC_KeyGen, EC_Encrypt, EC_Decrypt, bruteECLog, p
from rfc7748 import add

def test_single_encryption():
    print("\n=== Test d'un chiffrement/déchiffrement simple ===")
    # Génération des clés
    sk, pk = EC_KeyGen()
    print(f"Clé privée générée: {hex(sk)}")
    print(f"Clé publique générée: ({hex(pk[0])}, {hex(pk[1])})")
    
    # Test avec message = 1
    message = 1
    print(f"\nChiffrement du message: {message}")
    
    # Chiffrement
    r, c = EC_Encrypt(message, pk)
    print(f"Chiffré r: ({hex(r[0])}, {hex(r[1])})")
    print(f"Chiffré c: ({hex(c[0])}, {hex(c[1])})")
    
    # Déchiffrement
    decrypted_point = EC_Decrypt(r, c, sk)
    decrypted_message = bruteECLog(decrypted_point)
    print(f"Message déchiffré: {decrypted_message}")
    
    assert message == decrypted_message, "Erreur: le déchiffrement a échoué!"

def test_homomorphic_addition():
    print("\n=== Test de la propriété homomorphique additive ===")
    
    # Messages de test comme dans le readme
    messages = [1, 0, 1, 1, 0]  # Somme attendue = 3
    print(f"Messages à chiffrer: {messages}")
    
    # Génération des clés
    sk, pk = EC_KeyGen()
    
    # Chiffrement de tous les messages
    encrypted_messages = [EC_Encrypt(m, pk) for m in messages]
    
    # Addition homomorphique des chiffrés
    r_sum = encrypted_messages[0][0]  # Premier r
    c_sum = encrypted_messages[0][1]  # Premier c
    
    # Addition des autres chiffrés
    for r, c in encrypted_messages[1:]:
        r_sum = add(r_sum[0], r_sum[1], r[0], r[1], p)
        c_sum = add(c_sum[0], c_sum[1], c[0], c[1], p)
    
    # Déchiffrement de la somme
    decrypted_sum_point = EC_Decrypt(r_sum, c_sum, sk)
    decrypted_sum = bruteECLog(decrypted_sum_point)
    
    print(f"Somme déchiffrée: {decrypted_sum}")
    assert decrypted_sum == 3, "Erreur: la somme devrait être 3!"

if __name__ == "__main__":
    try:
        # Test du chiffrement/déchiffrement simple
        test_single_encryption()
        
        # Test de l'addition homomorphique
        test_homomorphic_addition()
        
        print("\n✅ Tous les tests ont réussi!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}") 