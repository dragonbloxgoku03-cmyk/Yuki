from flask import Flask
from threading import Thread
import main
import os
import time
import discord

app = Flask('') # L'application Flask que Render attend

bot_started = False # Variable de contrôle pour ne lancer le bot qu'une seule fois

@app.route('/')
def home():
    global bot_started
    
    # 1. Lance le bot la première fois que Render vérifie cette page
    if not bot_started:
        t = Thread(target=run)
        t.start()
        bot_started = True
        # On utilise une petite pause pour laisser le temps au thread de démarrer
        time.sleep(1) 
        return "Yuki Bot est en cours de lancement... Serveur Web actif pour Render."
    
    # 2. Retourne ce message lors des vérifications subséquentes
    return "Yuki Bot est en ligne et son serveur Web est actif."

def run():
  # Cette fonction lance le bot Discord
  print("Tentative de lancement du bot Yuki...")
  if main.DISCORD_TOKEN:
      try:
          main.bot.run(main.DISCORD_TOKEN)
      except discord.errors.LoginFailure:
          print("ERREUR FATALE: Le TOKEN Discord est invalide. Vérifiez vos variables d'environnement sur Render.")
  else:
      print("ERREUR: Le TOKEN Discord n'est pas disponible pour le lancement.")
