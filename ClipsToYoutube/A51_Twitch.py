import datetime
import json
import re
import requests
from twitchAPI.twitch import Twitch, AuthScope
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import VideoType
from twitchAPI.helper import first
import asyncio
from dateutil.relativedelta import relativedelta
import os, shutil
import subprocess
try:
    from ClipsToYoutube.ClipProcessing.ClipsProcessor import processAll_InputNoZoom
except ModuleNotFoundError:
    try:
        from ClipProcessing.ClipsProcessor import processAll_InputNoZoom
    except ModuleNotFoundError:
        raise
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


# ----- ClipsToYoutube -----
DEFAULT_TOKEN_FILE_LOCATION         = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\tokens.txt"
DEFAULT_LASTCLIPID_FILE_LOCATION    = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\lastClipID.txt"
CLIPS_PROCESSING_DIR_INPUT          = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\ClipProcessing\\Input-NoZoom"
CLIPS_PROCESSING_DIR_OUTPUT         = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\ClipProcessing\\Output"


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
        ## NOT USED
        # gets the mostrecent 'first' clip ID, and the last clip ID that was processed 'last'
        # returns tuple (first, last) 
        user = await first(self.twitch.get_users(logins='Arena_51_Gaming'))
        after_date = datetime.datetime.now() - relativedelta(months=2)
        clips = await self.twitch.get_clips(user.id, ended_at=datetime.datetime.now(), started_at=after_date)  # have to include before, as by default it returns in order of views
        clips.sort()
        fistClipID = fistClipID.id
        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'r') as f:
            lastClipID = f.readline()
        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'w') as f:
            # update the txt file to now have the most recent clipID as its 'most recently processed clip'
            f.write(fistClipID)
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
        # print(clipsList[:validClips])
        return clipsList[:validClips]


    async def get_clips_to_process(self):
        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'r') as f:
            lastClipID = f.readline()
        clipList = await self.get_clip_batch_until_clipFound(lastClipID)
        clipList = self.format_ClipsList(clipList, lastClipID)
        
        if (len(clipList) == 0):
            raise NoRecentClips(clipID=lastClipID)

        with open( DEFAULT_LASTCLIPID_FILE_LOCATION, 'w') as f:
            # update the txt file to now have the most recent clipID as its 'most recently processed clip'
            f.write(clipList[0].id)

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


