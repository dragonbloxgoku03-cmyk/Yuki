import os
import discord
from discord.ext import commands
from google import genai
from server import keep_alive # Importe le serveur factice

# Lance le serveur web factice pour satisfaire Render.com
keep_alive() 

# --- Configurations Clés ---
DISCORD_TOKEN = os.getenv('TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not DISCORD_TOKEN or not GEMINI_API_KEY:
    print("ERREUR: Le TOKEN Discord ou la GEMINI_API_KEY n'est pas configuré. Le bot ne démarrera pas.")
    exit()

# Configuration du client Discord pour lire les messages et les mentions
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

# Initialisation du client Gemini
try:
    client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    model = 'gemini-2.5-flash' # Modèle rapide pour le chat
except Exception as e:
    print(f"ERREUR lors de l'initialisation de Gemini: {e}")
    client_gemini = None


@bot.event
async def on_ready():
    """Confirme que le bot est connecté à Discord."""
    print(f'🤖 Yuki est en ligne! Connecté en tant que {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name="@Yuki pour parler"))


@bot.event
async def on_message(message):
    """Gère la logique de réponse du bot aux messages."""

    # Ne pas répondre à soi-même
    if message.author == bot.user:
        return

    # Vérifie si le bot est mentionné
    if bot.user.mentioned_in(message):

        # Le contenu du message sans la mention
        content = message.content.replace(f'<@!{bot.user.id}>', '').strip()

        if not content:
            await message.channel.send("Je suis en ligne. Posez-moi une question!")
            return

        # Indiquer que le bot est en train de taper (répondre)
        async with message.channel.typing():
            try:
                # Appeler l'API Gemini
                response = client_gemini.models.generate_content(
                    model=model,
                    contents=content
                )

                # Envoyer la réponse de Gemini
                await message.channel.send(f'{message.author.mention} {response.text}')

            except Exception as e:
                print(f"Erreur Gemini: {e}")
                await message.channel.send(f"{message.author.mention} Désolé, j'ai rencontré une erreur lors de l'appel à l'IA. Vérifiez ma clé API.")

    # Permet aux commandes slash ou aux commandes avec préfixe de fonctionner
    await bot.process_commands(message)


# --- Lancement du bot ---
if __name__ == '__main__':
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"ERREUR Critique: Impossible de lancer le bot. Le TOKEN est-il valide? Détails: {e}")
