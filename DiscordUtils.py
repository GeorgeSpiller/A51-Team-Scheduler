import json
import re
from os import getcwd, listdir, path
from discord.ext import commands
from discord import Embed, Color, errors
from datetime import datetime
from Schedule import get_teams, get_days_scrimming_teams, main
from Constants import *
from casterSignupEntry import CSignupEntry

#TODO: reduce async querys for dutil_updateall to increase efficency

def dutil_replace_roleid_with_rolename(message, guild):
    '''replaces any instances of role ID tags with the role corrisponding role's name.
        Also removes any roles that are between ~~strikethrough~~ tags'''
    # fist, get a list of all the ID's in the message
    # remove any ID's tht are between ~~strikethrough~~ tags
    strikethroughs = re.findall('~~<@&\d{18,19}>\d*.*~~', message)
    if strikethroughs:
        for s in strikethroughs:
            message = message.replace(s, '')

    # replace all ids with team names
    rids = re.findall('<@&\d{18,19}>', message)
    rids = [i.replace('<@&', '').replace('>', '') for i in rids]

    # Get each IDs name, and replace
    ret = message
    for rid in rids:
        role = guild.get_role(int(rid))
        if role != None:
            rid_name = role.name.replace(' ', '').upper()
            ret = ret.replace(rid, rid_name)
    return ret


async def dutil_count_total_casts(userID, client):
    counter = 0
    async for message in client.get_channel(CASTERSIGNUP_CHANNEL_ID).history(limit=None):
        if str(userID) in message.content:
            counter += 1
    return counter


async def dutil_build_embed(user, scoreString, client, month=None, arg=None, casterMonthStats=None):
    guild = client.get_guild(ARENA51_GUILD_ID)
    member = await guild.fetch_member(user.id)
    if member.joined_at:
        joinedAtDate = member.joined_at.strftime("%b %d, %Y, %T")
    else:
        joinedAtDate = "some time ago"

    # construct embed
    if month != None and arg != None and casterMonthStats != None:
        datetime_object = datetime.strptime(str(month), "%m")
        full_month_name = datetime_object.strftime("%B")
        arg.replace('prod', 'Producer')
        arg.replace('col', 'Colour Caster')
        arg.replace('pbp', 'Play-By-Play Caster')


        print(f"castermstats: {casterMonthStats}")

        embed=Embed(
            title=f"{user.name}#{user.discriminator} is {full_month_name}'s {arg} of the Month!", 
            description=f"{user.display_name}, joined at {joinedAtDate}. {member.top_role}.", 
            color=Color.blue())
        embed.add_field(
            name=f"Last month:", 
            value=f"Produced {casterMonthStats['prods']} times.\nColor Casted {casterMonthStats['cols']} times.\nPlay-By-Play Casted {casterMonthStats['pbps']} times.\n", 
            inline=True)
    else:
        embed=Embed(
            title=f"{user.name}#{user.discriminator}", 
            description=f"{user.display_name}, joined at {joinedAtDate}. {member.top_role}.", 
            color=Color.blue())

    embed.set_author(
        name=user.display_name, 
        icon_url=user.avatar_url)

    embed.set_thumbnail(
        url=user.avatar_url
    )

    embed.add_field(name=f"Total stats:", 
    value=f"{scoreString}",
    inline=False)

    return embed


async def dutil_write_previous_schedule(guild, textChannel):
    messageList = []
    async for message in textChannel.history(limit=PREVIOUS_SCHEDULE_LOOKBACK):
        messageList.append(message.content)
    messageList.reverse()
    PREVIOUS_SCHEDULE_STRING = '-----------------------------------------'.join(messageList)
    PREVIOUS_SCHEDULE_STRING = dutil_replace_roleid_with_rolename(PREVIOUS_SCHEDULE_STRING, guild)
    with open(PREVIOUS_SCHEDULES_TEXTFILE, 'wb') as f:
        f.write(PREVIOUS_SCHEDULE_STRING.encode('utf8'))


def dutl_dayString_to_dayumber(inp):
    #   m, tu, w, th, f, sa, su,
    #   0  1   2  3   4  5   6
    # god this is ugly, but need to update to python 3.10 for match statment :((
    if inp == 'mo':
        inp = 0
    elif inp == 'tu':
        inp = 1
    elif inp == 'we':
        inp = 2
    elif inp == 'th':
        inp = 3
    elif inp == 'fr':
        inp = 4
    elif inp == 'sa':
        inp = 5
    elif inp == 'su':
        inp = 6
    else:
        inp = -1
    return inp


def get_total_broadcasts_string(userID):
    count_prod, count_col, count_pbp, count_total = 0, 0, 0, 0
    for filename in listdir(BROADCASTER_SIGNUPSTORE_DIR):
        if filename == '.gitignore':
            continue
        json_Month = path.join(BROADCASTER_SIGNUPSTORE_DIR, filename)

        with open(json_Month, 'r') as f:
            counts = dutil_count_broadcasts(json.load(f), userID)
        count_prod += counts[str(userID)]['prods']
        count_col += counts[str(userID)]['cols']
        count_pbp += counts[str(userID)]['pbps']
        count_total += counts[str(userID)]['total']

    castedCountString = f"Has Casted/Produced {count_total} times total, thats ~{(count_total * STREAM_RUNTIME_HOURS):,} hours, or ~{(count_total * STREAM_RUNTIME_MINS):,} mins live!"
    if count_prod != 0:
        castedCountString += f'\nHas produced {count_prod} times.'
    if count_col != 0:
        castedCountString += f'\nHas colour casted {count_col} times.'
    if count_pbp != 0:
        castedCountString += f'\nHas play-by-play casted {count_pbp} times.'
    return castedCountString


