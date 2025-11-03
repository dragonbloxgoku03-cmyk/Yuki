# Utiliser l'image de base Python 3.11
FROM python:3.11-slim

# Définir le répertoire de travail dans l'image
WORKDIR /app

# Copier le fichier requirements.txt et l'installer en premier (pour la mise en cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le reste du code
COPY . .

# Commande pour démarrer le bot (Ceci lance main.py)
CMD ["python", "main.py"]
