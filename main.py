import os
import discord
from discord.ext import commands
from google import genai 
from groq import Groq 
from server import keep_alive
import asyncio 

# Lance le serveur web factice
keep_alive() 

# --- Configurations Clés & Clés API ---
DISCORD_TOKEN = os.getenv('TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY') 

if not DISCORD_TOKEN or not GEMINI_API_KEY or not GROQ_API_KEY:
    print("ERREUR: Une clé API (Discord, Gemini ou Groq) est manquante. Le bot ne démarrera pas.")
    exit()

# --- PERSONNALITÉ DE YUKI (System Prompt) ---
SYSTEM_PROMPT = (
    "Tu es Yuki, un bot Discord très serviable et courtois. "
    "Cependant, tu as un sens de l'humour subtil et sarcastique. "
    "Tu dois être ironique dans environ 25% de tes réponses, mais toujours de manière polie. "
    "Si l'utilisateur pose une question bête, n'hésite pas à y répondre avec un sarcasme intelligent. "
    "Ton rôle principal est de maintenir cette personnalité unique."
)

# Initialisation des clients IA
try:
    client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    MODEL_GEMINI = 'gemini-2.5-flash'
    client_groq = Groq(api_key=GROQ_API_KEY)
    MODEL_GROQ = "mixtral-8x7b-32768"
except Exception as e:
    print(f"ERREUR lors de l'initialisation des Clients IA: {e}")
    exit()

# Configuration du bot Discord : Utilisation du préfixe '!' pour TOUTES les commandes.
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix='!', intents=intents) 

# --- Fonctions d'Appel d'IA (avec Personnalité) ---

async def call_gemini(content):
    """Tente d'appeler Gemini avec le System Prompt."""
    response = client_gemini.models.generate_content(
        model=MODEL_GEMINI,
        contents=content,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT
        )
    )
    return response.text

async def call_groq(content):
    """Tente d'appeler Groq avec le System Prompt."""
    completion = client_groq.chat.completions.create(
        model=MODEL_GROQ,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]
    )
    return completion.choices[0].message.content

# --- COMMANDES EXPLICITES (@bot.command) ---

@bot.command(name='demande', aliases=['d', 'ask'], help='Pose une question à Yuki (IA). Ex: !demande comment va la météo?')
async def demande_ia(ctx, *, content):
    """Gère la logique de réponse du bot IA (Gemini/Groq)"""
    
    if ctx.message.mention_everyone:
        return

    await ctx.message.delete()
    
    async with ctx.channel.typing():
        response_text = None
        ia_used = "Gemini"
        
        # 1. ESSAI AVEC GEMINI (IA Primaire)
        try:
            response_text = await call_gemini(content)
        except Exception as e:
            print(f"Échec Gemini (Quota probable): {e}. Tentative Groq...")
            ia_used = "Groq"
            
            # 2. ESSAI AVEC GROQ (IA de Secours)
            try:
                response_text = await call_groq(content)
            except Exception as e_groq:
                print(f"Échec Groq également: {e_groq}.")
                
        
        if response_text:
            await ctx.send(f'{ctx.author.mention} [via {ia_used}] {response_text}')
        else:
            await ctx.send(f"{ctx.author.mention} Désolé, les deux IA sont indisponibles. Veuillez patienter 15 secondes.")
            await asyncio.sleep(15) 

@bot.command(name='ping', help='Répond avec la latence du bot.')
async def ping(ctx):
    """Commande !ping pour vérifier la latence."""
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f'Pong! Latence: {latency_ms}ms')

@bot.command(name='nettoyer', aliases=['clear'], help='Supprime un nombre spécifié de messages. (Nécessite Gérer les messages)')
@commands.has_permissions(manage_messages=True)
async def nettoyer(ctx, amount: int = 5):
    """Commande de modération !nettoyer pour purger des messages."""
    if amount <= 0:
        return await ctx.send("Le nombre de messages à supprimer doit être supérieur à zéro.")
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    
    await ctx.send(f'{len(deleted) - 1} messages nettoyés par Yuki. ✨', delete_after=5)

@nettoyer.error
async def nettoyer_error(ctx, error):
    """Gère les erreurs de la commande !nettoyer."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Désolé, vous n'avez pas la permission de 'Gérer les messages' pour exécuter cette commande.", delete_after=10)
    elif isinstance(error, commands.BadArgument):
         await ctx.send("Veuillez entrer un nombre valide de messages à supprimer (ex: !nettoyer 10).", delete_after=10)
    else:
        await ctx.send("Une erreur est survenue lors du nettoyage. Veuillez contacter l'administrateur.", delete_after=10)


@bot.command(name='sondage', help='Crée un sondage simple avec des réactions de vote.')
async def sondage(ctx, question, *options):
    """Commande !sondage pour créer un vote."""
    if len(options) < 2:
        return await ctx.send("Veuillez fournir au moins deux options pour le sondage. (Ex: !sondage 'Couleur préférée?' rouge bleu vert)")
    if len(options) > 9:
        return await ctx.send("Vous ne pouvez pas avoir plus de 9 options.")

    await ctx.message.delete()

    embed = discord.Embed(
        title=f"🗳️ Sondage : {question}",
        color=discord.Color.blue(),
        description="\n".join([f"{i}. {option}" for i, option in enumerate(options, 1)])
    )
    embed.set_footer(text=f"Sondage créé par {ctx.author.display_name}")

    poll_message = await ctx.send(embed=embed)
    
    emoji_numbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    for i in range(len(options)):
        await poll_message.add_reaction(emoji_numbers[i])

# --- Événements Discord ---

@bot.event
async def on_ready():
    """Confirme que le bot est connecté à Discord."""
    print(f'🤖 Yuki est en ligne! Connecté en tant que {bot.user}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name="!aide ou !demande"))

@bot.event
async def on_message(message):
    """Gère le comportement du bot en dehors des commandes."""
    # Cette fonction est vide car toutes les interactions sont gérées par les commandes explicites.
    
    # NE PAS OUBLIER : Laisser le traitement des commandes
    await bot.process_commands(message)

# --- Lancement du bot ---
if __name__ == '__main__':
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"ERREUR Critique: Impossible de lancer le bot. Détails: {e}")