def dutil_get_mostFrequent_broadcasters(month, casterType):
    for filename in listdir(BROADCASTER_SIGNUPSTORE_DIR):
        if filename == '.gitignore':
            continue
        fileNameMonth = int(filename.split()[0].replace('[', '').replace(']', '').replace(str(datetime.now().year), '').replace('-', ''))
        if fileNameMonth == int(month):
            json_MonthFile = path.join(BROADCASTER_SIGNUPSTORE_DIR, filename)
            with open(json_MonthFile, 'r') as f:
                count_month = dutil_count_broadcasts(json.load(f))

            # get caster with the most total casts
            currentMax = list(count_month.keys())[0]
            for userID in count_month.keys():
                if count_month[userID][f'{casterType}s'] > count_month[currentMax][f'{casterType}s']:
                    currentMax = userID

            return {currentMax : count_month[currentMax]}


def dutil_get_all_casterIDs(jsonDict):
    # search the given json dict for all IDs, grab each ID and get the caster name
    # return the user obj if found, else return False
    raw_casterIDs = []
    casterIDs = []
    for k in jsonDict.keys(): # for each day
        raw_casterIDs.append(jsonDict[k]['prods'])
        raw_casterIDs.append(jsonDict[k]['cols'])
        raw_casterIDs.append(jsonDict[k]['pbps'])

    for entry in raw_casterIDs:
        if entry != [] and entry != None:
            if len(entry) > 1:
                for e in entry:
                    casterIDs.append(e[0])
            else:
                casterIDs.append(entry[0])
    
    return [*set(casterIDs)]


def dutil_count_broadcasts(jsonDict, userID=None):
    count_prod = 0
    count_col = 0
    count_pbp = 0 
    count_total = 0
    oneCastPerDay = False
    counts = {}
    if userID != None:
        for k in jsonDict.keys(): # for each day
            oneCastPerDay = False
            if str(userID) in jsonDict[k]['prods']:
                count_prod += 1
                oneCastPerDay = True
            if str(userID) in jsonDict[k]['cols']:
                count_col += 1
                oneCastPerDay = True
            if str(userID) in jsonDict[k]['pbps']:
                count_pbp += 1
                oneCastPerDay = True
            if oneCastPerDay:
                count_total += 1
        counts[str(userID)] = { 'prods' : count_prod, 'cols' : count_col, 'pbps' : count_pbp, 'total' : count_total }
    else:
        for k in jsonDict.keys(): # for each day
            casterIDs = dutil_get_all_casterIDs(jsonDict)
            for id in casterIDs:
                counts[str(id)] = dutil_count_broadcasts(jsonDict, id)[str(id)]
        
    return counts


async def dutil_updateall(client):
    main()

    print('Loading Caster Data:\n\tReading Caster Sign-up...')
    # load all new signup messages into jsons
    caster_signup_channel = client.get_channel(CASTERSIGNUP_CHANNEL_ID)
    casterIDs = []
    casterIDsNames = {}
    # bot starts posting at/or/after roughly  01/2022
    async for message in caster_signup_channel.history(limit=None, after=datetime(2022, 1, 1)):
        # add as entry only if the 'role' @'s are not in the message (ie, the message is a day broacasters can react to)
        if message.author.bot:
            discordRoles = ['<@&913494942511431681>', '@DiamondPack', '<@&763408133736366142>', '<@&808742990868512849>', '<@913494942511431681>', '<@763408133736366142>', '<@808742990868512849>']
            if (not any(role in message.content for role in discordRoles)):
                entry = CSignupEntry(message.content, message.created_at)
                entry.save()
                idsInEntry = [entry.prods, entry.cols, entry.pbps]
                idsInEntry = [item for sublist in idsInEntry for item in sublist]
                for id in idsInEntry:
                    if id not in casterIDs:
                        casterIDs.append(id)
    print("\tQuerying ID's to names...")

    # get all caster IDs and corresponding names
    # if casterID not already in file
    with open(BROADCASTER_ID_TO_NAME_FILE, 'r') as f:
        savedCasterIDs = json.load(f)
    
    for uniqueUserID in casterIDs:
        if uniqueUserID not in savedCasterIDs.keys():
            try:
                queryUser = await client.fetch_user(int(uniqueUserID))
                casterIDsNames[uniqueUserID] = queryUser.name
            except errors.NotFound:
                continue
        else:
            casterIDsNames[uniqueUserID] = savedCasterIDs[uniqueUserID]
    print('\tSaving data...')
    # save all caster IDs and names in json
    with open(BROADCASTER_ID_TO_NAME_FILE, 'w') as f:
        json.dump(casterIDsNames, f)
    print('Finished Loading Caster Data')



def dutil_manualAdd_casterData(casterName, role, numberOfAdditionalHous):
    pass




