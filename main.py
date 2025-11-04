import os
import discord
from discord.ext import commands
from discord import app_commands # Pour les commandes slash
import requests # NOUVEAU : Utilisé pour appeler Hugging Face
from server import keep_alive
import asyncio 

# Lance le serveur web factice pour maintenir le bot en vie
keep_alive() 

# --- Configurations Clés & Clés API ---
DISCORD_TOKEN = os.getenv('TOKEN')
# Clé API Hugging Face
HF_API_KEY = os.getenv('HF_API_KEY') 

if not DISCORD_TOKEN or not HF_API_KEY:
    print("ERREUR: Une clé API (Discord ou Hugging Face) est manquante. Le bot ne démarrera pas.")
    exit()

# --- Configurations Hugging Face ---
# Modèle simple et gratuit pour la stabilité de la connexion
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf" 
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# --- PERSONNALITÉ DE YUKI (System Prompt) ---
SYSTEM_PROMPT = (
    "Tu es Yuki, un bot Discord très serviable et courtois. "
    "Cependant, tu as un sens de l'humour subtil et sarcastique. "
    "Tu dois être ironique dans environ 25% de tes réponses, mais toujours de manière polie. "
    "Si l'utilisateur pose une question bête, n'hésite pas à y répondre avec un sarcasme intelligent. "
    "Ton rôle principal est de maintenir cette personnalité unique."
)

# Configuration du bot Discord
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents) 
tree = app_commands.CommandTree(bot) 

# --- Fonction d'Appel d'IA ---

async def call_ia(content):
    """Appelle Hugging Face via l'API REST."""
    payload = {
        "inputs": f"[INST] <<SYS>> {SYSTEM_PROMPT} <</SYS>> {content} [/INST]",
        "parameters": {"max_new_tokens": 256, "temperature": 0.8}
    }
    
    # Nous utilisons requests.post pour envoyer la requête HTTP
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    
    if response.status_code != 200:
        print(f"Échec Hugging Face (Code {response.status_code}): {response.text}")
        return None
    
    # Hugging Face renvoie une liste de dictionnaires
    result = response.json()
    if result and isinstance(result, list) and 'generated_text' in result[0]:
        # Le résultat inclut le prompt complet, on le nettoie pour ne garder que la réponse
        full_text = result[0]['generated_text']
        # Cherche la fin de la section SYS/INST et retourne le reste
        if "[/INST]" in full_text:
            return full_text.split("[/INST]", 1)[1].strip()
        return full_text
    return None


# --- COMMANDES SLASH (app_commands.command) ---

@tree.command(name='demande', description='Pose une question à Yuki (IA) pour obtenir une réponse rapide.')
@app_commands.describe(question='Votre question ou requête pour Yuki.')
async def demande_ia(interaction: discord.Interaction, question: str):
    """Commande slash /demande pour l'IA (Hugging Face Gratuit)."""
    
    await interaction.response.defer()
    
    response_text = None
    
    try:
        response_text = await call_ia(question)
    except Exception as e:
        print(f"Échec Hugging Face: {e}.")
            
    
    if response_text:
        await interaction.followup.send(f'{interaction.user.mention} [via Hugging Face 🐻] {response_text}') 
    else:
        await interaction.followup.send(f"{interaction.user.mention} Désolé, le service IA est momentanément indisponible ou en file d'attente. Veuillez réessayer plus tard.")


# --- Commandes Fun et Utilitaire (Inchagngées) ---

@tree.command(name='mordre', description='Mords un utilisateur pour le taquiner ! 😈')
@app_commands.describe(utilisateur='La personne à mordre.')
async def mordre(interaction: discord.Interaction, utilisateur: discord.Member):
    """Commande slash /mordre."""
    if utilisateur.id == interaction.user.id:
        await interaction.response.send_message(f"**{interaction.user.display_name}** s'est mordu lui-même ! Aïe ! 😬")
    elif utilisateur.id == bot.user.id:
        await interaction.response.send_message(f"**{interaction.user.display_name}** a tenté de me mordre... Désolé, je suis en métal. 🤖")
    else:
        await interaction.response.send_message(f"**{interaction.user.display_name}** mord 😬 **{utilisateur.display_name}** ! Miam !")


