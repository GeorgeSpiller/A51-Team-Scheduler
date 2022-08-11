import json
import re
from discord.ext import commands
from discord import Embed, Color
from datetime import timedelta, date, datetime
from main import PREVIOUS_SCHEDULES_TEXTFILE, get_teams, get_days_scrimming_teams, main

# firstly, load data
TEAM_SCHEDULE_INFO_JSONFILE = 'D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ScheduleInfo.json'
with open(TEAM_SCHEDULE_INFO_JSONFILE, 'r') as f:
    data = json.load(f)   

DISCORD_BOT_TOKEN_TEXTFILE = 'D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\diecordbottoken.txt'
with open(DISCORD_BOT_TOKEN_TEXTFILE, 'r') as f:
    token = f.readline() 

LAST_UPDATED_DATE = datetime.strptime(data['Date Compiled'], "%Y-%m-%d %H:%M:%S.%f")
LAST_UPDATED_STRING = f'{LAST_UPDATED_DATE.day}/{LAST_UPDATED_DATE.month} at {LAST_UPDATED_DATE.hour}:{LAST_UPDATED_DATE.minute}'

ARENA51_GUILD_ID = 743968283006337116
ALLOWED_SERVERS = [714774324174782534, 743968283006337116, 999094760750981221]
SCHEDULE_CHANNEL_ID = 816724490674634772 # Testing Server: 1001559765215883344 A51: 816724490674634772
CASTERSIGNUP_CHANNEL_ID = 810799071232393216 # A51: 810799071232393216
BOTCOMMANDS_ALLOWED_CHANNELS = [1001915039386701965, 714774324174782537, 804415006631264306, 825990730752983040, 743968283434156033]
PROTECTED_COMMANDS_ALLOWED_ROLES = ['manager', 'Team Manager']

PREVIOUS_SCHEDULE_STRING = ''
PREVIOUS_SCHEDULE_LOOKBACK = 2

client = commands.Bot(command_prefix='!')

# TODO: catch discord.ext.commands.errors.MissingRequiredArgument exception and provide arg info for arg commands

def replace_roleid_with_rolename(message, guild):
    '''replaces any instances of role ID tags with the role corrisponding role's name.
        Also removes any roles that are between ~~strikethrough~~ tags'''
    # fist, get a list of all the ID's in the message
    # remove any ID's tht are between ~~strikethrough~~ tags
    strikethroughs = re.findall('~~<@&\d{18}>\d*.*~~', message)
    if strikethroughs:
        for s in strikethroughs:
            message = message.replace(s, '')

    # replace all ids with team names
    rids = re.findall('<@&\d{18}>', message)
    rids = [i.replace('<@&', '').replace('>', '') for i in rids]

    # Get each IDs name, and replace
    ret = message
    for rid in rids:
        role = guild.get_role(int(rid))
        if role != None:
            rid_name = role.name.replace(' ', '').upper()
            ret = ret.replace(rid, rid_name)
    return ret


async def replace_userid_with_username(id_string):
    currentID = ''
    idlist = id_string.split()
    print(f'processing userid string: {id_string}')
    for i, id in enumerate(idlist):
        currentID = int(id.replace('<', '').replace('>', '').replace('@', ''))
        idlist[i] = await client.fetch_user(int(currentID))
        idlist[i] = idlist[i].name

    return ' '.join(idlist)


def build_embed(tupledata):
    cotm_prod, full_month_name, prefix, verb = tupledata

    # embed the information
    embed=Embed(
        title=f"{prefix} of the month,  {full_month_name}", 
        description=f"{cotm_prod[0].display_name} (aka {cotm_prod[0].name})", 
        color=Color.blue())

    embed.set_author(
        name=cotm_prod[0].display_name, 
        icon_url=cotm_prod[0].avatar_url)

    embed.set_thumbnail(
        url=cotm_prod[0].avatar_url
    )

    embed.add_field(name=f"{verb}", 
    value=f"{cotm_prod[1]} {verb} last month.", 
    inline=True)

    embed.add_field(name=f"Total {verb}", 
    value=f"Has {verb} ## time total, thats ## mins live!", 
    inline=True)

    return embed



@client.event
async def on_ready():
    print('logged in as {0.user}'.format(client))
    print(f'{client.user} is connected to the following servers:\n')
    for guild in client.guilds:
        for textChannel in guild.text_channels:
            if textChannel.id == SCHEDULE_CHANNEL_ID:
                messageList = []
                async for message in textChannel.history(limit=PREVIOUS_SCHEDULE_LOOKBACK):
                    messageList.append(message.content)
                messageList.reverse()
                PREVIOUS_SCHEDULE_STRING = '-----------------------------------------'.join(messageList)
                PREVIOUS_SCHEDULE_STRING = replace_roleid_with_rolename(PREVIOUS_SCHEDULE_STRING, guild)
                with open(PREVIOUS_SCHEDULES_TEXTFILE, 'w') as f:
                    f.write(PREVIOUS_SCHEDULE_STRING)
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
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
	    await ctx.channel.send(f"The full team list is bellow, last updated on ``{LAST_UPDATED_STRING}``:\n```{', '.join(data['Teams'])}```")

