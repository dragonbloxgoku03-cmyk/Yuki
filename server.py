from flask import Flask
from threading import Thread
import main
import os

app = Flask('') # C'est l'objet 'app' que gunicorn cherche

@app.route('/')
def home():
    return "Yuki Bot est en ligne (Serveur Web actif pour Render)."

def run():
  # Lance le bot si le token est présent
  if main.DISCORD_TOKEN:
      main.bot.run(main.DISCORD_TOKEN)
  else:
      print("Erreur: Le Token Discord n'est pas disponible pour le lancement.")


# Lancement du bot dans un thread séparé
# Nous n'avons plus besoin de keep_alive, nous le lançons directement dans un thread
# car gunicorn gère le serveur Flask principal.
t = Thread(target=run)
t.start()

# NOTE: L'objet 'app' (l'application Flask) est maintenant à la racine du fichier,
# ce qui permet à gunicorn de le trouver immédiatement avec la commande 'gunicorn server:app'.
