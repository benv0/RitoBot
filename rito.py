
import discord
import json

from discord.ext import commands
import requests


TOKEN =  "YOUR DISCORD TOKEN"
KEY = "YOUR RIOT GAMES DEVELOPMENT KEY"
PLAYER_NAME_URL = 'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/'
CHAMPION_URL = 'http://ddragon.leagueoflegends.com/cdn/10.18.1/data/en_US/champion.json'

bot = commands.Bot(command_prefix='$')

#signals when the bot is ready for use
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

#takes in player name and queueType and look for the player winrate in that queue type
@bot.command()
async def wr(ctx, player_name, queueType):
    await ctx.send('Player name: {}'.format(player_name))

    summonerID = getID(player_name)

    if summonerID != 'err':
        result = getPlayerStats(summonerID, queueType)
        await ctx.send('Winrate for {} in {} is {:.2f}%'.format(result['summonerName'],result['queueType'],
            (round(result['wins']/(result['losses']+result['wins']),3)*100)))

#helper fucntion to retrieve the player's information
def getPlayerStats(sID,queueID):
    queue = ''
    if queueID == 'solo':
        queue = 'RANKED_SOLO_5x5'
    elif queueID == 'flex':
        queue = 'RANKED_FLEX_SR'

    response = requests.get('https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/' + sID + '?api_key='+ KEY)

    if(response.status_code == 200):
        for item in response.json():
            if item['queueType'] == queue:
                return item

    return 'err'

#returning player's encrypted Riot Games ID
def getID(player_name):
    response = requests.get(PLAYER_NAME_URL + player_name + '?api_key='+ KEY)
    if (response.status_code == 200):
        return response.json()['id']
    else: 
        return 'err'
#look up a player's win rate on a certain champion in all game modes
@bot.command()
async def wrChamp(ctx,player_name,champ_name):
    aID = getAccID(player_name)
    champID = getChampKey(champ_name)
    if aID != 'err' and champID != 'err':
        response = requests.get('https://na1.api.riotgames.com/lol/match/v4/matchlists/by-account/' + aID + '?champion=' + str(champID) + '&api_key=' + KEY)
        if (response.status_code == 200):
            await ctx.send(await display(ctx,response,aID,player_name,champ_name))
        else: 
            return 'err'

# returns a string detailing a player's winrate on champion after x games (maximum of 50 games)
# aID is the player's encrypted account ID
async def display(ctx,response,aID,player_name,champ_name):
    matches = response.json()['matches']
    limit = 0
    total = 50
    winCount = 0
    if len(matches) > total:
        limit = total
    else:
        limit = len(matches)
    for i in range(limit):
        if await checkPlayerWin(matches[i], aID):
            print(i)
            winCount = winCount + 1
    return '{} has a winrate of {:.2f}% with {} in the most recent {} games.'.format(player_name,round((winCount/limit)*100,2),champ_name,limit)

# see if the player has won a match, taking a matchID as an argument
async def checkPlayerWin(match,aID):
    participantID = 0
    r = requests.get('https://na1.api.riotgames.com/lol/match/v4/matches/' + str(match['gameId'])+ '?api_key=' + KEY)
    result = r.json()
    if(r.status_code == 200):
        participantID = getPlayerID(result,aID)
    if participantID != -1:
        for participant in result['participants']:
            print(participantID)
            if participant['participantId'] == participantID:
                return participant['stats']['win']
    return False

# getting the player's unique participant ID every game
def getPlayerID(r,aID):
    for player in r['participantIdentities']:
        if aID == player['player']['accountId']:
            return player['participantId']
    return -1
# returning the player's unique account ID 
def getAccID(player_name):
    response = requests.get(PLAYER_NAME_URL + player_name + '?api_key='+ KEY)
    if (response.status_code == 200):
        return response.json()['accountId']
    else: 
        return 'err'

# return the champion's unique id based on the champion's name
def getChampKey (champ_name):
    response = requests.get(CHAMPION_URL)
    if (response.status_code == 200):
        return response.json()['data'][champ_name]['key']
    else:
        return 'err'

bot.run(TOKEN)