import discord
from discord import app_commands
from discord.ext import commands
import os
import json 

# UTILISATION DE os.environ.get() pour une lecture plus fiable sur Render
DISCORD_TOKEN = os.environ.get("TOKEN")

# Configuration du bot
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

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


# --- COMMANDES SLASH ---

@bot.tree.command(name='apprendre', description='Apprend une nouvelle phrase ou réponse au bot (Nécessite Gérer les messages).')
@app_commands.describe(question='La phrase ou question à retenir.', reponse='La réponse que Yuki doit donner.')
@app_commands.checks.has_permissions(manage_messages=True) 
async def apprendre_slash(interaction: discord.Interaction, question: str, reponse: str):
    await interaction.response.defer(ephemeral=True)

    memoire = charger_memoire()
    question_cle = question.lower().strip()
    memoire[question_cle] = reponse

    sauvegarder_memoire(memoire)
    
    await interaction.followup.send(
        f"✅ J'ai retenu la leçon suivante :\n"
        f"**Question/Clé** : `{question}`\n"
        f"**Réponse** : `{reponse}`\n",
        ephemeral=True
    )


@bot.tree.command(name='monnom', description='Permet à Yuki de retenir votre nom.')
@app_commands.describe(nom='Votre prénom ou le nom par lequel vous voulez que Yuki vous appelle.')
async def monnom_slash(interaction: discord.Interaction, nom: str):
    await interaction.response.defer(ephemeral=True)

    profils = charger_profils()
    user_id = str(interaction.user.id)
    profils[user_id] = nom.strip()

    sauvegarder_profils(profils)
    
    await interaction.followup.send(
        f"✅ Entendu, **{nom.strip()}**. Je m'en souviendrai. Je ne vous appellerai plus 'cher humain'.",
        ephemeral=True
    )


# --- GESTION DES MESSAGES ---

@bot.event
async def on_message(message):
    
    if message.author.bot:
        return
    
    if bot.user.mentioned_in(message) or "yuki" in message.content.lower():
        
        question = message.content 
        
        # 1. VÉRIFICATION DU PROFIL UTILISATEUR
        profils = charger_profils()
        user_name = profils.get(str(message.author.id), "cher humain") 

        # 2. VÉRIFICATION DE LA MÉMOIRE INTERNE (Q/R)
        memoire = charger_memoire()
        
        question_cle = question.lower().strip().replace(f'@{bot.user.display_name.lower()}', '').strip()

        if question_cle in memoire:
            # L'IA interne a la réponse !
            response_text = memoire[question_cle].replace("cher humain", user_name) 
            
            await message.channel.send(f'{message.author.mention} {response_text}') 
            return 

        # Si aucune réponse n'est trouvée
        else:
            if user_name != "cher humain":
                 reponse_inconnue = f"Je suis désolée {user_name}, je n'ai pas la réponse à cela dans ma mémoire. Vous pouvez me l'apprendre avec `/apprendre`."
            else:
                 reponse_inconnue = "Je suis désolée, je n'ai pas la réponse à cela dans ma mémoire. Vous pouvez me l'apprendre avec la commande `/apprendre`."
            
            await message.channel.send(f'{message.author.mention} {reponse_inconnue}')
            return
            
    await bot.process_commands(message)

# --- LANCEMENT DU BOT ---
# Le bot.run est désactivé ici. Il est appelé par server.py.
if DISCORD_TOKEN is None:
    print("❌ AVERTISSEMENT: La clé 'TOKEN' (Discord) n'a pas été trouvée lors de l'importation de main.py.")