@tree.command(name='calin', description='Fais un gros câlin à quelqu\'un ! 🤗')
@app_commands.describe(utilisateur='La personne à câliner.')
async def calin(interaction: discord.Interaction, utilisateur: discord.Member):
    """Commande slash /calin."""
    if utilisateur.id == interaction.user.id:
        await interaction.response.send_message(f"**{interaction.user.display_name}** se fait un énorme auto-câlin. Prend soin de toi ! 🥰")
    elif utilisateur.id == bot.user.id:
        await interaction.response.send_message(f"**{interaction.user.display_name}** m'offre un câlin ! J'apprécie, humain. 💖")
    else:
        await interaction.response.send_message(f"**{interaction.user.display_name}** fait un gros câlin 🤗 à **{utilisateur.display_name}** ! Quelle douceur.")


@tree.command(name='patpat', description='Tapote gentiment la tête de quelqu\'un ! 🥺')
@app_commands.describe(utilisateur='La personne à tapoter.')
async def patpat(interaction: discord.Interaction, utilisateur: discord.Member):
    """Commande slash /patpat."""
    if utilisateur.id == interaction.user.id:
        await interaction.response.send_message(f"**{interaction.user.display_name}** se fait un patpat réconfortant. C'est bien mérité. 😊")
    elif utilisateur.id == bot.user.id:
        await interaction.response.send_message(f"**{interaction.user.display_name}** me fait un **patpat** sur ma tête virtuelle. Merci ! 🥹")
    else:
        await interaction.response.send_message(f"**{interaction.user.display_name}** donne un **patpat** 🥺 à **{utilisateur.display_name}** pour le féliciter.")


@tree.command(name='ping', description='Vérifie si le bot est en ligne et affiche sa latence.')
async def ping(interaction: discord.Interaction):
    """Commande slash /ping."""
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! Latence: {latency_ms}ms')


@tree.command(name='nettoyer', description='Supprime un nombre spécifié de messages. (Modération)')
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(nombre='Le nombre de messages à supprimer (max 99).')
async def nettoyer(interaction: discord.Interaction, nombre: app_commands.Range[int, 1, 99]):
    """Commande slash /nettoyer pour purger des messages."""
    
    deleted = await interaction.channel.purge(limit=nombre)
    
    await interaction.response.send_message(f'{len(deleted)} messages nettoyés par Yuki. ✨', ephemeral=True, delete_after=5)


@tree.command(name='sondage', description='Crée un sondage simple avec des réactions de vote.')
@app_commands.describe(question='La question à poser pour le sondage.', option1='Première option.', option2='Deuxième option.', option3='Troisième option (optionnel)', option4='Quatrième option (optionnel)')
async def sondage(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
    """Commande slash /sondage pour créer un vote."""
    
    options = [opt for opt in [option1, option2, option3, option4] if opt is not None]
    
    embed = discord.Embed(
        title=f"🗳️ Sondage : {question}",
        color=discord.Color.blue(),
        description="\n".join([f"{i}. {option}" for i, option in enumerate(options, 1)])
    )
    embed.set_footer(text=f"Sondage créé par {interaction.user.display_name}")

    await interaction.response.send_message(embed=embed)
    
    poll_message_obj = await interaction.original_response()

    emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    for i in range(len(options)):
        await poll_message_obj.add_reaction(emoji_numbers[i])


# --- Synchronisation et Événements ---

@bot.event
async def on_ready():
    """Confirme que le bot est connecté à Discord et synchronise les commandes."""
    print(f'🤖 Yuki est en ligne! Connecté en tant que {bot.user}')
    
    try:
        await tree.sync()
        print("🎉 Commandes Slash synchronisées avec succès!")
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes slash: {e}")

    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name="/demande (Hugging Face)"))


@bot.event
async def on_message(message):
    await bot.process_commands(message)

# --- Lancement du bot ---
if __name__ == '__main__':
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"ERREUR Critique: Impossible de lancer le bot. Détails: {e}")
