import json
import re
from os import getcwd
from discord.ext import commands
from discord import Embed, Color, errors
from datetime import datetime
from Schedule import get_teams, get_days_scrimming_teams, main
from Constants import *


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


async def count_total_casts(userID, client):
    counter = 0
    async for message in client.get_channel(CASTERSIGNUP_CHANNEL_ID).history(limit=None):
        if str(userID) in message.content:
            counter += 1
    return counter


def build_embed(tupledata):
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


def build_embed_nomonth(tupledata):
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








