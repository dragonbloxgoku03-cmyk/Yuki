import discord
from discord.ext import commands
import os
import time
import datetime as dt 
from discord import app_commands 

# --- 1. CONFIGURATION DU BOT ---

# Intents nécessaires pour la modération et les messages
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True 
intents.messages = True

bot = commands.Bot(command_prefix=".", intents=intents)

start_time = time.time() 

print("Yuki démarre en mode Commandes Stables.")
    
# --- 2. ÉVÉNEMENT DE DÉMARRAGE ET SYNCHRONISATION SLASH ---

@bot.event
async def on_ready():
    # Synchronise toutes les commandes slash
    try:
        synced = await bot.tree.sync()
        print(f'Yuki est en ligne et prêt ! Synchronisé {len(synced)} commande(s) slash.')
        print(f'Connecté en tant que {bot.user}')
    except Exception as e:
        print(f"Erreur lors de la synchronisation des commandes slash : {e}")

# --- 3. LOGIQUE DE MESSAGE ---

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Répond si le bot est mentionné
    if bot.user.mentioned_in(message) or "yuki" in message.content.lower():
        await message.channel.send("Je suis en ligne. Utilisez les commandes slash comme /aide.")
    
    await bot.process_commands(message)

# --- 4. COMMANDES MODÉRATION ET INTERACTION ---

# ➡️ COMMANDE BAN (BANNIR)
@bot.tree.command(name="bannir", description="Bannit un membre du serveur (nécessite la permission Banir).")
@app_commands.describe(membre="Le membre à bannir.", raison="La raison du bannissement.")
@app_commands.checks.has_permissions(ban_members=True)
async def bannir_slash(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison spécifiée"):
    
    if membre.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message(f"Désolé, je ne peux pas bannir ce membre. Leur rôle est trop élevé.", ephemeral=True)
    
    try:
        await membre.ban(reason=raison)
        await interaction.response.send_message(f"🚫 {membre.mention} a été banni(e). Raison : **{raison}**")
    except discord.Forbidden:
        await interaction.response.send_message("Je n'ai pas la permission de bannir ce membre. Veuillez vérifier ma hiérarchie de rôles.", ephemeral=True)


# ➡️ COMMANDE ISOLER (MUTE/TIMEOUT)
@bot.tree.command(name="isoler", description="Isole un membre pour une durée spécifiée (nécessite la permission Timeout).")
@app_commands.describe(membre="Le membre à isoler.", minutes="Durée de l'isolation en minutes.", raison="La raison de l'isolation.")
@app_commands.checks.has_permissions(moderate_members=True)
async def isoler_slash(interaction: discord.Interaction, membre: discord.Member, minutes: int, raison: str = "Aucune raison spécifiée"):
    
    duree = dt.timedelta(minutes=minutes)
    
    try:
        await membre.timeout(duree, reason=raison)
        await interaction.response.send_message(f"🔇 {membre.mention} a été isolé(e) pendant **{minutes} minutes**. Raison : **{raison}**")
    except discord.Forbidden:
        await interaction.response.send_message("Je n'ai pas la permission d'isoler ce membre. Vérifiez ma hiérarchie de rôles.", ephemeral=True)


# ➡️ COMMANDE DIRE (ENVOYER UN MESSAGE À TRAVERS LE BOT)
@bot.tree.command(name="dire", description="Fait dire quelque chose au bot dans le canal actuel.")
@app_commands.describe(message="Le message à envoyer.")
async def dire_slash(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(f"Message envoyé !", ephemeral=True) 
    await interaction.channel.send(message)


# ➡️ COMMANDE REAGIR (METTRE UNE RÉACTION)
@bot.tree.command(name="reagir", description="Ajoute une réaction à un message.")
@app_commands.describe(message_id="L'ID du message auquel réagir.", emoji="L'emoji à utiliser (ex: :thumbsup: ou l'ID d'un emoji personnalisé).")
async def reagir_slash(interaction: discord.Interaction, message_id: str, emoji: str):
    
    try:
        message = await interaction.channel.fetch_message(int(message_id))
    except discord.NotFound:
        return await interaction.response.send_message("Message non trouvé. Veuillez vérifier l'ID.", ephemeral=True)
    except Exception:
        return await interaction.response.send_message("ID de message invalide.", ephemeral=True)
        
    try:
        await message.add_reaction(emoji)
        await interaction.response.send_message(f"Réaction ajoutée au message `{message_id}`.", ephemeral=True)
    except discord.HTTPException:
        await interaction.response.send_message("Emoji invalide ou je n'ai pas la permission d'ajouter cette réaction.", ephemeral=True)


# --- 5. COMMANDES DE BASE ---

@bot.tree.command(name="aide", description="Affiche une liste des commandes de Yuki.")
async def aide_slash(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Liste des Commandes de Yuki ⚙️",
        description="J'utilise les commandes slash (/) pour toutes mes fonctions.",
        color=discord.Color.blue()
    )
    embed.add_field(name="➡️ MODÉRATION", value="`/bannir`, `/isoler`", inline=False)
    embed.add_field(name="➡️ INTERACTION", value="`/dire`, `/reagir`", inline=False)
    embed.add_field(name="➡️ BASE", value="`/aide`, `/bonjour`, `/info`", inline=False)
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="bonjour", description="Yuki vous dit bonjour.")
async def bonjour_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"Bonjour à toi, {interaction.user.mention} ! Je suis Yuki, ton bot.")


@bot.tree.command(name="info", description="Affiche les informations de base de Yuki et son état.")
async def info_slash(interaction: discord.Interaction):
    
    current_time = time.time()
    difference = int(round(current_time - start_time))
    uptime = str(dt.timedelta(seconds=difference))

    embed = discord.Embed(
        title="✨ Informations sur Yuki ✨",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Temps de Fonctionnement (Uptime)", value=uptime, inline=True)
    embed.add_field(name="Latence (Ping)", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Bibliothèque", value=f"discord.py v{discord.__version__}", inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True) 

# --- 6. LANCEMENT DU BOT ---

# Lance le bot en utilisant la clé TOKEN.
try:
    bot.run(os.environ['TOKEN'])
except KeyError:
    print("ERREUR FATALE : La clé TOKEN Discord n'a pas été trouvée dans les secrets. Assurez-vous qu'elle est bien nommée 'TOKEN' (en majuscules).")
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")