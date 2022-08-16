import json
import re
from os import getcwd
from discord.ext import commands
from discord import Embed, Color, errors
from datetime import datetime
from Schedule import get_teams, get_days_scrimming_teams, main
from Constants import *
from DiscordUtils import *
from casterSignupEntry import CSignupEntry

global glob_data
global glob_tocken

# firstly, load data
def load_data():
    global glob_data
    global glob_tocken
    TEAM_SCHEDULE_INFO_JSONFILE = f'{getcwd()}\\data\\ScheduleInfo.json'
    with open(TEAM_SCHEDULE_INFO_JSONFILE, 'r') as f:
        glob_data = json.load(f)   

    DISCORD_BOT_TOKEN_TEXTFILE = f'{getcwd()}\\auth\\diecordbottoken.txt'
    with open(DISCORD_BOT_TOKEN_TEXTFILE, 'r') as f:
        glob_tocken = f.readline() 


load_data()

LAST_UPDATED_DATE                   = datetime.strptime(glob_data['Date Compiled'], "%Y-%m-%d %H:%M:%S.%f")
LAST_UPDATED_STRING                 = f'{LAST_UPDATED_DATE.day}/{LAST_UPDATED_DATE.month} at {LAST_UPDATED_DATE.hour}:{LAST_UPDATED_DATE.minute}'


client = commands.Bot(command_prefix='!')

# TODO: catch discord.ext.commands.errors.MissingRequiredArgument exception and provide arg info for arg commands
# TODO: Change cotm to fetch only message history in a cirtain time frame
# TODO: !casterinfo counts duo prod/cast reacts for the same day as two different days for the stats.



@client.event
async def on_ready():
    print('logged in as {0.user}'.format(client))
    print(f'{client.user} is connected to the following servers:\n')
    load_data()
    for guild in client.guilds:
        for textChannel in guild.text_channels:
            if textChannel.id == SCHEDULE_CHANNEL_ID:
                await dutil_write_previous_schedule(guild, textChannel)
                break

        print(f'{guild.name} ({guild.id})')
        if guild.id not in ALLOWED_SERVERS:
            print(f'leaving server: {guild.name} ({guild.id})')
            await client.get_guild(int(guild.id)).leave()


@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help="Gives a list of all the teams that are currently affiliated with Arena 51!",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!ft] Gives a list of all A51 teams.",
    aliases=['ft', 'fulteams', 'fullteam', 'fulteam', 'fteams', 'fteam']
)
async def fullteams(ctx):
    print(f'{ctx.author.name} sent command !fullteams')
    global glob_data
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
	    await ctx.channel.send(f"The full team list is bellow, last updated on ``{LAST_UPDATED_STRING}``:\n```{', '.join(glob_data['Teams'])}```")


@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help="Lists all the Arena 51 teams that are currently on the stream schedule, and therefore all the teams that could potentially be streamed. If you believe a team should be on here, please message spag!",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!at] Lists all teams that are currently on the stream schedule.",
    aliases=['at', 'ateam', 'ateams', 'activet', 'activeteam', 'acteams']
)
async def activeteams(ctx):
    print(f'{ctx.author.name} sent command !activeteams')
    global glob_data
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
	    await ctx.channel.send(f"The full list of teams that are currently on the stream schedule is bellow, last updated on ``{LAST_UPDATED_STRING}``:\n```{', '.join(glob_data['Teams On Schedule'])}```")


@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help="Gives the stream priority for a team, for example: !teamscore platpack . The score is arbitary, that is it's not based on anything such as days, but rather is a guideline as to how likely you will beon the next schedule.",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!tp] Gives the stream priority for a team.",
    aliases=['tp', 'tpriority', 'teamp', 'teampri', 'teampriorities']
)
async def teampriority(ctx, arg):
    print(f'{ctx.author.name} sent command !teampriority {arg}')
    global glob_data
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        userInputTeamName = arg.upper().strip()
        if userInputTeamName in glob_data['Teams']:
            if userInputTeamName in glob_data['Teams On Schedule']:
                for team in glob_data['TeamScore']:
                    if team[0] == userInputTeamName:
                        teams_in_future_schedule = [t[0] for t in glob_data["Future Schedule"]]
                        is_on_future_schedule = "likely" if team[0] in teams_in_future_schedule else "un-likley"
                        await ctx.channel.send(f"The team ``{userInputTeamName}`` has a stream priority of {team[1]}/{ glob_data['Highest Priority']}. It is currently {is_on_future_schedule} to be streamed next week. Last updated on ``{LAST_UPDATED_STRING}``")
                        break
            else:
                await ctx.channel.send(f"The team ``{userInputTeamName}`` is not currently on the stream schedule. Last updated on ``{LAST_UPDATED_STRING}``")
        else:
            await ctx.channel.send(f"My bad chief, i cannot find ``{userInputTeamName}`` as a team, try !teams for a list of teams we have. Last updated on ``{LAST_UPDATED_STRING}``")


@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help="Lists all the teams that scrim on a particular day. For example: !whoscrimson monday",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!wso] Lists all the teams that scrim on a particular day.",
    aliases=['wso', 'whoso', 'whoscrimo', 'whoscrimso', 'wscrimo']
)
async def whoscrimson(ctx, arg):
    print(f'{ctx.author.name} sent command !whoscrimson {arg}')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        processedInput = arg[:2].lower()
        processedInput = dutl_dayString_to_dayumber(processedInput)
        
        if processedInput == -1:
            await ctx.channel.send(f'I dont recognise ``{arg}`` as a day of the week.')
        else:
            teams = get_teams()
            teaminfo = get_days_scrimming_teams(teams, processedInput)
            output = [ti[0] for ti in teaminfo]
            await ctx.channel.send(f"The A51 teams that scrim on {arg} are: ``{', '.join(output)}``")


