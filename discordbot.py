import json
import re
from os import getcwd, listdir, path
import traceback
from typing import final
from discord.ext import commands
from discord import Embed, Color, errors, Intents
from datetime import datetime
from Schedule import get_teams, get_days_scrimming_teams, main
from Constants import *
from DiscordUtils import *
from casterSignupEntry import CSignupEntry


# firstly, load data
def load_data():
    global glob_data
    global glob_tocken
    print('\tReading previous schedule data...')
    TEAM_SCHEDULE_INFO_JSONFILE = f'{getcwd()}\\data\\ScheduleInfo.json'
    with open(TEAM_SCHEDULE_INFO_JSONFILE, 'r') as f:
        glob_data = json.load(f)   
    print('\tReading bot token...')
    DISCORD_BOT_TOKEN_TEXTFILE = f'{getcwd()}\\auth\\diecordbottoken.txt'
    with open(DISCORD_BOT_TOKEN_TEXTFILE, 'r') as f:
        glob_tocken = f.readline() 

print(' ----- Preparing Bot -----')
load_data()
global glob_data
global glob_tocken
LAST_UPDATED_DATE                   = datetime.strptime(glob_data['Date Compiled'], "%Y-%m-%d %H:%M:%S.%f")
LAST_UPDATED_STRING                 = f'{LAST_UPDATED_DATE.day}/{LAST_UPDATED_DATE.month} at {LAST_UPDATED_DATE.hour}:{LAST_UPDATED_DATE.minute}'


intents = Intents.default()
intents.message_content = True
intents.members = True

client = commands.Bot(intents=intents, command_prefix='a/')


@client.event
async def on_ready():
    # load_data()
    joinedServers = []
    for guild in client.guilds:
        for textChannel in guild.text_channels:
            if textChannel.id == SCHEDULE_CHANNEL_ID:
                print('\tReading previous schedules...')
                # await dutil_write_previous_schedule(guild, textChannel)
                break
        joinedServers.append(f'{guild.name} ({guild.id})')
        if guild.id not in ALLOWED_SERVERS:
            print(f'\tleaving server: {guild.name} ({guild.id})')
            await client.get_guild(int(guild.id)).leave()
    # await dutil_updateall(client)
    print('\tlogged in as {0.user}, connected to the following servers:'.format(client))
    print('\t' + ', '.join(joinedServers))
    print(' ----- Finished Bot Preperation ----- ')


@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help="Gives a list of all the teams that are currently affiliated with Arena 51!",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/ft] Gives a list of all A51 teams.",
    aliases=['ft', 'fulteams', 'fullteam', 'fulteam', 'fteams', 'fteam']
)
async def fullteams(ctx):
    print(f'{ctx.author.name} sent command a/fullteams')
    global glob_data
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
	    await ctx.channel.send(f"The full team list is bellow, last updated on ``{LAST_UPDATED_STRING}``:\n```{', '.join(glob_data['Teams'])}```")


@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help="Lists all the Arena 51 teams that are currently on the stream schedule, and therefore all the teams that could potentially be streamed. If you believe a team should be on here, please message spag!",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/at] Lists all teams that are currently on the stream schedule.",
    aliases=['at', 'ateam', 'ateams', 'activet', 'activeteam', 'acteams']
)
async def activeteams(ctx):
    print(f'{ctx.author.name} sent command a/activeteams')
    global glob_data
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
	    await ctx.channel.send(f"The full list of teams that are currently on the stream schedule is bellow, last updated on ``{LAST_UPDATED_STRING}``:\n```{', '.join(glob_data['Teams On Schedule'])}```")


@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help="Gives the stream priority for a team, for example: a/teamscore platpack . The score is arbitary, that is it's not based on anything such as days, but rather is a guideline as to how likely you will beon the next schedule.",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/tp] Gives the stream priority for a team.",
    aliases=['tp', 'tpriority', 'teamp', 'teampri', 'teampriorities']
)
async def teampriority(ctx, arg):
    print(f'{ctx.author.name} sent command a/teampriority {arg}')
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
            await ctx.channel.send(f"My bad chief, i cannot find ``{userInputTeamName}`` as a team, try a/teams for a list of teams we have. Last updated on ``{LAST_UPDATED_STRING}``")


@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help="Lists all the teams that scrim on a particular day. For example: a/whoscrimson monday",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/wso] Lists all the teams that scrim on a particular day.",
    aliases=['wso', 'whoso', 'whoscrimo', 'whoscrimso', 'wscrimo']
)
async def whoscrimson(ctx, arg):
    print(f'{ctx.author.name} sent command a/whoscrimson {arg}')
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


@commands.has_any_role(*PROTECTED_COMMANDS_ALLOWED_ROLES)
@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help=f"Updates the bots information on A51 teams. Can only be used by {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/upd] Updates the bots information on A51 teams.",
    aliases=['upd', 'refresh', 'reload']
)
async def update(ctx):
    print(f'{ctx.author.name} sent command a/update')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        await ctx.channel.send(f"Updating information. This may take a moment....")
        await dutil_updateall(client)
        load_data()
        print('Updating Finished.')
        await ctx.channel.send(f"Bot records have been updated!")


