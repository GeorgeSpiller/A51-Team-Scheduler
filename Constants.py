from os import getcwd
from re import A
from gspread import service_account
from gspread_formatting import get_user_entered_format
from datetime import timedelta, date, datetime

def cellFormat_to_color(cellformatstring):
    '''Small Global function used to convert gspread_formatting.CellFormat data to RGB color values. 
    It only returns the background color of a cell. Behaviour undefined if the cell has no background color attribute.
    
    Parameters:
        cellformatstring : cellFormat object as a string (retrieved useing get_user_entered_format(WORKSHEET,LABEL)). Must have backgroundcolor attribute as first attribute.
    Return:
        [float, float, float] : List of floats rounded to 2 dp, corresponding to the red, green and blue channels respectivly.
    '''

    # Use string comprehension to get the first attrib, almost always background color
    backgroundcolor = cellformatstring.split(')')[0]
    backgroundcolor = backgroundcolor.replace('backgroundColor=(', '').split(';')
    # format from list of strings to floats (removes the color tags red=, green=, blue=)
    if backgroundcolor[0] != 'None':
        for i, v in enumerate(backgroundcolor):
            backgroundcolor[i] = round(float(v.split('=')[1]), 2)
        return backgroundcolor
    return None


# ----- Schedule.py -----
# Create the service account from the json private key, allowing use access to the teams spreadsheet
SERVICE_ACCOUNT                     = service_account(filename=f'{getcwd()}\\auth\\plasma-respect-323910-617fd6c81027.json')
SPREADSHEET_URL                     = 'https://docs.google.com/spreadsheets/d/1n-W6oyEv4HehYN3gYcUVk7dOJQUP_Y70L7AN_Sp8Lgo/edit#gid=2043552790'
SPREADSHEET                         = SERVICE_ACCOUNT.open_by_url(SPREADSHEET_URL)
WORKSHEET                           = SPREADSHEET.get_worksheet(1)    # We only want to use the 2nd worksheet, 'Team Schedule'
WORKSHEET_AVAILABLE_CELLFORMAT      = get_user_entered_format(WORKSHEET,'C10')   # This cell is constant, formatted with the available color
WORKSHEET_NOTAVAILABLE_CELLFORMAT   = get_user_entered_format(WORKSHEET,'C11')# This cell is constant, formatted with the not available color

# use the constant cells in the sheets key to deturmine what the format for avaliable and not available is
AVAILABLE_COLOR                     = cellFormat_to_color(str(WORKSHEET_AVAILABLE_CELLFORMAT))
NOTAVAILABLE_COLOR                  = cellFormat_to_color(str(WORKSHEET_NOTAVAILABLE_CELLFORMAT))
# used to store the previous stream schedules. This would be the scraped discord message(s) as a string  
PREVIOUS_SCHEDULES_TEXTFILE         = f'{getcwd()}\\data\\previousSchedules.txt'
# used to store information about teams ad scheduleing. This is what the discord bot reads and relays to users
TEAM_SCHEDULE_INFO_JSONFILE         = f'{getcwd()}\\data\\ScheduleInfo.json'
JSON_DUMP_OBJECT                    = {  }


# ----- DiscordBot.py -----
ARENA51_GUILD_ID                    = 743968283006337116
ALLOWED_SERVERS                     = [714774324174782534, 743968283006337116, 999094760750981221]
SCHEDULE_CHANNEL_ID                 = 816724490674634772 # Testing Server: 1001559765215883344 A51: 816724490674634772
CASTERSIGNUP_CHANNEL_ID             = 810799071232393216 # A51: 810799071232393216
BOTCOMMANDS_ALLOWED_CHANNELS        = [1001915039386701965, 714774324174782537, 804415006631264306, 825990730752983040, 743968283434156033]
BROADCASTER_ROLES                   = ['caster_ow', 'observer_ow', 'producer']
PROTECTED_COMMANDS_ALLOWED_ROLES    = ['manager', 'team manager']
PREVIOUS_SCHEDULE_STRING            = ''
PREVIOUS_SCHEDULE_LOOKBACK          = 4
STREAM_RUNTIME_HOURS                = 3
STREAM_RUNTIME_MINS                 = STREAM_RUNTIME_HOURS * 60
BROADCASTER_ID_TO_NAME_FILE         = f'{getcwd()}\\data\\BroadcasterIDsAndNames.json'

# ----- casterSignupEnty -----
BROADCASTER_SIGNUPSTORE_DIR         = f'{getcwd()}\\data\\BroadcasterSigunupStore\\'



if __name__ == '__main__':
    print(f'''
# ----- Schedule.py -----
SERVICE_ACCOUNT                     = {SERVICE_ACCOUNT}
SPREADSHEET_URL                     = {SPREADSHEET_URL}
SPREADSHEET                         = {SPREADSHEET}
WORKSHEET                           = {WORKSHEET}
WORKSHEET_AVAILABLE_CELLFORMAT      = {WORKSHEET_AVAILABLE_CELLFORMAT}
WORKSHEET_NOTAVAILABLE_CELLFORMAT   = {WORKSHEET_NOTAVAILABLE_CELLFORMAT}
AVAILABLE_COLOR                     = {AVAILABLE_COLOR}
NOTAVAILABLE_COLOR                  = {NOTAVAILABLE_COLOR}
PREVIOUS_SCHEDULES_TEXTFILE         = {PREVIOUS_SCHEDULES_TEXTFILE}
TEAM_SCHEDULE_INFO_JSONFILE         = {TEAM_SCHEDULE_INFO_JSONFILE}
JSON_DUMP_OBJECT                    = {JSON_DUMP_OBJECT}

# ----- DiscordBot.py -----
ARENA51_GUILD_ID                    = {ARENA51_GUILD_ID}
ALLOWED_SERVERS                     = {ALLOWED_SERVERS}
SCHEDULE_CHANNEL_ID                 = {SCHEDULE_CHANNEL_ID}
CASTERSIGNUP_CHANNEL_ID             = {CASTERSIGNUP_CHANNEL_ID}
BOTCOMMANDS_ALLOWED_CHANNELS        = {BOTCOMMANDS_ALLOWED_CHANNELS}
BROADCASTER_ROLES                   = {BROADCASTER_ROLES}
PROTECTED_COMMANDS_ALLOWED_ROLES    = {PROTECTED_COMMANDS_ALLOWED_ROLES}
PREVIOUS_SCHEDULE_STRING            = {PREVIOUS_SCHEDULE_STRING}
PREVIOUS_SCHEDULE_LOOKBACK          = {PREVIOUS_SCHEDULE_LOOKBACK}
STREAM_RUNTIME_HOURS                = {STREAM_RUNTIME_HOURS}
STREAM_RUNTIME_MINS                 = {STREAM_RUNTIME_MINS}
    ''')