@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=f"Updates the bots information on A51 teams. Can only be used by {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!upd] Updates the bots information on A51 teams.",
    aliases=['upd', 'refresh', 'reload']
)
async def update(ctx):
    print(f'{ctx.author.name} sent command !update')
    is_allowed = False
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        for role in PROTECTED_COMMANDS_ALLOWED_ROLES:
            if role in [y.name.lower() for y in ctx.author.roles]:
                is_allowed = True
                await ctx.channel.send(f"Updating information. This may take a moment....")
                main()
                load_data()
                await ctx.channel.send(f"Bot records have been updated!")
        if not is_allowed:
            await ctx.channel.send(f"This command can only be used by people with the roles {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}")
    

@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=f"Sends the user the stream schedule for next week. Can only be used by {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!gen] Sends the user the stream schedule for next week.",
    aliases=['gen']
)
async def generate(ctx):
    print(f'{ctx.author.name} sent command !generate')
    is_allowed = False
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        for role in PROTECTED_COMMANDS_ALLOWED_ROLES:
            if role in [y.name.lower() for y in ctx.author.roles]:
                is_allowed = True
                await ctx.channel.send(f"Aye Aye Captain!")
                newSchedule = main()
                await ctx.author.send(f"Hello there! I believe you requested the schedule for next week:")
                await ctx.author.send(f"```{newSchedule}```")
        if not is_allowed:
            await ctx.channel.send(f"This command can only be used by people with the roles {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}")
    

@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=f"Gives the caster of the month. Example: !cotm prod. Can only be used by {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!cotm] Gives the caster of the month. Example: !cotm prod. Args: prod, pbp, col",
    aliases=['cotm', 'prodofthemonth']
)
async def casterofthemonth(ctx, arg):
    print(f'{ctx.author.name} sent command !casterofthemonth')
    is_allowed = False
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        for role in PROTECTED_COMMANDS_ALLOWED_ROLES:
            if role in [y.name.lower() for y in ctx.author.roles]:
                is_allowed = True
                if arg != "prod" and arg != "pbp" and arg != "col":
                    await ctx.channel.send(f"Unrecognised argument ``{arg}``! Please use iether: ``prod``, ``pbp`` or ``col``.")
                else:
                    dutil_cotm(client, arg, ctx)
        if not is_allowed:
            await ctx.channel.send(f"This command can only be used by people with the roles {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}")
    

@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=f"Gets information about a broadcaster. Example: !ci spaggettiohs",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!ci] Gets information about a broadcaster.",
    aliases=['ci'] 
)
async def casterinfo(ctx, arg):
    print(f'{ctx.author.name} sent command !casterinfo {arg}')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        caster_signup_channel = client.get_channel(CASTERSIGNUP_CHANNEL_ID)
        casterDict = {}
        user_found_ID = None
        async for message in caster_signup_channel.history(limit=None):
            if user_found_ID != None:
                break
            if '@' in message.content:
                user_search = ' '.join(re.findall('<@\d{18}>', message.content))
                user_search = user_search.replace('<', '').replace('>', '').replace('@', '')

                # add to or update dict
                for uid in user_search.split():
                    if user_found_ID == None:
                        if uid not in casterDict:
                            try:
                                casterDict[uid] = await client.fetch_user(int(uid))
                            except(errors.NotFound):
                                casterDict[uid] = f'Not Found User ({uid})'
                    # else:
                    #     if uid == user_found_ID:
                    #         casterDict[uid] = [casterDict[uid][0], casterDict[uid][1] + 1]

            # if the user we are looking for has been found
            if user_found_ID == None:
                for key in casterDict:
                    if casterDict[key].name.lower() == arg.lower():
                        # found! now only count for this user
                        foundVal = casterDict[key]
                        casterDict.clear()
                        casterDict[key] = foundVal
                        user_found_ID = key
                        break
        
        if user_found_ID == None:
            await ctx.channel.send(f"I could not find a caster with the name {arg}.")
        else:
            winnerUser = casterDict[user_found_ID]
            embed = dutil_build_embed_nomonth((winnerUser, await dutil_count_total_casts(winnerUser.id, client)))
            await ctx.send(embed=embed)



@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=f"Can only be used by {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="",
    aliases=['lc']
)
async def loadcasters(ctx):
    print(f'{ctx.author.name} sent command !loadcasters')
    is_allowed = False
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        for role in PROTECTED_COMMANDS_ALLOWED_ROLES:
            if role in [y.name.lower() for y in ctx.author.roles]:
                is_allowed = True

        if is_allowed:
            # load all new signup messages into jsons
            caster_signup_channel = client.get_channel(CASTERSIGNUP_CHANNEL_ID)

            async for message in caster_signup_channel.history(limit=6):
                # add as entry only if the 'role' @'s are not in the message (ie, the message is a day broacasters can react to)
                if "<@&913494942511431681> <@&763408133736366142> <@&808742990868512849>" not in message.content:
                    entry = CSignupEntry(message.content, message.created_at)
                    print(entry)

        else: #  if not is_allowed
            await ctx.channel.send(f"This command can only be used by people with the roles {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}")
    



client.run(glob_tocken)









