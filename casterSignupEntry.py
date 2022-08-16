import re
import json
from datetime import datetime, timedelta
from Constants import BROADCASTER_SIGNUPSTORE_DIR
from os.path import exists

class CSignupEntry:
    
    date = None
    prods = None
    cols = None
    pbps = None
    label_YearMonth = None
    label_YearMonthDay = None
    entrySaveFileName = None



    def __init__(self, rawSignupString, datePosted):
        strDay = re.findall('\*{2}\w*:\*{2}', rawSignupString)
        if len(strDay) == 1:
            self.date = self.__extract_post_date(datePosted, strDay[0].replace("**", "").replace(":", ""))
        else:
            unsureDay = re.findall('\*{2}\w*.*\*{2}', rawSignupString)
            for match in unsureDay:
                for d_str in match.split():
                    print(f'evaluating unsureString: {d_str}, passing: {d_str.replace("**", "").replace(":", "")}')
                    try:
                        self.date = self.__extract_post_date(datePosted, d_str.replace("**", "").replace(":", ""))
                    except DayNotFoundError:
                        continue
                    if self.date != None:
                        break
                if self.date != None:
                        break
            print(f'self.date is {self.date}')
            if self.date == None:
                raise MessageDayCountError(rawSignupString)
        
        self.prods, self.cols, self.pbps = self.__extract_broadcasters(rawSignupString)
        self.label_YearMonth = f'{self.date.year}-{self.date.month}'
        self.label_YearMonthDay = f'{self.label_YearMonth}-{self.date.day}'
        self.entrySaveFileName = f'[{self.label_YearMonth}] Broadcaster-Signup-Store.json'


    def __repr__(self):
        return "CSignupEntry()"


    def __str__(self):
        return f"<({hash(self)}): label: {self.label_YearMonthDay}, prods: {self.prods}, cols: {self.cols}, pbps: {self.pbps}>"


    def __eq__(self, other):
        return self.date == other.date and self.prods == other.prods and self.cols == other.cols and self.pbps == other.pbps
 

    def __hash__(self):
        return hash((self.date, self.prods, self.cols, self.pbps))


    def __extract_post_date(self, datePosted, listedDay):
        # the date that the message represents can be between listedDay and listedDay + 7days
        for _ in range(7): # for each day of the week 
            if datePosted.strftime("%A").lower().strip() == listedDay.lower().strip():
                return datePosted 
            datePosted += timedelta(days=1)
        raise DayNotFoundError(listedDay)


    def __extract_broadcasters(self, rawStr):

        producers, colours, playbyplays = (), (), ()
        producer_search = ' '.join(re.findall('Production\/Observer\(🎥\): (<@\d{18}> ?)*', rawStr))
        caster_pbp_search = ' '.join(re.findall('Play-By-Play\(🎙\): (<@\d{18}> ?)*', rawStr))
        caster_col_search = ' '.join(re.findall('Colour\(🔬\): (<@\d{18}> ?)*', rawStr))

        if producer_search:
            producers = tuple([ps.replace('<', '').replace('>', '').replace('@', '') for ps in producer_search.split()])
        
        if caster_pbp_search:
            colours = tuple([pbps.replace('<', '').replace('>', '').replace('@', '') for pbps in caster_pbp_search.split()])

        if caster_col_search:
            playbyplays = tuple([cols.replace('<', '').replace('>', '').replace('@', '') for cols in caster_col_search.split()])

        # can get user names here from userID's if needed

        return producers, colours, playbyplays


    def save(self):
        # save the entry to the corrrect json file
        # check if json exists,
        monthDict = {}
        saveFilePath = f'{BROADCASTER_SIGNUPSTORE_DIR}\\{self.entrySaveFileName}'
        if exists(saveFilePath):
            # read all entries into dict. Add self to that dict.
            with open(saveFilePath, 'r') as f:
                monthDict = json.load(f)

        selfSaveData = vars(self)
        selfSaveData['date'] = self.date.isoformat()
        monthDict[self.label_YearMonthDay] = selfSaveData
        
        with open(saveFilePath, 'w') as f:
            json.dump(monthDict, f)

    



class CasterSignupEntryError(Exception):
    """Base class for CSignupEntry exceptions"""
    pass


class MessageDayCountError(CasterSignupEntryError):
    """"""
    def __init__(self, rawStr, message=f"There are an incorrect number of days found in raw message string."):
        self.rawStr = rawStr
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.rawStr} -> {self.message}'


class DayNotFoundError(CasterSignupEntryError):
    """"""
    def __init__(self, rawStr, message=f"The day string listed in the raw message cannot be equated to a datetime"):
        self.rawStr = rawStr
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.rawStr} -> {self.message}'



