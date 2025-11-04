import os
import discord
from discord.ext import commands
from discord import app_commands # Pour les commandes slash
from groq import Groq # Seulement Groq !
from server import keep_alive
import asyncio 

# Lance le serveur web factice pour maintenir le bot en vie
keep_alive() 

# --- Configurations Clés & Clés API ---
DISCORD_TOKEN = os.getenv('TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY') 

if not DISCORD_TOKEN or not GROQ_API_KEY:
    print("ERREUR: Une clé API (Discord ou Groq) est manquante. Le bot ne démarrera pas.")
    exit()

# --- PERSONNALITÉ DE YUKI (System Prompt) ---
SYSTEM_PROMPT = (
    "Tu es Yuki, un bot Discord très serviable et courtois. "
    "Cependant, tu as un sens de l'humour subtil et sarcastique. "
    "Tu dois être ironique dans environ 25% de tes réponses, mais toujours de manière polie. "
    "Si l'utilisateur pose une question bête, n'hésite pas à y répondre avec un sarcasme intelligent. "
    "Ton rôle principal est de maintenir cette personnalité unique."
)

# Initialisation du client Groq
try:
    client_groq = Groq(api_key=GROQ_API_KEY)
    # Modèle plus léger pour une meilleure stabilité de la connexion Render/Discord
    MODEL_GROQ = "llama2-70b-4096" 
except Exception as e:
    print(f"ERREUR lors de l'initialisation du Client Groq: {e}")
    exit()

# Configuration du bot Discord
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents) 
tree = app_commands.CommandTree(bot) 

# --- Fonction d'Appel d'IA ---

async def call_groq(content):
    """Appelle Groq avec le System Prompt."""
    completion = client_groq.chat.completions.create(
        model=MODEL_GROQ,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    )
    return completion.choices[0].message.content

# --- COMMANDES SLASH (app_commands.command) ---

@tree.command(name='demande', description='Pose une question à Yuki (IA) pour obtenir une réponse rapide.')
@app_commands.describe(question='Votre question ou requête pour Yuki.')
async def demande_ia(interaction: discord.Interaction, question: str):
    """Commande slash /demande pour l'IA (Groq seulement)."""
    
    await interaction.response.defer()
    
    response_text = None
    
    try:
        response_text = await call_groq(question)
    except Exception as e:
        print(f"Échec Groq: {e}.")
            
    
    if response_text:
        # Ligne corrigée de l'erreur de syntaxe
        await interaction.followup.send(f'{interaction.user.mention} [via Groq 🚀] {response_text}') 
    else:
        # Ligne corrigée de l'erreur de syntaxe
        await interaction.followup.send(f"{interaction.user.mention} Désolé, le service IA est momentanément indisponible. Veuillez réessayer plus tard.")


# --- Commandes Fun ---

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
