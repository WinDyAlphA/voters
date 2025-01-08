from rfc7748 import x25519, add, sub, computeVcoordinate, mult
from random import randint
from algebra import mod_inv
from secrets import randbelow  # Ajout d'une meilleure source d'aléa


# Courbe curve25519 paramètres
p = 2**255 - 19
Gu = 9  # Point de base (coordonnée u)
Gv = computeVcoordinate(Gu)  # Coordonnée v du point de base

def ECencode(m):
    """
    Encode un message 0 ou 1 en point sur la courbe
    0 -> Point à l'infini (1,0)
    1 -> Point de base G
    """
    if m == 0:
        return (1, 0)
    elif m == 1:
        return (Gu, Gv)
    else:
        raise ValueError("Message must be 0 or 1")

def EC_KeyGen():
    """
    Génère une paire de clés ElGamal EC
    Retourne (sk, pk) où:
    - sk est la clé privée (entier)
    - pk est la clé publique (point sur la courbe)
    """
    # Clé privée aléatoire
    sk = randbelow(p-2)+1
    
    # Clé publique = sk*G
    pku, pkv = mult(sk, Gu, Gv, p)
    
    return sk, (pku, pkv)

def EC_Encrypt(m, pk):
    """
    Chiffre un message m (0 ou 1) avec la clé publique pk
    Retourne (r, c) où:
    - r est le premier élément du chiffré (point sur la courbe)
    - c est le deuxième élément du chiffré (point sur la courbe)
    """
    # Encode le message en point
    M = ECencode(m)
    
    # Génère un aléa k
    k = randbelow(p-2)+1
    
    # Calcule r = k*G
    ru, rv = mult(k, Gu, Gv, p)
    
    # Calcule s = k*pk
    su, sv = mult(k, pk[0], pk[1], p)
    
    # Calcule c = M + s
    cu, cv = add(M[0], M[1], su, sv, p)
    
    return (ru, rv), (cu, cv)

def EC_Decrypt(r, c, sk):
    """
    Déchiffre (r,c) avec la clé privée sk
    Retourne le point M = c - sk*r
    """
    # Calcule s = sk*r
    su, sv = mult(sk, r[0], r[1], p)
    
    # Calcule M = c - s
    Mu, Mv = sub(c[0], c[1], su, sv, p)
    
    return (Mu, Mv)

def bruteECLog(point):
    """
    Recherche exhaustive pour trouver m tel que point = m*G
    Utilisé pour les petites valeurs de m (0-5)
    """
    current = (1, 0)  # Point à l'infini
    for m in range(6):
        if (current[0], current[1]) == (point[0], point[1]):
            return m
        current = add(current[0], current[1], Gu, Gv, p)
    return None