@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help="Lists all the Arena 51 teams that are currently on the stream schedule, and therefore all the teams that could potentially be streamed. If you believe a team should be on here, please message spag!",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!at] Lists all teams that are currently on the stream schedule.",
    aliases=['at', 'ateam', 'ateams', 'activet', 'activeteam', 'acteams']
)
async def activeteams(ctx):
    print(f'{ctx.author.name} sent command !activeteams')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
	    await ctx.channel.send(f"The full list of teams that are currently on the stream schedule is bellow, last updated on ``{LAST_UPDATED_STRING}``:\n```{', '.join(data['Teams On Schedule'])}```")
    
@client.command(
    # ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help="Gives the stream priority for a team, for example: !teamscore platpack . The score is arbitary, that is it's not based on anything such as days, but rather is a guideline as to how likely you will beon the next schedule.",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="[!tp] Gives the stream priority for a team.",
    aliases=['tp', 'tpriority', 'teamp', 'teampri', 'teampriorities']
)
async def teampriority(ctx, arg):
    print(f'{ctx.author.name} sent command !teampriority {arg}')
    if ctx.channel.id in BOTCOMMANDS_ALLOWED_CHANNELS:
        userInputTeamName = arg.upper().strip()
        if userInputTeamName in data['Teams']:
            if userInputTeamName in data['Teams On Schedule']:
                for team in data['TeamScore']:
                    if team[0] == userInputTeamName:
                        teams_in_future_schedule = [t[0] for t in data["Future Schedule"]]
                        is_on_future_schedule = "likely" if team[0] in teams_in_future_schedule else "un-likley"
                        await ctx.channel.send(f"The team ``{userInputTeamName}`` has a stream priority of {team[1]}/{data['Highest Priority']}. It is currently {is_on_future_schedule} to be streamed next week. Last updated on ``{LAST_UPDATED_STRING}``")
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
        #   m, tu, w, th, f, sa, su,
        #   0  1   2  3   4  5   6
        # god this is ugly, but need to update to python 3.10 for match statment :((
        if processedInput == 'mo':
            processedInput = 0
        elif processedInput == 'tu':
            processedInput = 1
        elif processedInput == 'we':
            processedInput = 2
        elif processedInput == 'th':
            processedInput = 3
        elif processedInput == 'fr':
            processedInput = 4
        elif processedInput == 'sa':
            processedInput = 5
        elif processedInput == 'su':
            processedInput = 6
        else:
            processedInput = -1
        
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
	brief="Gives the caster of the month. Example: !cotm prod. Args: prod, pbp, col",
    aliases=['cotm']
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
                    currentMonth = datetime.now().month
                    lastMonth = currentMonth - 1 if (currentMonth - 1) != 0 else 12
                    
                    producers = []
                    caster_pbp = []
                    caster_col = []
                    caster_signup_channel = client.get_channel(CASTERSIGNUP_CHANNEL_ID)
                    async for message in caster_signup_channel.history(limit=45*2):   # 45 is the maximum amount of messages a month the bot that posts in this channel could post
                        if message.created_at.month == lastMonth:
                            if '@' in message.content:
                                producer_search = ' '.join(re.findall('Production\/Observer\(🎥\): (<@\d{18}> ?)*', message.content))
                                caster_pbp_search = ' '.join(re.findall('Play-By-Play\(🎙\): (<@\d{18}> ?)*', message.content))
                                caster_col_search = ' '.join(re.findall('Colour\(🔬\): (<@\d{18}> ?)*', message.content))

                                if producer_search:
                                    producers.append(producer_search.replace('<', '').replace('>', '').replace('@', ''))
                                
                                if caster_pbp_search:
                                    caster_pbp.append(caster_pbp_search.replace('<', '').replace('>', '').replace('@', ''))

                                if caster_col_search:
                                    caster_col.append(caster_col_search.replace('<', '').replace('>', '').replace('@', ''))

                    # count the occurance of each name, based on which role was inout as an arg
                    datetime_object = datetime.strptime(str(lastMonth), "%m")
                    full_month_name = datetime_object.strftime("%B")

                    broadcasterDict = {}
                    winnerData = []
                    embed = None

                    if arg == "prod":
                        for entry in producers:
                            broadcasterDict[entry] = producers.count(entry)
                        winnerData = [await client.fetch_user(int(max(broadcasterDict, key=broadcasterDict.get))), broadcasterDict[max(broadcasterDict, key=broadcasterDict.get)]]
                        embed = build_embed( (winnerData, full_month_name, "Producer", "Producing") )
                        await ctx.send(embed=embed)

                    elif arg == "pbp":
                        for entry in caster_pbp:
                            broadcasterDict[entry] = caster_pbp.count(entry)
                        winnerData = [await client.fetch_user(int(max(broadcasterDict, key=broadcasterDict.get))), broadcasterDict[max(broadcasterDict, key=broadcasterDict.get)]]
                        embed = build_embed( (winnerData, full_month_name, "Play-by-Play Caster", "Casting") )
                        await ctx.send(embed=embed)
                    
                    elif arg == "col":
                        for entry in caster_col:
                            broadcasterDict[entry] = caster_col.count(entry)
                        winnerData = [await client.fetch_user(int(max(broadcasterDict, key=broadcasterDict.get))), broadcasterDict[max(broadcasterDict, key=broadcasterDict.get)]]
                        embed = build_embed( (winnerData, full_month_name, "Color Caster", "Casting") )
                        await ctx.send(embed=embed)
                    
        if not is_allowed:
            await ctx.channel.send(f"This command can only be used by people with the roles {', '.join(PROTECTED_COMMANDS_ALLOWED_ROLES)}")
    

client.run(token)









