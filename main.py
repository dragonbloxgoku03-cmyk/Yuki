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
# CORRECTION CRITIQUE : Cherche la clé Discord sous le nom "TOKEN"
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
@app_commands.describe(question='Votre question ou
