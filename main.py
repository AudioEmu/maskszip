import discord, os, pickle, aiohttp, asyncio
from dotenv import load_dotenv
from discord import app_commands, Webhook

from masks import player

#v----- Function Definitions-----v
def pSave(objectToSave, fileName): #Use pickle to dump object into fileName
	with open(fileName, 'wb') as f:
		pickle.dump(objectToSave, f)
def pLoad(fileName): #Use pickle to load fileName into object
	with open(fileName, 'rb') as f:
		loadedObject = pickle.load(f)
		return loadedObject

client = discord.Client(intents=discord.Intents.all())

load_dotenv()

playersSaveFile="players.pickle"
botToken=os.getenv("botToken")
client.chatWebhook=os.getenv("chatWebhook")
client.deadWebhook=os.getenv("deadWebhook")
client.serverID=int(os.getenv("serverID"))
client.gmRoleID=int(os.getenv("gmRoleID"))
client.defaultIconURL="https://cdn11.bigcommerce.com/s-40v409mhy5/images/stencil/1280x1280/products/2972/27471/A-LONGNOSEMIRROR-47348-9__96277.1696314846.jpg"
client.thisServer=None
client.gmRole=None

tree=app_commands.CommandTree(client)

client.players=[]
print(f'Looking for saved players file at {playersSaveFile}')
if os.path.isfile(playersSaveFile):
    print(f'Found saved players file at {playersSaveFile}')
    client.players=pLoad(playersSaveFile)
    print(f'Loaded!')
else:
    print(f'No saved players file found at {playersSaveFile}! Add user masks to make one!')

##########################
#     SLASH COMMANDS     #
##########################

@tree.command(name='chat', description='Send a message as your mask!', guild=discord.Object(id=client.serverID))
async def chat(interaction, message :str='', attachment :discord.Attachment=None):
    foundSender = False
    senderName = "User Not Found"
    senderIconURL = client.defaultIconURL
    senderIsDead = False
    chatHook=''

    await interaction.response.defer(ephemeral=True)

    for p in client.players:
        if p.memID==interaction.user.id:
            senderName=p.maskName
            senderIconURL=p.maskImageLink
            foundSender = True
            if p.isDead:
                senderIsDead = True

    if not foundSender:
        await interaction.followup.send(f'You are not in the list of active players!')
    else:
        if senderIsDead:
            chatHook = client.deadWebhook
        else:
            chatHook = client.chatWebhook

        async with aiohttp.ClientSession() as session:
            webhook=Webhook.from_url(chatHook, session=session)
            if not message=='':
                await webhook.send(message, username=senderName, avatar_url=senderIconURL)
            if not attachment==None:
                if (('image' in attachment.content_type) or ('video' in attachement.content_type)):
                    await webhook.send(attachment.url, username=senderName, avatar_url=senderIconURL)

        await interaction.followup.send(f'Sent!', ephemeral=True)


@tree.command(
    name='setmask',
    description='Set a player\'s mask info',
    guild=discord.Object(id=client.serverID)
)
async def setmask(interaction, userid :str, maskname :str, maskimage :discord.Attachment=None):

    userid=int(userid)

    mask=player(userid, maskname, maskimage.url, False)
    foundPlayer = False

    await interaction.response.defer(ephemeral=True)

    if not client.gmRole in interaction.user.roles:
        await interaction.followup.send(f'You are not allowed to do this!', ephemeral=True)
    else:
        for p in client.players:
            if p.memID == userid:
                await interaction.followup.send(f'This user already has a mask. Please use /deletemask before setting again', ephemeral=True)
                foundPlayer=True
        if not foundPlayer:
            client.players.append(mask)
            await interaction.followup.send(f'Added user mask!', ephemeral=True)
            pSave(client.players, playersSaveFile)

@tree.command(
    name='deletemask',
    description='Delete a player\'s mask info',
    guild=discord.Object(id=client.serverID)
)
async def deletemask(interaction, userid :str):
    userid=int(userid)
    foundUser = False

    await interaction.response.defer(ephemeral=True)

    if not client.gmRole in interaction.user.roles:
        await interaction.followup.send("You are not allowed to do that!")
    else:
        for p in client.players:
            if p.memID == userid:
                client.players.remove(p)
                pSave(client.players, playersSaveFile)
                await interaction.followup.send("Mask removed!")
                foundUser=True
        if not foundUser:
            await interaction.followup.send("That player was not in the mask list!")


@tree.command(
    name='listmasks',
    description='List the names of the masks',
    guild=discord.Object(id=client.serverID)
)
async def listmasks(interaction):
    await interaction.response.defer(ephemeral=True)
    masks='.'
    for p in client.players:
        masks+=(p.maskName+' ')
    await interaction.followup.send(masks, ephemeral=True)

@tree.command(
    name='toggledead',
    description='Toggle whether or not a player is dead',
    guild=discord.Object(id=client.serverID)
)
async def toggledead(interaction, userid :str):
    await interaction.response.defer(ephemeral=True)

    userid=int(userid)

    if not client.gmRole in interaction.user.roles:
        await interaction.followup.send(f'You are not allowed to do that!')
    else:
        for p in client.players:
            if p.memID == userid:
                if p.isDead:
                    p.isDead = False
                    await interaction.followup.send(f'User is back from the dead!', ephemeral=True)
                else:
                    p.isDead = True
                    await interaction.followup.send(f'User is kil :(', ephemeral=True)
        pSave(client.players, playersSaveFile)


@client.event
async def on_ready():
    print(client.serverID)

    for guild in client.guilds:
        print(f'{guild.name} at {guild.id}')
        if guild.id==client.serverID:
            client.thisServer=guild
            print('matched!')

        for p in client.players:
            print(f'{p.maskName} at {p.memID}')

    client.gmRole=discord.utils.get(client.thisServer.roles, id=client.gmRoleID)
    await tree.sync(guild=discord.Object(id=client.serverID))
    print(f'Bot is live!')

client.run(botToken)