@commands.has_any_role(*PROTECTED_COMMANDS_ALLOWED_ROLES)
@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help=f"Sends the user the stream schedule for next week. Can only be used by {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/gen] Sends the user the stream schedule for next week.",
    aliases=['gen']
)
async def generate(ctx):
    print(f'{ctx.author.name} sent command a/generate')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        await ctx.channel.send(f"Aye Aye Captain!")
        newSchedule = main()
        await ctx.author.send(f"Hello there! I believe you requested the schedule for next week:")
        await ctx.author.send(f"```{newSchedule}```")


@commands.has_any_role(*PROTECTED_COMMANDS_ALLOWED_ROLES)
@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help=f"Gives the caster of the month. Example: a/cotm prod. Can only be used by {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/cotm] Gives the caster of the month. Example: a/cotm prod. Args: prod, pbp, col",
    aliases=['cotm', 'prodofthemonth']
)
async def casterofthemonth(ctx, arg):
    print(f'{ctx.author.name} sent command a/casterofthemonth')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        if arg != "prod" and arg != "pbp" and arg != "col":
            await ctx.channel.send(f"Unrecognised argument ``{arg}``! Please use iether: ``prod``, ``pbp`` or ``col``.")
        else:
            # get month specific info
            currentMonth = datetime.now().month
            lastMonth = currentMonth - 1 if (currentMonth - 1) != 0 else 12
            casterOTM = dutil_get_mostFrequent_broadcasters(lastMonth, arg)
            casterOTM_ID = list(casterOTM.keys())[0]

            # get total info
            casterOTM_total = dutl_get_total_broadcasts_string(casterOTM_ID)

            embed = await dutil_build_embed(await client.fetch_user(int(casterOTM_ID)), casterOTM_total, client, lastMonth, arg, casterOTM[casterOTM_ID])
            await ctx.send(embed=embed)



@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help=f"Gets information about a broadcaster. Example: a/ci spaggettiohs",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/ci] Gets information about a broadcaster.",
    aliases=['ci'] 
)
async def casterinfo(ctx, arg):
    print(f'{ctx.author.name} sent command a/casterinfo {arg}')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        # format arg
        userNameString = arg.lower().strip()

        # read the json store to first match a caster name to ID
        requestedUser = None
        with open(BROADCASTER_ID_TO_NAME_FILE, 'r') as f:
            casterIDsAndNames = json.load(f)
        for name in casterIDsAndNames.values():
            if name.lower().strip() == userNameString:
                position = list(casterIDsAndNames.values()).index(name)
                requestedUser = list(casterIDsAndNames.keys())[position]

        if requestedUser != None:
            requestedUser = await client.fetch_user(int(requestedUser))
            castedCountString = dutl_get_total_broadcasts_string(requestedUser.id)
            embed = await dutil_build_embed(requestedUser, castedCountString, client)
            await ctx.send(embed=embed)
        else:
            # user not found
            await ctx.channel.send(f"Ope. I cannot find the user ``{arg}`` in <#{SCHEDULE_CHANNEL_ID}>. ")


@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help=f"Manually add caster info. Example: a/ci spaggettiohs prod 2 (adds 2 days of producing for spag)",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/maddci casterName role number] Add data to caster.",
    aliases=['maddci'] 
)
async def manualAddCasterinfo(ctx, *arg):
    print(f'{ctx.author.name} sent command a/manualAddCasterinfo {arg}')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        try:
            cName = arg[0]
            role = arg[1]
            days = int(arg[2])
            dutil_manualAdd_casterData(cName, role, days)
            await ctx.channel.send(f"Data added.")
        except Exception as e:
            print(e)
            await ctx.channel.send(f"Bad arguments {arg}. Syntax: a/maddci casterName role number")


@commands.has_any_role(*PROTECTED_COMMANDS_ALLOWED_ROLES)
@client.command(
    # ADDS THIS VALUE TO THE a/HELP PRINT MESSAGE.
	help=f"Gives all discord uses in an attached `.txt` file a specific role. The discrod names in the file must be `name#1234` and separated by commas: `,` , newlines: `\n` , or spaces. Role must be plain text, not an ID.",
	# ADDS THIS VALUE TO THE a/HELP MESSAGE.
	brief="[a/bar] assigns users in attached file a role. eg: a/bar Admin",
    aliases=['bulkar', 'bar', 'bulkasign'] 
)
async def bulkAssignRoles(ctx, arg):
    print(f'{ctx.author.name} sent command a/bulkRoles_ProcessFile {arg}')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        try:
            attachment_url = ctx.message.attachments[0].url
            discordNames = dutil_loadFile(attachment_url)
            discordRole = dutils_roleExists(ctx.message.guild, arg)
            results = await dutils_bulkAssignRoles(ctx.message.guild, discordNames, discordRole)
            await ctx.channel.send(f"""Role assignments processed.
            Members who have been sucessfully given the {arg} role: \n```{results['SucessfulAssignment']}```
            
            Members who where not found in {ctx.author.guild}: \n```{results['MembersNotFoundInGuild']}```
            
            Members who were not added due to internal errors: \n```{results['AssignmentError']}```""")

        except (UndefinedSeporator, RoleNotFound)  as e:
            await ctx.channel.send(f"There was an error performing your request: \n{e}")
        except IndexError  as e:
            await ctx.channel.send(f"Please upload a file as an attachment to the `a/bar` command.")
        except Exception  as e:
            print(f'Errors: {traceback.format_exc()}')



client.run(glob_tocken)









