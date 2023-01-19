import datetime
from twitchAPI.twitch import Twitch, AuthScope
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import VideoType
from twitchAPI.helper import first
import asyncio
from dateutil.relativedelta import relativedelta

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
        after_date = datetime.datetime.now() - relativedelta(months=2)
        async for clip in self.twitch.get_clips(user.id, ended_at=datetime.datetime.now(), started_at=after_date):   # have to include before, as by default it returns in order of views
            if (clip.title == title_or_clipID or clip.id == title_or_clipID):
                break
            clipDict[clip.id] = clip
        return clipDict# {k: v for k, v in clipDict.items() if v is not None}


    async def get_clip_range(self):
        # gets the mostrecent 'first' clip ID, and the last clip ID that was processed 'last'
        # returns tuple (first, last) 
        user = await first(self.twitch.get_users(logins='Arena_51_Gaming'))
        after_date = datetime.datetime.now() - relativedelta(months=2)
        clips = await self.twitch.get_clips(user.id, ended_at=datetime.datetime.now(), started_at=after_date)  # have to include before, as by default it returns in order of views
        clips.sort()
        fistClipID = fistClipID.id
        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'r') as f:
            lastClipID = f.readline()
        #with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'w') as f:
            # update the txt file to now have the most recent clipID as its 'most recently processed clip'
        print("This is a reminder to uncommend line ~91  in A51_Twitch.py (to re-write the most recently processed clip)")
            #f.write(fistClipID)
        return (fistClipID, lastClipID)

    
    async def get_clip_batch(self, monthLookBack):
        user = await first(self.twitch.get_users(logins='Arena_51_Gaming'))
        clipBatch = []
        recent_date = datetime.datetime.now() + relativedelta(months=-monthLookBack)
        until_date = datetime.datetime.now() + relativedelta(months=-(monthLookBack-1))
        batchClipCount = 0
        while (batchClipCount == 0):
            batchClipCount = 20
            async for clip in self.twitch.get_clips(user.id, first=batchClipCount, ended_at=until_date, started_at=recent_date):
                clipBatch.append(clip)
                batchClipCount -= 1
        return clipBatch


    async def get_clip_batch_until_clipFound(self, title_or_clipID):
        monthLookback = 1
        clipFoundFlag = False
        clipList = []
        while not clipFoundFlag:
            currClipList = await self.get_clip_batch(monthLookback)
            for clip in currClipList:
                if (clip.title == title_or_clipID or clip.id == title_or_clipID):
                    clipFoundFlag = True
            monthLookback -= 1
            clipList.append(currClipList)
        return clipList 

    def format_ClipsList(self, clipsList, title_or_clipID):
        clipsList = [item for sublist in clipsList for item in sublist]
        clipsList.sort(reverse=True, key=self.getClipDate)

        validClips = 0
        for c in clipsList:
            if (c.title == title_or_clipID or c.id == title_or_clipID):
                return clipsList[:validClips]
            validClips +=1
        print(clipsList[:validClips])
        return clipsList[:validClips]


    async def get_clips_to_process(self):
        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'r') as f:
            lastClipID = f.readline()
        clipList = await self.get_clip_batch_until_clipFound(lastClipID)
        clipList = self.format_ClipsList(clipList, lastClipID)
        
        print(self.clipListToString(clipList))
        return clipList


    def getClipDate(self, clip):
        return clip.created_at


    def clipToSting(self, clip):
        return f"'{clip.title}' Clipped By: {clip.creator_name}.\t{clip.url}"


    def clipListToString(self, clipList):
        retSrt = ""
        for c in clipList:
            retSrt += f"{self.clipToSting(c)}, "
        return retSrt



# Redirect URL: http://localhost:17563

if __name__ == "__main__":
    # clip ID: ExcitedPoorKiwiBloodTrail-91Q4pix6023dELgn
    # stream ID: 1641595218
    twitchProcessor = twitchUtils()
    clipDict = asyncio.run(twitchProcessor.get_clips_to_process())

