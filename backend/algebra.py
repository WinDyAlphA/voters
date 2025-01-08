import math
from Crypto.Util.number import inverse

def int_to_bytes(n):
    """Converts int to bytes."""
    return n.to_bytes((n.bit_length() + 7) // 8, 'big')

def mod_inv(a, n):
    """Calcule l'inverse modulaire de a modulo n"""
    t, r = 1, a
    new_t, new_r = 0, n

    while new_r != 0:
        quotient = r // new_r
        t, new_t = new_t, t - quotient * new_t
        r, new_r = new_r, r - quotient * new_r

    if r > 1:
        raise Exception("a is not invertible")
    if t < 0:
        t = t + n
    return t

def mod_sqrt(a, p):
    """
    Calcule la racine carrée modulaire de a modulo p
    Utilise l'algorithme de Tonelli-Shanks
    """
    if legendre_symbol(a, p) != 1:
        return 0
    elif a == 0:
        return 0
    elif p == 2:
        return a
    elif p % 4 == 3:
        return pow(a, (p + 1) // 4, p)

    # Décompose p-1 en s * 2^e
    q = p - 1
    s = 0
    while q % 2 == 0:
        q //= 2
        s += 1

    # Trouve un non-résidu quadratique
    z = 2
    while legendre_symbol(z, p) != -1:
        z += 1

    m = s
    c = pow(z, q, p)
    t = pow(a, q, p)
    r = pow(a, (q + 1) // 2, p)

    while t != 1:
        # Trouve le plus petit i tel que t^(2^i) = 1
        i = 0
        temp = t
        while temp != 1 and i < m:
            temp = (temp * temp) % p
            i += 1

        if i == 0:
            return r

        # Calcule b = c^(2^(m-i-1))
        b = c
        for _ in range(m - i - 1):
            b = (b * b) % p

        m = i
        c = (b * b) % p
        t = (t * c) % p
        r = (r * b) % p

    return r

def legendre_symbol(a, p):
    """
    Calcule le symbole de Legendre (a/p)
    Retourne:
     1 si a est un résidu quadratique modulo p
    -1 si a est un non-résidu quadratique modulo p
     0 si a ≡ 0 (mod p)
    """
    if a == 0:
        return 0
    if p == 2:
        return 1
    
    # Théorème d'Euler
    ls = pow(a, (p - 1) // 2, p)
    return -1 if ls == p - 1 else ls
