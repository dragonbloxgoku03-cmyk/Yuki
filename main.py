import os
import discord
from discord.ext import commands
from discord import app_commands # Pour les commandes slash
from google import genai # Utilisation du SDK Google Gemini
from server import keep_alive
import asyncio

# Lance le serveur web factice pour maintenir le bot en vie
keep_alive()

# --- Configurations Clés & Clés API ---
# CORRECTION CRITIQUE : Assure la compatibilité avec la variable "TOKEN" sur Render
DISCORD_TOKEN = os.getenv('TOKEN') 
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("ERREUR: Une clé API (Discord ou Gemini) est manquante. Le bot ne démarrera pas.")
    exit()

# --- PERSONNALITÉ DE YUKI (System Prompt) ---
SYSTEM_PROMPT = (
    "Tu es Yuki, un bot Discord très serviable et courtois. "
    "Cependant, tu as un sens de l'humour subtil et sarcastique. "
    "Tu dois être ironique dans environ 25% de tes réponses, mais toujours de manière polie. "
    "Si l'utilisateur pose une question bête, n'hésite pas à y répondre avec un sarcasme intelligent. "
    "Ton rôle principal est de maintenir cette personnalité unique."
)

# Initialisation du client Gemini
try:
    client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    # Modèle rapide et stable
    MODEL_GEMINI = "gemini-2.5-flash" 
except Exception as e:
    print(f"ERREUR lors de l'initialisation du Client Gemini: {e}")
    exit()

# Configuration du bot Discord
# Assurez-vous que les Intents sont activés sur le portail développeur Discord !
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
tree = app_commands.CommandTree(bot)

# --- Fonction d'Appel d'IA ---

async def call_ia(content):
    """Appelle Gemini avec le System Prompt."""
    response = await client_gemini.models.generate_content_async(
        model=MODEL_GEMINI,
        contents=content,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )
    return response.text

# --- COMMANDES SLASH (app_commands.command) ---

@tree.command(name='demande', description='Pose une question à Yuki (IA) pour obtenir une réponse.')
@app_commands.describe(question='Votre question ou requête pour Yuki.')
async def demande_ia(interaction: discord.Interaction, question: str):
    """Commande slash /demande pour l'IA (Gemini seulement)."""

    await interaction.response.defer()

    response_text = None

    try:
        response_text = await call_ia(question)
    except Exception as e:
        print(f"Échec Gemini: {e}.")

    if response_text:
        await interaction.followup.send(f'{interaction.user.mention} [via Gemini 💎] {response_text}')
    else:
        await interaction.followup.send(f"{interaction.user.mention} Désolé, le service IA est momentanément indisponible. Veuillez réessayer plus tard.")

# --- Commandes Fun, Utilitaire et Modération (Inchagngées) ---

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
        await interaction.response.send_message(f"**{interaction.user.display_name}** me fait un **patpat** sur ma tête virtuelle.
