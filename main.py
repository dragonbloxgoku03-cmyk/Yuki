import discord
from discord import app_commands
from discord.ext import commands
import os
import json 
import re 
import random 
import requests 
from google import genai

# --- CONFIGURATION DES CLÉS ---
DISCORD_TOKEN = os.environ.get("TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

# Client Gemini
client_gemini = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# --- LISTE DES GIFS POUR LA COMMANDE /KISS ---
KISS_GIFS = [
    "https://media.tenor.com/T0b-p-3KzN8AAAAd/anime-kiss.gif",
    "https://media.tenor.com/qL3B_cO9dE0AAAAC/hug-kiss.gif",
    "https://media.tenor.com/qS074J-qKqUAAAAC/couple-cute.gif",
    "https://media.tenor.com/W-b2-v_zYk8AAAAC/kiss-love.gif",
]

# --- FONCTIONS DE GESTION DES FICHIERS ---

def sauvegarder_memoire(memoire):
    with open('memoire.json', 'w', encoding='utf-8') as f:
        json.dump(memoire, f, indent=4)

def charger_memoire():
    try:
        with open('memoire.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} 

def sauvegarder_profils(profils):
    with open('user_profiles.json', 'w', encoding='utf-8') as f:
        json.dump(profils, f, indent=4)

def charger_profils():
    try:
        with open('user_profiles.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} 

# --- ÉVÉNEMENTS DU BOT ---

@bot.event
async def on_ready():
    print(f'🤖 Yuki est en ligne! Connecté en tant que {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées.")
    except Exception as e:
        print(f"❌ Erreur de synchronisation: {e}")

# --- COMMANDES SLASH ---

@bot.tree.command(name='apprendre', description='Apprend une réponse au bot.')
@app_commands.describe(question='La phrase à retenir.', reponse='La réponse de Yuki.')
@app_commands.checks.has_permissions(manage_messages=True) 
async def apprendre_slash(interaction: discord.Interaction, question: str, reponse: str):
    memoire = charger_memoire()
    memoire[question.lower().strip()] = reponse
    sauvegarder_memoire(memoire)
    await interaction.response.send_message(
        f"✅ J'ai retenu la leçon :\n**Question** : `{question}`\n**Réponse** : `{reponse}`"
    )

@bot.tree.command(name='monnom', description='Définit votre prénom/pseudo.')
@app_commands.describe(nom='Votre prénom/pseudo.')
async def monnom_slash(interaction: discord.Interaction, nom: str):
    profils = charger_profils()
    profils[str(interaction.user.id)] = nom.strip()
    sauvegarder_profils(profils)
    await interaction.response.send_message(f"✅ Reçu **{nom.strip()}**, je m'en souviendrai.")

@bot.tree.command(name='ping', description='Affiche le ping du bot.')
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f'Pong! 🛰️ Latence: **{round(bot.latency * 1000)}ms**')

@bot.tree.command(name='dire', description='Fait dire un message au bot.')
@app_commands.describe(message='Le message.')
async def dire_slash(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f"**{message}**")

@bot.tree.command(name='clear', description='Supprime des messages.')
@app_commands.describe(nombre='Nombre de messages.')
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_slash(interaction: discord.Interaction, nombre: int):
    if nombre < 1 or nombre > 100:
        await interaction.response.send_message("Choisis un nombre entre 1 et 100.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True) 
    deleted = await interaction.channel.purge(limit=nombre) 
    await interaction.followup.send(f"🗑️ **{len(deleted)}** messages supprimés.", ephemeral=True)

@bot.tree.command(name='kiss', description='Embrasse un membre.')
@app_commands.describe(membre='Membre ciblé.')
async def kiss_slash(interaction: discord.Interaction, membre: discord.Member):
    if membre.id == interaction.user.id:
        msg = f"**{interaction.user.display_name}** s'embrasse tout seul... 😅"
    elif membre.id == bot.user.id:
        msg = f"Merci **{interaction.user.display_name}** ! 😊"
    else:
        msg = f"**{interaction.user.display_name}** donne un baiser à **{membre.display_name}** ! 😘"
    
    gif = random.choice(KISS_GIFS)
    embed = discord.Embed(title="💖 Baiser !", url=gif, color=discord.Color.red())
    embed.set_image(url=gif)
    await interaction.response.send_message(msg, embed=embed)

# --- GESTION DES MESSAGES ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.user.mentioned_in(message) or "yuki" in message.content.lower():
        profils = charger_profils()
        user_id = str(message.author.id)
        user_name = profils.get(user_id, message.author.display_name)

        # Nettoyage de la question
        question_cle = message.content.lower().strip()
        if bot.user.mentioned_in(message):
            question_cle = re.sub(r'^' + re.escape(bot.user.mention.lower()), '', question_cle).strip()
        elif question_cle.startswith("yuki"):
            question_cle = re.sub(r'^yuki', '', question_cle).strip()
            
        question_cle = question_cle.strip('?!.,:;').strip()

        if not question_cle:
            return

        # 1. Mémoire personnalisée
        memoire = charger_memoire()
        if question_cle in memoire:
            await message.channel.send(memoire[question_cle]) 
            return 

        # 2. Traitement par Gemini
        async with message.channel.typing():
            if client_gemini:
                try:
                    prompt = f"Tu es Yuki, un bot Discord utile et amical. Réponds de façon concise à {user_name} : {message.content}"
                    response = client_gemini.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    await message.channel.send(response.text)
                    return
                except Exception as e:
                    print(f"Erreur Gemini: {e}")

            await message.channel.send(f"Désolée {user_name}, je n'ai pas pu trouver de réponse.")
            return

    await bot.process_commands(message)

if DISCORD_TOKEN is None:
    print("❌ AVERTISSEMENT: La clé 'TOKEN' n'a pas été trouvée.")
