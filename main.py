import discord
from discord import app_commands
from discord.ext import commands
import os
import json 
import re 
import random 
import requests # Nécessaire pour l'API Serper

# --- CONFIGURATION DES CLÉS ---
DISCORD_TOKEN = os.environ.get("TOKEN")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY") # Clé pour la recherche web stable

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
    # Ajoutez ici d'autres liens de GIF
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

# --- LOGIQUE DE RECHERCHE STABLE (SERPER API) ---

def search_serper(query):
    """Lance une recherche sur Serper API et renvoie le premier résultat."""
    if not SERPER_API_KEY:
        return None, None
        
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query, "gl": "fr", "hl": "fr"})
    headers = {
      'X-API-KEY': SERPER_API_KEY,
      'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if 'organic' in data and data['organic']:
            first_result = data['organic'][0]
            # Utilise un nettoyage de base pour s'assurer que le lien est propre
            link = first_result.get('link').split('&sa=U&')[0] if first_result.get('link') else None
            return first_result.get('title'), link
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur de recherche Serper: {e}")
    except Exception as e:
        print(f"Erreur de traitement JSON Serper: {e}")
        
    return None, None


# --- ÉVÉNEMENTS DU BOT ---

@bot.event
async def on_ready():
    print(f'🤖 Yuki est en ligne! Connecté en tant que {bot.user}')
    
    # Synchronisation des commandes slash
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
    
    # Réponse publique
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
    
    # Réponse publique
    await interaction.response.send_message(
        f"✅ Entendu, **{nom.strip()}**. Je m'en souviendrai. Je ne vous appellerai plus 'cher humain'.",
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
    # Supprime la commande de l'utilisateur et envoie juste le message
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


# --- GESTION DES MESSAGES (RÉPONSES AUTOMATIQUES PAR MÉMOIRE OU RECHERCHE STABLE) ---

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
        if user_id not in profils:
             user_name = "cher humain"


        # 2. NETTOYAGE DE LA QUESTION POUR LA RECHERCHE
        question_cle = question.lower().strip()
        
        if bot.user.mentioned_in(message):
            mention_pattern = re.escape(bot.user.mention.lower())
            question_cle = re.sub(r'^' + mention_pattern, '', question_cle).strip()
        
        elif question_cle.startswith("yuki"):
            question_cle = re.sub(r'^yuki', '', question_cle).strip()
            
        question_cle = question_cle.strip('?!.,:;').strip()


        # 3. VÉRIFICATION DE LA MÉMOIRE STATIQUE (memoire.json)
        memoire = charger_memoire()
        if question_cle in memoire:
            response_text = memoire[question_cle].replace("cher humain", user_name) 
            await message.channel.send(f'{user_name} : {response_text}') 
            return 

        # 4. PAS DE RÉPONSE STATIQUE -> RECHERCHE STABLE VIA API SERPER
        else:
            await message.channel.send(f"Hum... Je ne connais pas la réponse. Laissez-moi chercher ça pour vous, {user_name}...")
            
            title, link = search_serper(question_cle) # Appel à l'API Serper
            
            if link and title:
                # Réponse trouvée et structurée
                await message.channel.send(
                    f"J'ai trouvé ceci ! 🔍\n\n"
                    f"**{title}**\n"
                    f"<{link}>"
                )
            else:
                # Si l'API n'a rien trouvé
                reponse_inconnue = f"Désolée {user_name}, je n'ai rien trouvé sur internet pour cette requête, et ce n'est pas dans ma mémoire. Vous pouvez me l'apprendre avec `/apprendre`."
                await message.channel.send(reponse_inconnue)
            
            return
            
    await bot.process_commands(message)

# --- LANCEMENT DU BOT (DÉCLENCHÉ PAR server.py) ---

if DISCORD_TOKEN is None:
    print("❌ AVERTISSEMENT: La clé 'TOKEN' (Discord) n'a pas été trouvée lors de l'importation de main.py.")
