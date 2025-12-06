from flask import Flask
from threading import Thread
import main # Importe le fichier principal

app = Flask('')

@app.route('/')
def home():
    return "Yuki Bot est en ligne (Serveur Web actif pour Render)."

def run():
  # Cette fonction tente de lancer le bot si le token est présent
  if main.DISCORD_TOKEN:
      main.bot.run(main.DISCORD_TOKEN)
  else:
      print("Erreur: Le Token Discord n'est pas disponible pour le lancement.")

def keep_alive():
    # Lance le bot dans un thread séparé du serveur Flask
    t = Thread(target=run)
    t.start()
    # Démarre le serveur Flask
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

# La variable 'app' est utilisée par gunicorn pour lancer le serveur Flask
# Le lancement du bot se fait via keep_alive() appelé dans le thread Flask
