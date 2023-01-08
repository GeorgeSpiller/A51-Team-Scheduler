from twitchAPI.twitch import Twitch, AuthScope
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import VideoType
from twitchAPI.helper import first
import asyncio

# ----- ClipsToYoutube -----
DEFAULT_TOKEN_FILE_LOCATION         = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\tokens.txt"
DEFAULT_LASTCLIPID_FILE_LOCATION    = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\lastClipID.txt"
DEFAULT_LASTSTREAMID_FILE_LOCATION  = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\lastStreamID.txt"



async def twitch_oAuthlogin(tokenfile = DEFAULT_TOKEN_FILE_LOCATION):
    # initialize the twitch instance, this will by default also create a app authentication for you
    with open(tokenfile, 'r') as f:
        content = f.readlines()
        APPID = content[0].strip()
        APPSECRET = content[1].strip()
    
    twitch = await Twitch(APPID, APPSECRET)
    target_scope = [AuthScope.CLIPS_EDIT]
    auth = UserAuthenticator(twitch, target_scope, force_verify=False)
    # this will open your default browser and prompt you with the twitch verification website
    token, refresh_token = await auth.authenticate()
    # token, refresh_token = auth.authenticate()
    # add User authentication
    await twitch.set_user_authentication(token, target_scope, refresh_token)
    return twitch

class twitchUtils:

    def __init__(self, twitchClient = None):
        if (twitchClient == None):
            loop = asyncio.get_event_loop()
            coroutine = twitch_oAuthlogin()
            twitchClient = loop.run_until_complete(coroutine)

        self.twitch = twitchClient

    async def get_clips_until(self, title_or_clipID):
        user = await first(self.twitch.get_users(logins='Arena_51_Gaming'))
        # dict of [clip ID] : (title, url)
        clipDict = {}
        async for clip in self.twitch.get_clips(user.id):
            # print( f"clip({clip.title} : {clip.duration}, id: {clip.id}, url: {clip.url})" )
            if (clip.title == title_or_clipID or clip.id == title_or_clipID):
                break
            clipDict[clip.id] = clip
        return clipDict# {k: v for k, v in clipDict.items() if v is not None}


    async def get_streams_until(self, title_or_streamID):
        user = await first(self.twitch.get_users(logins='Arena_51_Gaming'))
        # dict of [clip ID] : (title, url)
        streamDict = {}
        async for stream in self.twitch.get_videos(user_id=user.id, video_type=VideoType.ARCHIVE):
            # print( f"stream({stream.title} : {stream.duration}, id: {stream.id}, url: {stream.url})" )
            streamDict[stream.id] = (stream.title, stream.url)
            if (stream.title == title_or_streamID or stream.id == title_or_streamID):
                break
        return streamDict


    async def get_stream_range(self):
        # gets the mostrecent 'first' clip ID, and the last clip ID that was processed 'last'
        # returns tuple (first, last) 
        user = await first(self.twitch.get_users(logins='Arena_51_Gaming'))
        firstStreamID = await first(self.twitch.get_videos(user_id=user.id, video_type=VideoType.ARCHIVE))
        firstStreamID = firstStreamID.id
        with open( DEFAULT_LASTSTREAMID_FILE_LOCATION, 'r') as f:
            lastStreamID = f.readline()
        with open( DEFAULT_LASTSTREAMID_FILE_LOCATION, 'w') as f:
            # update the txt file to now have the most recent streamID as its 'most recently processed clip'
            f.write(firstStreamID)
        return (firstStreamID, lastStreamID)


    async def get_clip_range(self):
        # gets the mostrecent 'first' clip ID, and the last clip ID that was processed 'last'
        # returns tuple (first, last) 
        user = await first(self.twitch.get_users(logins='Arena_51_Gaming'))
        fistClipID = await first(self.twitch.get_clips(user.id))
        fistClipID = fistClipID.id
        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'r') as f:
            lastClipID = f.readline()
        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'w') as f:
            # update the txt file to now have the most recent clipID as its 'most recently processed clip'
            f.write(fistClipID)
        return (fistClipID, lastClipID)


    async def get_clips_to_process(self):
        # twitch = asyncio.run(twitch_oAuthlogin())
        firstClp, lastClp = await self.get_clip_range()
        clipDict = await self.get_clips_until(lastClp)
        return clipDict


    async def get_streams_to_process(self):
        # twitch = asyncio.run(twitch_oAuthlogin())
        firstStrm, lastStrm = asyncio.run(self.get_stream_range())
        streamDict = await self.get_streams_until(lastStrm)
        print(streamDict)
        return streamDict


    def clipToSting(self, clip):
        return f"'{clip.title}' Clipped By: {clip.creator_name}:\t{clip.url}"


    def clipDictToString(self, clipDictionary):
        retSrt = ""
        for key in clipDictionary.keys():
            retSrt += f"{self.clipToSting(clipDictionary[key])}\n"
        print(retSrt)
        return retSrt


# Redirect URL: http://localhost:17563

if __name__ == "__main__":
    # clip ID: ExcitedPoorKiwiBloodTrail-91Q4pix6023dELgn
    # stream ID: 1641595218

    twitchProcessor = twitchUtils()
    clipDict = asyncio.run(twitchProcessor.get_clips_to_process())
    print(twitchProcessor.clipDictToString(clipDict))

