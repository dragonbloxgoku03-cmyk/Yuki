from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Yuki Bot est en ligne et à l'écoute sur Discord (Port factice actif)."

def run():
    # Démarre le serveur web sur le port requis par Render (via $PORT)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # Lance le serveur dans un thread séparé pour ne pas bloquer le bot
    t = Thread(target=run)
    t.start()
