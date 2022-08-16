import json
import re
from os import getcwd
from discord.ext import commands
from discord import Embed, Color, errors
from datetime import datetime
from Schedule import get_teams, get_days_scrimming_teams, main
from Constants import *


def dutil_replace_roleid_with_rolename(message, guild):
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


async def dutil_count_total_casts(userID, client):
    counter = 0
    async for message in client.get_channel(CASTERSIGNUP_CHANNEL_ID).history(limit=None):
        if str(userID) in message.content:
            counter += 1
    return counter


def dutil_build_embed(tupledata):
    cotm_prod, full_month_name, prefix, verb = tupledata

    # embed the information
    embed=Embed(
        title=f"{full_month_name}'s {prefix} of the month!", 
        description=f"{cotm_prod[0].display_name} (aka {cotm_prod[0].name}#{cotm_prod[0].discriminator})", 
        color=Color.blue())

    embed.set_author(
        name=cotm_prod[0].display_name, 
        icon_url=cotm_prod[0].avatar_url)

    embed.set_thumbnail(
        url=cotm_prod[0].avatar_url
    )

    embed.add_field(name=f"{verb}", 
    value=f"{verb} {cotm_prod[1]} times last month.", 
    inline=True)

    embed.add_field(name=f"Total {verb}", 
    value=f"Has {verb} {cotm_prod[2]} times total, thats ~{(int(cotm_prod[2]) * STREAM_RUNTIME_HOURS):,} hours, or ~{(int(cotm_prod[2]) * STREAM_RUNTIME_MINS):,} mins live!", 
    inline=True)

    return embed


def dutil_build_embed_nomonth(tupledata):
    user, score = tupledata

    # embed the information
    embed=Embed(
        title=f"{user.name} Broadcaster info:", 
        description=f"{user.display_name} (aka {user.name}#{user.discriminator})", 
        color=Color.blue())

    embed.set_author(
        name=user.display_name, 
        icon_url=user.avatar_url)

    embed.set_thumbnail(
        url=user.avatar_url
    )

    embed.add_field(name=f"Total stats", 
    value=f"Has Casted/Produced {score} times total, thats ~{(int(score) * STREAM_RUNTIME_HOURS):,} hours, or ~{(int(score) * STREAM_RUNTIME_MINS):,} mins live!", 
    inline=False)

    return embed


async def dutil_write_previous_schedule(guild, textChannel):
    messageList = []
    async for message in textChannel.history(limit=PREVIOUS_SCHEDULE_LOOKBACK):
        messageList.append(message.content)
    messageList.reverse()
    PREVIOUS_SCHEDULE_STRING = '-----------------------------------------'.join(messageList)
    PREVIOUS_SCHEDULE_STRING = dutil_replace_roleid_with_rolename(PREVIOUS_SCHEDULE_STRING, guild)
    with open(PREVIOUS_SCHEDULES_TEXTFILE, 'w') as f:
        f.write(PREVIOUS_SCHEDULE_STRING)


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


async def dutil_cotm(client, arg, ctx):
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
    winnerUser = None

    if arg == "prod":
        for entry in producers:
            broadcasterDict[entry] = producers.count(entry)
        winnerUser = await client.fetch_user(int(max(broadcasterDict, key=broadcasterDict.get)))
        winnerData = [winnerUser, broadcasterDict[str(winnerUser.id)], await dutil_count_total_casts(winnerUser.id, client)]
        embed = dutil_build_embed( (winnerData, full_month_name, "Producer", "Produced") )
        await ctx.send(embed=embed)

    elif arg == "pbp": 
        for entry in caster_pbp:
            broadcasterDict[entry] = caster_pbp.count(entry)
        winnerUser = await client.fetch_user(int(max(broadcasterDict, key=broadcasterDict.get)))
        winnerData = [winnerUser, broadcasterDict[str(winnerUser.id)], await dutil_count_total_casts(winnerUser.id, client)]
        embed = dutil_build_embed( (winnerData, full_month_name, "Play-by-Play Caster", "Casted") )
        await ctx.send(embed=embed)
    
    elif arg == "col":
        for entry in caster_col:
            broadcasterDict[entry] = caster_col.count(entry)
        winnerUser = await client.fetch_user(int(max(broadcasterDict, key=broadcasterDict.get)))
        winnerData = [winnerUser, broadcasterDict[str(winnerUser.id)], await dutil_count_total_casts(winnerUser.id, client)]
        embed = dutil_build_embed( (winnerData, full_month_name, "Color Caster", "Casted") )
        await ctx.send(embed=embed)
                    