# Image de base Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Créer les dossiers nécessaires
RUN mkdir -p /app/data

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY . .

# Donner les permissions nécessaires
RUN chmod -R 777 /app/data

# Exposer le port
EXPOSE 8000

# Commande pour initialiser la base de données et démarrer l'API
CMD ["sh", "-c", "python init_db.py && python api.py"] 