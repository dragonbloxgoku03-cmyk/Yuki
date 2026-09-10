import discord
from discord import app_commands
from discord.ext import commands
import os
import json 
import re 
import random 
import requests 
import wikipedia # Pour l'accès à Wikipedia
import asyncio

# --- CONFIGURATION DES CLÉS ---
# Le bot va chercher ces valeurs dans les variables d'environnement de Render.
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


# --- FONCTIONS POUR LA GESTION DES FICHIERS DE MÉMOIRE ---

def sauvegarder_memoire(memoire):
    """Sauvegarde le dictionnaire de mémoire dans le fichier memoire.json."""
    with open('memoire.json', 'w', encoding='utf-8') as f:
        json.dump(memoire, f, indent=4)

def charger_memoire():
    """Charge le dictionnaire de mémoire depuis le fichier memoire.json."""
    try:
        with open('memoire.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} 

def sauvegarder_profils(profils):
    """Sauvegarde le dictionnaire des profils utilisateur dans le fichier user_profiles.json."""
    with open('user_profiles.json', 'w', encoding='utf-8') as f:
        json.dump(profils, f, indent=4)

def charger_profils():
    """Charge le dictionnaire des profils utilisateur depuis le fichier user_profiles.json."""
    try:
        with open('user_profiles.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} 


# --- FONCTIONS DE RECHERCHE DYNAMIQUE (SILENCIEUSE ET SANS MESSAGES INTERMÉDIAIRES) ---

def search_wikipedia(query):
    """Recherche sur Wikipedia en français et renvoie le résumé et le lien."""
    try:
        wikipedia.set_lang("fr")
        page = wikipedia.page(query, auto_suggest=False) 
        summary = page.content[:400] + ('...' if len(page.content) > 400 else '')
        return page.title, summary, page.url

    except wikipedia.exceptions.PageError:
        return None, None, None
    except wikipedia.exceptions.DisambiguationError:
        return None, None, None
    except Exception as e:
        print(f"Erreur Wikipedia: {e}")
        return None, None, None


def search_google_cse(query):
    """Lance une recherche via Google Custom Search Engine API."""
    if not GOOGLE_API_KEY or not CSE_ID:
        print("Erreur: Clés Google CSE manquantes.")
        return None, None
        
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': CSE_ID,
        'q': query,
        'num': 1,
        'hl': 'fr' 
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if 'items' in data and data['items']:
            first_result = data['items'][0]
            return first_result.get('title'), first_result.get('link')
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur de recherche Google CSE: {e}")
        
    return None, None


# --- ÉVÉNEMENTS DU BOT ---

@bot.event
async def on_ready():
    print(f'🤖 Yuki est en ligne! Connecté en tant que {bot.user}')
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes synchronisées.")
    except Exception as e:
        print(f"❌ Erreur de synchronisation des commandes: {e}")


# --- COMMANDES SLASH AVEC MEMOIRE ET PUBLICITÉ ---

@bot.tree.command(name='apprendre', description='Apprend une nouvelle phrase ou réponse au bot (Nécessite Gérer les messages).')
@app_commands.describe(question='La phrase ou question à retenir.', reponse='La réponse que Yuki doit donner.')
@app_commands.checks.has_permissions(manage_messages=True) 
async def apprendre_slash(interaction: discord.Interaction, question: str, reponse: str):
    
    memoire = charger_memoire()
    question_cle = question.lower().strip()
    memoire[question_cle] = reponse

    sauvegarder_memoire(memoire)
    
    await interaction.response.send_message(
        f"✅ J'ai retenu la leçon suivante :\n"
        f"**Question/Clé** : `{question}`\n"
        f"**Réponse** : `{reponse}`\n",
        ephemeral=False
    )


@bot.tree.command(name='monnom', description='Permet à Yuki de retenir votre nom pour vous appeler par celui-ci.')
@app_commands.describe(nom='Votre prénom ou le nom par lequel vous voulez que Yuki vous appelle.')
async def monnom_slash(interaction: discord.Interaction, nom: str):
    
    profils = charger_profils()
    user_id = str(interaction.user.id)
    profils[user_id] = nom.strip()

    sauvegarder_profils(profils)
    
    await interaction.response.send_message(
        f"✅ Entendu, **{nom.strip()}**. Je m'en souviendrai.",
        ephemeral=False
    )


# --- COMMANDES SLASH DE BASE ---

@bot.tree.command(name='ping', description='Affiche la latence (ping) du bot.')
async def ping_slash(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! 🛰️ Latence: **{latency}ms**', ephemeral=False)

@bot.tree.command(name='dire', description='Fait dire au bot un message public.')
@app_commands.describe(message='Le message que vous voulez que Yuki dise.')
async def dire_slash(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f"**{message}**", ephemeral=False)

@bot.tree.command(name='clear', description='Supprime un nombre spécifié de messages (Nécessite Gérer les messages).')
@app_commands.describe(nombre='Le nombre de messages à supprimer.')
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_slash(interaction: discord.Interaction, nombre: int):
    
    if nombre < 1 or nombre > 100:
        await interaction.response.send_message("Veuillez choisir un nombre entre 1 et 100.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True) 
    
    deleted = await interaction.channel.purge(limit=nombre) 
    
    await interaction.followup.send(f"🗑️ J'ai supprimé **{len(deleted)}** messages.", ephemeral=True)


@bot.tree.command(name='kiss', description='Donne un baiser à un utilisateur.')
@app_commands.describe(membre='Le membre à qui donner un baiser.')
async def kiss_slash(interaction: discord.Interaction, membre: discord.Member):
    
    if membre.id == interaction.user.id:
        message = f"**{interaction.user.display_name}** essaie de s'embrasser lui-même. 😅"
    elif membre.id == bot.user.id:
        message = f"Merci **{interaction.user.display_name}**! Ça me fait plaisir. 😊"
    else:
        message = f"**{interaction.user.display_name}** donne un baiser à **{membre.display_name}**! 😘"
        
    gif = random.choice(KISS_GIFS)
    
    embed = discord.Embed(title="💖 Baiser !", url=gif, color=discord.Color.red())
    embed.set_image(url=gif)
    
    await interaction.response.send_message(message, embed=embed)


# --- GESTION DES MESSAGES (PRIORITÉ : Mémoire > Wikipedia > Google CSE) ---

@bot.event
async def on_message(message):
    
    if message.author.bot:
        return
    
    if bot.user.mentioned_in(message) or "yuki" in message.content.lower():
        
        question = message.content 
        
        # 1. VÉRIFICATION DU PROFIL UTILISATEUR
        profils = charger_profils()
        user_id = str(message.author.id)
        user_name = profils.get(user_id, message.author.display_name)


        # 2. NETTOYAGE DE LA QUESTION POUR LA RECHERCHE
        question_cle = question.lower().strip()
        
        if bot.user.mentioned_in(message):
            mention_pattern = re.escape(bot.user.mention.lower())
            question_cle = re.sub(r'^' + mention_pattern, '', question_cle).strip()
        
        elif question_cle.startswith("yuki"):
            question_cle = re.sub(r'^yuki', '', question_cle).strip()
            
        question_cle = question_cle.strip('?!.,:;').strip()

        if not question_cle:
            return

        # 3. VÉRIFICATION DE LA MÉMOIRE STATIQUE (memoire.json)
        memoire = charger_memoire()
        if question_cle in memoire:
            response_text = memoire[question_cle]
            await message.channel.send(f'{response_text}') 
            return 

        # 4. RECHERCHE EN ARRIÈRE-PLAN (SANS MESSAGES INTERMÉDIAIRES)
        async with message.channel.typing():
            
            # Essai Wikipédia
            title, summary, link = search_wikipedia(question_cle)
            
            if link and title:
                embed = discord.Embed(
                    title=f"📚 {title}",
                    description=summary,
                    url=link,
                    color=discord.Color.blue()
                )
                await message.channel.send(embed=embed)
                return
            
            # Essai Google CSE (Si Wikipédia échoue)
            title, link = search_google_cse(question_cle)
            
            if link and title:
                await message.channel.send(
                    f"🔍 **{title}**\n"
                    f"<{link}>"
                )
                return

            # Échec total de la recherche
            else:
                reponse_inconnue = f"Désolée {user_name}, je n'ai rien trouvé pour cette requête sur Wikipédia ou le Web. Tu peux m'apprendre la réponse avec `/apprendre`."
                await message.channel.send(reponse_inconnue)
                return
            
    await bot.process_commands(message)

# --- LANCEMENT DU BOT (DÉCLENCHÉ PAR server.py OU DIRECTEMENT) ---

if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("❌ AVERTISSEMENT: La clé 'TOKEN' (Discord) n'a pas été trouvée dans les variables d'environnement.")
