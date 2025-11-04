import os
import discord
from discord.ext import commands
from server import keep_alive # Importe le serveur factice

# Lance le serveur web factice pour satisfaire Render.com
keep_alive() 

# --- Configurations Clés ---
DISCORD_TOKEN = os.getenv('TOKEN')

if not DISCORD_TOKEN:
    print("ERREUR: Le TOKEN Discord n'est pas configuré. Le bot ne démarrera pas.")
    exit()

intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 Yuki est en ligne! Connecté en tant que {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="pour les mots-clés"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    # --- LOGIQUE DES RÉPLIQUES SIMPLES ---

    if 'bonjour yuki' in content or 'salut yuki' in content:
        await message.channel.send(f'Salut à toi, {message.author.mention} !')

    elif 'dis un truc gentille' in content:
        await message.channel.send('Tu es une personne incroyable !')

    else:
        if bot.user.mentioned_in(message):
            await message.channel.send(f'Je ne comprends pas. Essaie "Bonjour Yuki".')

    await bot.process_commands(message)

# --- Lancement du bot ---
if __name__ == '__main__':
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"ERREUR Critique: Impossible de lancer le bot. Détails: {e}")