class clipProcessingUtils:

    ClipPath_TwitchUrl = None
    ClipPath_LocalPreProcessed = None
    ClipPath_LocalProcessed = None
    ClipName = None
    context = None
    client = None

    clipMessageOBJ = None

    def __init__(self, TwitchClipUrl, clipMessageOBJ, ctx, client,  clipName = "NoNameClip"):
        self.ClipPath_TwitchUrl = TwitchClipUrl
        self.ClipName = clipName
        self.clipMessageOBJ = clipMessageOBJ
        self.context = ctx
        self.client = client
    

    async def updateClipMessage(self, newMessage, includeURL =  True):
        if (includeURL):
            await self.clipMessageOBJ["message"].edit(content=f"{newMessage} <{self.clipMessageOBJ['url']}>")
        else:
            await self.clipMessageOBJ["message"].edit(content=f"{newMessage}")


    async def downloadClipFromTwitchUrl(self):
        clipInputDir = CLIPS_PROCESSING_DIR_INPUT
        if (self.ClipPath_TwitchUrl == None):
            raise NameError("Need to have initialsed an instance of class clipProcessingUtils for class field ClipPath_TwitchUrl to be set.")
        self.ClipName = "".join(ch for ch in self.ClipName if ch.isalnum()) #  re.sub(r'[^\w]', ' ', self.ClipName).strip()
        self.ClipName += ".mp4"
        if (self.ClipName == ".mp4"):
            self.ClipName = "UnNamedClip.mp4"
        print(f"if os path exists: {clipInputDir}\\{self.ClipName}")
        if os.path.exists(f"{clipInputDir}\\{self.ClipName}"):
            print("in if")
            clipnamesuffix = str(datetime.datetime.now().strftime("%m/%d/%Y%H%M%S"))
            self.ClipName = self.ClipName.replace(".mp4", f"{clipnamesuffix}.mp4")
        print(f"clipname: {self.ClipName}")
        
        # more info here: https://twitch-dl.bezdomni.net/commands/download.html
        # os.system(f'python ClipsToYoutube\\twitch-dl.2.1.1.pyz download {self.ClipPath_TwitchUrl} -f mp4 -q source -o "{CLIPS_PROCESSING_DIR_OUTPUT}\\{self.ClipName}"')
        proc = subprocess.Popen(["python", "ClipsToYoutube\\twitch-dl.2.1.1.pyz", "download", self.ClipPath_TwitchUrl, "-f", "mp4", "-q", "source", "-o", f'{clipInputDir}\\{self.ClipName}'], stdout=subprocess.PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout=15)
            proc.wait(20)
        except subprocess.TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
        outString = outs.decode("utf-8")
        # print(outString )
        if ("Downloaded:" not in outString):
            raise Exception("Could not download clip.")


    def clearOutputAndInputFolders(self):
        inputFolder = CLIPS_PROCESSING_DIR_INPUT
        outputFolder = CLIPS_PROCESSING_DIR_OUTPUT
        def delFileFromFolder(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
        delFileFromFolder(inputFolder)
        delFileFromFolder(outputFolder)


    def processAllInputNoZoomClips(self):
        processAll_InputNoZoom()


    def getAllClipsInOutput(self):
        filePathList = []
        for filename in os.listdir(CLIPS_PROCESSING_DIR_OUTPUT):
                file_path = os.path.join(CLIPS_PROCESSING_DIR_OUTPUT, filename)
                try:
                    if os.path.isfile(file_path):
                        filePathList.append(file_path)
                except Exception as e:
                    print('Could not find completed file %s. Reason: %s' % (file_path, e))
        return filePathList[0]


    async def uploadLocalClipToDrive(self, localClpFilePath):
        # TODO: use refreshtoken instead so you dont need to constantly sign in:
        # https://stackoverflow.com/questions/19766912/how-do-i-authorise-an-app-web-or-installed-without-user-intervention/19766913#19766913
        FolderID_ContentQueueROOT = "1-xIFfasNyCIAv6bL4MtlddaWNisCzM8D"
        clipTitle = localClpFilePath.split('\\')[-1]
       
        # creating a folder: https://stackoverflow.com/questions/66107562/create-new-folder-on-gdrive-using-pydrive-module
        gauth = GoogleAuth()
        if (gauth.access_token_expired):
            gauth.LocalWebserverAuth() # Creates local webserver and auto handles authentication.
            """             
            # use self.context to send @ to user with login
            await self.context.channel.send(f"You'll need to authenticate with Google Drive! Click the link bellow, clikck continue anyway, and login using the agent account:")
            auth_url = gauth.GetAuthUrl()
            await self.context.channel.send(f"{auth_url}\n Please gimme the code!")
            def check(m):
                return m.channel == self.context.channel and m.author == self.context.author

            msg = await self.client.wait_for('message', check=check)
            gauth.Auth(msg) """
        drive = GoogleDrive(gauth)

        print(f"logged in, uploading file: {clipTitle}")
        fileClip = drive.CreateFile({'parents': [{'id': FolderID_ContentQueueROOT}], 'title': clipTitle})
        # Read file and set it as a content of this instance.
        fileClip.SetContentFile(localClpFilePath)
        fileClip.Upload(param={'supportsTeamDrives': True}) # Upload the file.

        print("getting sharable link")
        ## get sharable link to the file
        access_token = gauth.credentials.access_token # gauth is from drive = GoogleDrive(gauth) Please modify this for your actual script.
        file_id = fileClip['id']
        url = 'https://www.googleapis.com/drive/v3/files/' + file_id + '/permissions?supportsAllDrives=true'
        headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
        payload = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
        res = requests.post(url, data=json.dumps(payload), headers=headers)
        # SHARABLE LINK
        link = fileClip['alternateLink']
        return link

# Redirect URL: http://localhost:17563

async def main():
    twitchUrl = "https://clips.twitch.tv/CredulousEmpathicKumquatOSsloth-Us8WoYjVRJgtinLh"
    localProcessedClip = "D:\\Users\\geosp\\Documents\\Code\\PY\\Projects\\A51 Team Scheduler\\ClipsToYoutube\\ClipProcessing\\Output\\CouchPotatoesvsEulogySCRIMNIGHTlogitechdiscordClippedByFrostxtute #shorts.mp4"
    clipProcessor = clipProcessingUtils(twitchUrl, "")

    # download the clip 
    # await clipProcessor.downloadClipFromTwitchUrl()
    # clipProcessor.processAllInputNoZoomClips()

    # get processed clip from output dir
    # clipList = clipProcessor.getAllClipsInOutput()
    # print(clipList)
    clipProcessor.uploadLocalClipToDrive(localProcessedClip)


class ClipsProcessingError(Exception):
    """Base class for A51_Twitch exceptions"""
    pass


class NoRecentClips(ClipsProcessingError):
    """"""
    def __init__(self, clipID=f"yikes, idk bro. Maybe I didnt find any clips after all....", message=f"There are no more recent clips to snatch!"):
        self.message = f"{message} Last Clip ID I found was: {clipID}"
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'

    def getMessage(self):
        return f'{self.message}'



if __name__ == "__main__":
    pass
    # stream ID: 1641595218
    # twitchProcessor = twitchUtils()
    # clipDict = asyncio.run(twitchProcessor.get_clips_to_process())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

