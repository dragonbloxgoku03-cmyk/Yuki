from flask import Flask
from threading import Thread
import main
import os
import time
import discord

app = Flask('') 

bot_started = False 

@app.route('/')
def home():
    global bot_started
    
    # Lance le bot la première fois que Render vérifie cette page
    if not bot_started:
        t = Thread(target=run)
        t.start()
        bot_started = True
        # Petite pause pour laisser le temps au thread de démarrer
        time.sleep(1) 
        return "Yuki Bot est en cours de lancement... Serveur Web actif pour Render."
    
    return "Yuki Bot est en ligne et son serveur Web est actif."

def run():
  # Cette fonction lance le bot Discord
  print("Tentative de lancement du bot Yuki...")
  if main.DISCORD_TOKEN:
      try:
          main.bot.run(main.DISCORD_TOKEN)
      except discord.errors.LoginFailure:
          # Erreur si le token est mal entré sur Render
          print("ERREUR FATALE: Le TOKEN Discord est invalide. Vérifiez vos variables d'environnement.")
  else:
      # Erreur si la variable TOKEN est manquante sur Render
      print("ERREUR: Le TOKEN Discord n'est pas disponible pour le lancement.")
