Applied Cryptography: Project
This project requires that you run python. Ensure that you have last versions of files
algebra.py, rfc7748.py, as sent by your teacher. Ensure also that you have installed
pyCryptodome cryptographic library, as explained by your teacher.
Note: several questions are given in this document, they are here as hints to help your
developement tasks.
1 Introduction
Objective of this project is to implement an electronic voting system, based on crypto-
graphic mechanisms. This voting system is simple and covers only a few properties of a
real electronic voting system:
• Vote privacy.
• Vote elligibility.
• Homomorphic tally.
In particular, this voting system does not cover other important properties, such that:
• Voter authentication.
• Proof of valid vote.
• Individual verifiability.
• Universal verifiability.
2 DSA algorithm
Note: these are the same exercices as given during lectures.
2.1 DSA signature implementations
You will find in file dsa.py prototypes for the following algorithms:
• DSA key generation
• DSA signature generation
• DSA signature verification
Assume we use SHA256as hash function and MODP Group 24for public parameters.
For each algorithm, what are the inputs and the outputs, what are their length in bits ?
Complete these implementations with mod_inv algorithm from algebra.py and use the
following imports:
from algebra import mod_inv
from Crypto.Hash import SHA256
from random import randint
2.2 Signature implementation test
We still use SHA256 as hash function and MODP Group 24 for public parameters.
Let m (a message), k (the nonce used in signature generation) and x (signature private
key) defined with:
m = An important message !
k= 0x7e7f77278fe5232f30056200582ab6e7cae23992bca75929573b779c62ef4759
x = 0x49582493d17932dabd014bb712fc55af453ebfb2767537007b0ccff6e857e6a3
Use your implementation of DSA signature algorithm and verify that you obtain (r, s) as
signature, defined with:
r = 0x5ddf26ae653f5583e44259985262c84b483b74be46dec74b07906c5896e26e5a
s = 0x194101d2c55ac599e4a61603bc6667dcc23bd2e9bdbef353ec3cb839dcce6ec1
3 ElGamal encryption algorithm
Note: these are the same exercices as given during lectures.
3.1 Multiplicative version
You will find in file elgamal.py prototypes for the following algorithms:
• ElGamal key generation
• ElGamal encryption
• ElGamal decryption
Assume we use MODP Group 24 for public parameters. For each algorithm, what are
the inputs and the outputs, what are their length in bits ? Complete these implementa-
tions with mod_inv algorithm from algebra.py and use the following imports:
from algebra import mod_inv
from random import randint
3.2 Homomorphic encryption : multiplicative version
We still use MODP Group 24 for public parameters. Let m1 and m2 two messages
defined with:
m1 = 0x2661b673f687c5c3142f806d500d2ce57b1182c9b25bfe4fa09529424b
m2 = 0x1c1c871caabca15828cf08ee3aa3199000b94ed15e743c3
Use your implementation of ElGamal encryption algorithm to encrypt these two messages
and compute the following process, where EG
_Encrypt denotes ElGamal encryption
and EG
_Decrypt denotes ElGamal decryption:
• (r1, c1) = EG
_Encrypt(m1)
• (r2, c2) = EG
_Encrypt(m2)
• Let (r3, c3) = (r1 × r2, c1 × c2)
• Let m3 = EG
_Decrypt(r3, c3)
• Assess m3 = m1 × m2
• Decode m3 with int_to_bytes from algebra.py !
3.3 Homomorphic encryption : additive version
You have implemented ElGamal encryption such that for two messages m1 and m2,
EG
_Encrypt(m1) × EG
_Encrypt(m2) = EG
_Encrypt(m1 × m2).
Explain how you can turn your previous implementation into an additive version, i.e:
EGA
_Encrypt(m1) × EGA
_Encrypt(m2) = EGA
_Encrypt(m1 + m2). Implement
it !
In the context of electronic voting, we will use the additive version of ElGamal where
messages are 0 or 1. We still use MODP Group 24 for public parameters.
Let m1 = 1, m2 = 0, m3 = 1, m4 = 1, m5 = 0 five messages.
Use your implementation of ElGamal encryption algorithm (additive version) to encrypt
these five messages and compute the following process, where EGA
_Encrypt denotes
ElGamal encryption (additive version) and EG
_Decrypt denotes ElGamal decryption:
• (r1, c1) = EGA
_Encrypt(m1)
• (r2, c2) = EGA
_Encrypt(m2)
• (r3, c3) = EGA
_Encrypt(m3)
• (r4, c4) = EGA
_Encrypt(m4)
• (r5, c5) = EGA
_Encrypt(m5)
• Let (r, c) = (r1 × r2 × r3 × r4 × r5, c1 × c2 × c3 × c4 × c5)
• Compute EG
_Decrypt(r, c). Beware that the result of this computation is not
directly m = m1 + m2 + m3 + m4 + m5 ! Indeed you obtain gm and not m (where g is
MODP Group 24 public parameter). But as in this situation m is small, a direct
brute force search is possible. You will find in file elgamal.py an implementation
of a brute force search, named bruteLog. Use it to compute m.
• Assess m = m1 + m2 + m3 + m4 + m5 = 3
4 Elliptic Curves Cryptography
Note: this section is informative only.
Consider RFC 7748 (https://www.rfc-editor.org/rfc/rfc7748). This RFC contains
some python code and some pseudocode. These allow to implement scalar multiplication
in curve25519, which is usually named X25519.
In file rfc7748.py you will find implementations for these functions. They both use an
internal function, named mul, whose pseudocode is given in RFC 7748. Function mul
itself uses another function, named cswap, for which a proposed implementation is given
in file rfc7748.py. Implementation also uses encoding and decoding functions, whose
python code is given in RFC 7748 and in file rfc7748.py.
5 ECDSA signature algorithm
Note: these are new exercices.
5.1 ECDSA signature implementations
In file rfc7748.py you have an optimized implementation of scalar multiplication which
is adapted from RFC 7748. This implementation does not use point addition and point
doubling to ensure security against side-channels attacks. This implementation is usefull
in contexts where ECDH is performed.
However, to compute ECDSA, we need to have access to point addition on the curve. In
file rfc7748.py you will find implementations for three additionnal functions:
• Function add, that implements point addition. Beware that this function also
implements point doubling !
• Function mult, that implements (unoptimized and unprotected) scalar multiplica-
tion. This function uses internally add function.
• Function computeVcoordinate, that computes v coordinate of a point given its u
coordinate (a point on a curve has (u, v) coordinates).
With these functions, you have all material to implement ECDSA signature and veri-
fication algorithms on curve25519. In file ecdsa.py you will find prototypes for the
following algorithms:
• ECDSA key generation
• ECDSA signature generation
• ECDSA signature verification
Assume we use SHA256 as hash function. For each algorithm, what are the inputs
and the outputs, what are their length in bits ? Complete these implementations with
mod_inv algorithm from algebra.py, with add ans mult algorithms from rfc7748.py
and use the following imports:
from rfc7748 import x25519, add, computeVcoordinate, mult
from Crypto.Hash import SHA256
from random import randint
from algebra import mod_inv
5.2 Signature implementation test
We still use SHA256as hash function. Let m (a message), k (the nonce used in signature
generation) and x (signature private key) defined with:
m = A very very important message !
k= 0x2c92639dcf417afeae31e0f8fddc8e48b3e11d840523f54aaa97174221faee6
x = 0xc841f4896fe86c971bedbcf114a6cfd97e4454c9be9aba876d5a195995e2ba8
Use your implementation of ECDSA signature algorithm and verify that you obtain (r, s)
as signature, defined with:
r = 0x429146a1375614034c65c2b6a86b2fc4aec00147f223cb2a7a22272d4a3fdd2
s = 0xf23bcdebe2e0d8571d195a9b8a05364b14944032032eeeecd22a0f6e94f8f33
Check also your signature verification algorithm.
6 EC ElGamal encryption algorithm
Note: these are new exercices.
ElGamalencryptionalgorithmcanbecomputedonellipticcurves. Wewillusecurve25519
implementation from file rfc7748.py to implement this algorithm. Our purpose is to use
it for electronic voting, so messages to encrypt are equal to 0 or 1.
6.1 Implementation
You will find in file ecelgamal.py prototypes for the following algorithms:
• EC ElGamal key generation
• EC ElGamal encryption
• EC ElGamal decryption
In order to perform EC ElGamal encryption, we need to map messages 0 and 1 to points
on the elliptic curve. Furthermore, we need to use points that have an additive property,
as have 0 and 1 for integers. One solution is to map 0 to point at infinity of coordinates
(1, 0) and to map 1 to the base point of the elliptic curve. We also need to use point
substraction in order to compute these functions. In files rfc7748.py and ecelgamal.py
you will find implementation for additionnal functions:
• Function sub, that implements point substraction.
• Function ECencode, that maps 0 and 1 to the correct points on the elliptic curve.
Complete propotypes with mod_inv algorithm from algebra.py, with add, sub and mult
algorithms from rfc7748.py and use the following imports:
from rfc7748 import x25519, add, sub, computeVcoordinate, mult
from random import randint
from algebra import mod_inv
6.2 Homomorphic encryption : additive version
EC ElGamal is already additive ! Explain why !
Let m1 = 1, m2 = 0, m3 = 1, m4 = 1, m5 = 0 five messages.
Use your implementation of EC ElGamal encryption algorithm to encrypt these five mes-
sages and compute the following process, where ECEG
_Encrypt denotes EC ElGamal
encryption and ECEG
_Decrypt denotes EC ElGamal decryption. Beware that in the
process, ri and ci are points on elliptic curve (hence they are composed of two coordi-
nates). Furthermore, + here denotes points addition on elliptic curve !
• (r1, c1) = ECEG
_Encrypt(m1)
• (r2, c2) = ECEG
_Encrypt(m2)
• (r3, c3) = ECEG
_Encrypt(m3)
• (r4, c4) = ECRG
_Encrypt(m4)
• (r5, c5) = ECEG
_Encrypt(m5)
• Let (r, c) = (r1 + r2 + r3 + r4 + r5, c1 + c2 + c3 + c4 + c5)
• Compute ECEG
_Decrypt(r, c). Beware that as before the result of this compu-
tation is not directly m = m1 +m2 +m3 +m4 +m5 ! As before you obtain m×G and
not m (where G is base point of curve25519). But as before, in this situation m is
small, a direct brute force search is possible. You will find in file ecelgamal.py an
implementation of this brute force search, named bruteECLog. Use it to compute
m.
• Assess m = m1 + m2 + m3 + m4 + m5 = 3
7 Electronic Voting
Note: these are new exercices.
With all previous algorithms, you have all material to implement a simple electronic vot-
ing system, that ensures vote privacy and voters’ elligibility.
In this system, assume a voter has to choose between five candidates C1, C2, C3, C4, C5.
A vote for a candidate Ci generates a list composed of 0 (four times) or 1 (one time). In
this system, blank vote is not possible. For example:
• Vote for candidate C1 generates list (1, 0, 0, 0, 0)
• Vote for candidate C2 generates list (0, 1, 0, 0, 0)
• Vote for candidate C4 generates list (0, 0, 0, 1, 0)
7.1 Privacy
To ensure vote privacy, the voting system encrypts each message of the list. Hence
there are five encrypted messages for each vote! Furthermore, to ensure that voters’
choice cannot be linked with their encrypted ballot, the voting system does not decrypt
each voter’s ballot, but use homomorphic property to decrypt the sum of all choices.
Describe the previous process for two voters, e.g with EGA
_Encrypt seen previously.
7.2 Elligility
To ensure elligibility, each voter signs its encrypted ballot with its own signature key
distributed by the voting system. At reception, ballot signature are verified by the voting
system. Hence a ballot finally contains five encrypted messages (as seen before) and a
signature of these five messages ! All asymmetric signature algorithms can be used to
perform this operation.
Depending on the signature algorithm, signature size will be different !
7.3 Implementation
As seen previously, the voting system can either use ElGamal or EC ElGamal encryption
for vote privacy, and DSA or ECDSA signature for voter elligibility. Your work is to
implement all combinations. As before, parameters are the following:
• MODP Group 24 for ElGamal encryption and DSA signature algorithm.
• SHA256 for hash function for DSA and ECDSA signature algorithms.
• curve25519 for EC ElGamal encryption and ECDSA signature algorithms.
To fix parameters, you can assume the following:
• There are ten (10) voters.
• There are five (5) candidates for the election.
Hence you need to implement, for each algorithm:
• Voters’ signature key generation and distribution : one signature key pair for each
voter.
• Ballot generation: each ballot contains 5 encrypted messages.
• Ballot multiplication (for ElGamal) or addition (for EC ElGamal): this generates
5 encrypted messages (one for each candidate).
• Five decryptions and brute force searches to recover election result (number of votes
per candidate).
8 Deliverables
Expected deliverables for this project are:
• Completed files dsa.py, elgamal.py, ecdsa.py and ecelgamal.py.
• An implementation of the described voting system, that uses as import functions
thatyouhaveimplementedinfilesdsa.py,elgamal.py,ecdsa.py andecelgamal.py.
• A report that explains your implementations and your tests. Be prepared to present
your report (see below).
You can work as a team (three students max.).
Due date for implementation and report delivery (on Google Classroom):
January 12th
.
Presentation Dates: January 21th (exact schedule will be defined later).