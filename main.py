import discord
from discord import app_commands
from discord.ext import commands
import os
import json 
import re 
import random 
import requests 
import wikipedia # Pour l'accès à Wikipedia

# --- CONFIGURATION DES CLÉS ---
DISCORD_TOKEN = os.environ.get("TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY") 
CSE_ID = os.environ.get("CSE_ID") 

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

# --- FONCTIONS DE RECHERCHE WIKIPEDIA & GOOGLE (MAX 10 SITES) ---

def search_wikipedia(query):
    """Recherche sur Wikipedia en nettoyant les requêtes complexes."""
    try:
        wikipedia.set_lang("fr")
        
        # Nettoyage des phrases d'amorce pour extraire le mot-clé principal
        query_clean = re.sub(r'^(que\s+veux?\s+dire|c\'est\s+quoi|qu\'est[- ]ce\s+que|définition|def|définir)\s+', '', query, flags=re.IGNORECASE).strip()
        target = query_clean if query_clean else query
        
        # Recherche directe
        try:
            page = wikipedia.page(target, auto_suggest=True)
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
            # Si pas de page exacte, on cherche dans les suggestions fréquentes
            search_results = wikipedia.search(target, results=5)
            if search_results:
                page = wikipedia.page(search_results[0], auto_suggest=False)
            else:
                return None, None, None

        summary = page.content[:400] + ('...' if len(page.content) > 400 else '')
        return page.title, summary, page.url

    except Exception as e:
        print(f"Erreur Wikipedia: {e}")
        return None, None, None


def search_google_cse(query):
    """
    Lance une recherche Google CSE en analysant jusqu'à 10 résultats/sites 
    pour trouver la page web la plus pertinente selon les recherches fréquentes.
    """
    if not GOOGLE_API_KEY or not CSE_ID:
        return None, None
        
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': CSE_ID,
        'q': query,
        'num': 10,  # Parcourt au maximum 10 sites différents sur le thème
        'hl': 'fr'
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        items = data.get('items', [])
        if items:
            # Filtre pour éviter les pages de recherche vides ou incompréhensibles
            for item in items:
                title = item.get('title', '')
                snippet = item.get('snippet', '')
                link = item.get('link', '')
                
                # Vérifie que le résultat contient bien du contenu pertinent
                if link and (title or snippet):
                    return title, link
                    
    except Exception as e:
        print(f"Erreur Google CSE: {e}")
        
    return None, None

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

        # Nettoyage du texte du message
        question_cle = message.content.lower().strip()
        if bot.user.mentioned_in(message):
            question_cle = re.sub(r'^' + re.escape(bot.user.mention.lower()), '', question_cle).strip()
        elif question_cle.startswith("yuki"):
            question_cle = re.sub(r'^yuki', '', question_cle).strip()
            
        question_cle = question_cle.strip('?!.,:;').strip()

        if not question_cle:
            return

        # 1. Vérification dans memoire.json
        memoire = charger_memoire()
        if question_cle in memoire:
            await message.channel.send(memoire[question_cle]) 
            return 

        # 2. Recherche silencieuse
        async with message.channel.typing():
            # Étape A : Essai Wikipédia
            title, summary, link = search_wikipedia(question_cle)
            if link and title:
                embed = discord.Embed(title=f"📚 {title}", description=summary, url=link, color=discord.Color.blue())
                await message.channel.send(embed=embed)
                return
            
            # Étape B : Analyse de 10 résultats Google Web
            title, link = search_google_cse(question_cle)
            if link and title:
                await message.channel.send(f"🔍 **{title}**\n<{link}>")
                return

            # Échec
            await message.channel.send(f"Désolée {user_name}, je n'ai rien trouvé sur Wikipédia ou sur le Web pour cette recherche.")
            return

    await bot.process_commands(message)

if DISCORD_TOKEN is None:
    print("❌ AVERTISSEMENT: La clé 'TOKEN' n'a pas été trouvée.")
    
