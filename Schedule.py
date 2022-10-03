from gspread import service_account
from gspread_formatting import get_user_entered_format
from datetime import timedelta, date, datetime
from json import dumps
from os import getcwd
from Constants import *
from random import choice


'''
Note:
    1. All hardcoded ranges and cells (eg, WORKSHEET_AVAILABLE_CELLFORMAT, or thoes in get_teams()) are protected on the google sheet, meaning they cannot be changed.
'''


def is_cell_available(cell):
    '''Given a cell in the format "A1", deturmine weather its formatted in the available or not available color.
    Paramters:
        cell : The cell to read, given as a string with the first letter being the column, and the proceeding number being the row. No spaces.
    Return:
        bool : True if the cell given has the same background color as the available keyed cell.
     '''

     # get the color of the cell the user input
    cell_format_string = str(get_user_entered_format(WORKSHEET, cell))
    cell_color = cellFormat_to_color(cell_format_string)    
    # return True if the team is available
    if cell_color == AVAILABLE_COLOR:
        return True
    if cell_color == NOTAVAILABLE_COLOR:
        return False
    # if the cell given is niether, return False with a message
    print(f'Cell {cell} has color:\n\t{cell_color}\nwhich does not match iether:\n\tAVAILABLE: {AVAILABLE_COLOR}\n\tNOT AVAILABLE: {NOTAVAILABLE_COLOR}\n Assuming team in cell is not available.')
    return False


def get_teams():
    '''Retrieve a list of teams available to be placed on the schedule from the google sheet.
    Return:
        A list of 'team' lists, where each 'team' has the format:
        [team name, mon,  tue,  wed,  thur, fri,  sat,  sun,  score]
        [string,    bool, bool, bool, bool, bool, bool, bool, int  ]
        The booleans for days denote weather a team is scrimming that day. The score is always 0.
    '''
    # get all values in the spreadsheet, remove the first 12 rows so the list starts on the first team. 
    # This will always be 12 (see Note 1. above) .
    raw_team_list = WORKSHEET.get_all_values()
    raw_team_list = raw_team_list[12:]
    team_list = []

    # loop through all rows that have team info, if the team name (row[7]) is blank, the end of the table ahs been reached 
    for row in raw_team_list:
        if row[6] == '':
            break
        team_list.append(row[6:14])
        
    # format scrim days as a bool (replace all present text with True, excluding team name. '' = False)
    for index, value in enumerate(team_list):
        for innerindex, innervalue in enumerate(value):
            if innervalue == '':
                team_list[index][innerindex] = False
            elif innerindex > 0:    # for all values that re not the first ahve have text, set them to True
                team_list[index][innerindex] = True
            else:                   # change the first value (team name) to uppercase no spaces
                team_list[index][innerindex] = team_list[index][innerindex].replace(' ', '').upper()
        team_list[index].append(0)  # append score to the end of each team. Score set to 0 by default

    # remove teams that are not currently on the schedule
    team_list_culled = []
    for team_index, team_value in enumerate(team_list):
        row = 13 + team_index                   # To get the cel row number, offest of 13 is needed as the first team is on row 13 in sheets
        teamCell = 'G' + str(row)               # All team names have the avaialbility formatted and are on col G
        if(is_cell_available(teamCell)):        # if the current team is highlighted as available on sheets,
            team_list_culled.append(team_value) # add to the culled team list

    JSON_DUMP_OBJECT["Teams"] = [t[0] for t in team_list]
    JSON_DUMP_OBJECT["Teams On Schedule"] = [t[0] for t in team_list_culled]

    return team_list_culled    
        

def get_day_order(teamlist):
    ''' Gets a list of days and the number of scrims on each day, ordered from least scrims to most.
    Parameters:
        teamlist : list of teams to evaluate. Scrim days should be index 1-7 and be bool values.
    Return:
        List of lists, where inner list has the following format, sorted by number of scrims low to high:
        [ int,       int ]
        [ day index, number of scrims ]
        day index corrisponds to a day, where Where mon = 0, tue = 1, ..., sun = 6
    '''

    dayList = [] 
    for i in range(7):                      # for each day
        scrimCounter = 0
        for team in teamlist:               # count the number fo True values in the team list
            if(team[i+1] == True):
                scrimCounter += 1
        dayList.append([i, scrimCounter])   # append [day index, number of scrims] to return list
    
    return sorted(dayList, key=lambda x: x[1])# sort low to high by number of scrims


def get_previous_schedule():
    ''' Gets the string of previous shedule(s) by reading the text file. 
    Return:
        list of eah day, with spaces removed and in all caps.
    '''
    global SUNDAY_TIMECODE
    # open file, read all, format. The split val separates each day
    with open(PREVIOUS_SCHEDULES_TEXTFILE, encoding="utf8") as f:
        ps = f.readlines()
    
    formattedLS = ''.join(ps).replace(' ', '').upper().split('-----------------------------------------')

    # Get previouse schedules timecode for Sunday. Used to generate timecodes for upcomming schedule.
    # If there is a bad read (eg. text in schedule contains <t:##:t>) prompt manual entry
    if SUNDAY_TIMECODE == 0:
        try:
            SUNDAY_TIMECODE = int(formattedLS[-1].split('<T:')[1].split(':T>')[0])
        except ValueError:
            print(f'\t--- \n\tError reading timecode for sunday.')
            try:
                SUNDAY_TIMECODE = int(input('\tPlease input timecode maunally: ').upper().replace('<T:', '').replace(':T>', ''))
            except ValueError:
                print('\tBad timecode format. Examples: <t:1664733600:T>  or 1664733600 . Time code will be undefined')
                SUNDAY_TIMECODE = 0
            print('\t---')
    return formattedLS


def calculate_team_scores(teams):
    ''' The main scheduler. Scores each team from low (not likey to be streamed) to high (likely) and adds it to the score value
        The score is arbitary, and is based on the number of days since a team has been streamed. The number of days the 
        algoritm checks (lookback) is based on how many days are stored in PREVIOUS_SCHEDULES_TEXTFILE, once this limit is reached,
        all remaining unscored teams gain the same, highest score possible.

        Score is calculated by itterating over the previous schedule, starting from the most recent day. A count of each day its 
        looked back is kept (lookback), and this is used for the score. If a team is found on a day, that team is given the current 
        lookback as its score.  
    
        Parameters:
            teams : the list of teams (only the name and score are used)
        Return:
            None (teams list is edited directly)
    '''

    # get previous schedule and lookback
    previouseStreams = get_previous_schedule()
    lookback = len(previouseStreams)

    # calculate the lower bracket of scores, for teams that were previousely on the stream schedule
    for i in range(lookback):
        for team_index, team_data in enumerate(teams):
            if team_data[0] in previouseStreams[(lookback - 1) - i]:
                teams[team_index][8] = i
    
    # for teams that have not been streamed in a while, give them the highest score
    # calculate max
    highestScore = max( [team[8] for team in teams] )
    for team_index, team_data in enumerate(teams):
        if(team_data[8] == 0):  # if score has not been changed, set to max
            teams[team_index][8] = highestScore + 1

    # store team name and its score in the json file
    teamScore = []
    for team in teams:
        teamScore.append([team[0], team[8]])    # add team name and scores to list
    JSON_DUMP_OBJECT["TeamScore"] = teamScore
    JSON_DUMP_OBJECT["Highest Priority"] = highestScore + 1


def get_days_scrimming_teams(teams, dayIndex):
    ''' Get all the teams that have a scrim on a specific day
    Parameters:
        teams : the list of teams
        dayIndex : The index of the day to search (0=Mon, 1=Tue, ..., 6=Sun)
    Return:
        List of all teams that are scriming on a given day, sorted by their score highest to lowest 
    '''

    # 0 = Mon, 1 = Tue, ..., 6 = Sun
    teamsAvailable = []
    for teamData in teams:
        if(teamData[dayIndex + 1] == True): # +1 as the first value in the team list is the team name
           teamsAvailable.append(teamData)

    return sorted(teamsAvailable, key=lambda x: x[8], reverse=True)


def next_weekday(d, weekday):
    ''' This was taken from stack overflow, beacuse who in their right mind wants to deal with dates (not me lol)
        Should, given a day, return the date of the next occurance of that day.
    Parameters:
        d : the date to start the search (often the current date)
        weekday : the weekday to search for
    Return:
        a date object of the next occurance of weekday from date d
    '''

    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def fill_schedule_failsafe(order, teams):
    ''' Fills in and entries or subs in the order list with any available team, reguardless if they're already on the schedule
        for that week. Seleects team to list at random.
    Parameters:
        order   : the current order for the schedule, in order of days, with each day having [main team name, sub team name]
        teams   : list of all teams with their scrim days list
    Return:
        a new order, with any blank or 'No sub' entries replaced with a team, if possible.
    '''

    for dayIndex, dayEntry in enumerate(order):
        available_teams = get_days_scrimming_teams(teams, dayIndex)
        # only continue if there are available teams
        if len(dayEntry) == 0:
            dayEntry = ['', '']
        
        if len(available_teams) == 0 or len(dayEntry[0]) == 0:
            order[dayIndex][0] = 'No Stream'
            continue
        else:
            for team in available_teams:
                if team[0] == dayEntry[0]:
                    available_teams.remove(team)
                    break
            if len(available_teams) == 0:
                continue
        
        randomAvailableTeam = choice(available_teams)
        if dayEntry[0] == '':
            # that day has no team listed, choose a random team from avalable teams
            order[dayIndex][0] = randomAvailableTeam[0]
        if dayEntry[1] == 'No sub':
            # that day has no sub listed
            order[dayIndex][1] = randomAvailableTeam[0]
        
    return order



def get_schedule(teams):
    ''' Places teams into each day of the week (starting with the day that has the least teams scrimming) based on their score
    Substitue teams are also calculated, but a bit differently. Firstly, once the main teams have been selected and removed from 
    the pool of available teams, the next team with the highest score is chosen to be a sub. Then for all days that chosen team 
    scrim, they are placed as a sub. Then they are removed from the pool, and the process repeats, ensuring that the minimal amount
    of teams are chosen as subs.

    Paramenters:
        teams : the list of teams (name and score are read)
    Return:
        A list ordered for each day of the week (0=Mon, ect..) that contains the names of 1 to 3 teams. The team in index 0 is the
        main team. Any following teams are substitute teams, up to 2 subs. Sub teams are not guaranteed. 
    '''

    # get a formatted list of scrim days [day, number of active teams] sorted by least to most popular day 
    dayOrder = get_day_order(teams)
    final_order = [[], [], [], [], [], [], []]  # placeholders used to ensure teams are kept in the right days
    remainingTeams = teams.copy()   # used as the pool of teams to choose from. Teams chosen will be removed, so coppy list.
    originalTeams = teams.copy()

    for dayIndex, _ in dayOrder:    # list is already sorted, so the 2nd 'number of teams scrimming' value can be ignored
        available_teams = get_days_scrimming_teams(remainingTeams, dayIndex)
        if available_teams:  # if there exists teams to place on the schedule, place the next highest scoring team
            final_order.insert(dayIndex, [available_teams[0][0]]) # only insert the teamname (no other data is needed)
            del final_order[dayIndex + 1]
            remainingTeams.remove(available_teams[0])   # remove chosen team from the pool
        else:   # failsafe, if for some reason there are no available teams that scrim on a day, set team name to 'no stream'
            final_order.insert(dayIndex, ['No Stream'])
            del final_order[dayIndex + 1]

    # calculate the subs.
    # if a team is a sub, then they should be a sub for all days they scrim 
    for j in range(len(remainingTeams)):    # for all available teams remaining
        for i, data in enumerate(remainingTeams[j]):
            if data == True and type(data) == bool: # for each day that team scrims
                if (len(final_order[i-1]) <=2):     # if there is room on the final list to add them as a sub, add them
                    final_order[i-1].append(remainingTeams[j][0])
    # Make sure that there is at least some text to place as a sub, if there are no available sub teams
    for i, teams in enumerate(final_order): # for all teams in the final order
        if len(teams) == 1: # if there are no entries for any subs, append 'no subs'
            final_order[i].append("No sub")

    final_order = fill_schedule_failsafe(final_order, originalTeams)

    JSON_DUMP_OBJECT["Future Schedule"] = final_order    
    return final_order
   

def format_schedule(teamlist):
    ''' Formats the final order of the teams into a discord message, and returns the final string
    Paramters:
        teamlist : List (ordered for each day) of lists (team names in order of priority to add for that day)
    Return:
        Formatted string of schedule with sub teams denoted
    '''

    # get next weeks (from current date) monday and sunday date 
    d = date.today()
    next_monday = next_weekday(d, 0) # 0 = Monday, 1=Tuesday, 2=Wednesday...
    next_sunday = next_weekday(next_monday, 6)

    discord_message_format = f"""
    Week {next_monday.day}/{next_monday.month} - {next_sunday.day}/{next_sunday.month}

    Monday scrim <t:{SUNDAY_TIMECODE + (HAMMERTIME_DIFFERENCE * 1)}:t>
    @{teamlist[0][0]} (sub: {teamlist[0][1]})
    -----------------------------------------
    Tuesday scrim <t:{SUNDAY_TIMECODE + (HAMMERTIME_DIFFERENCE * 1)}:t>
    @{teamlist[1][0]} (sub: {teamlist[1][1]})
    -----------------------------------------
    Wednesday scrim <t:{SUNDAY_TIMECODE + (HAMMERTIME_DIFFERENCE * 1)}:t>
    @{teamlist[2][0]} (sub: {teamlist[2][1]})
    -----------------------------------------
    Thursday scrim <t:{SUNDAY_TIMECODE + (HAMMERTIME_DIFFERENCE * 1)}:t>
    @{teamlist[3][0]} (sub: {teamlist[3][1]})
    -----------------------------------------
    Friday scrim <t:{SUNDAY_TIMECODE + (HAMMERTIME_DIFFERENCE * 1)}:t>
    @{teamlist[4][0]} (sub: {teamlist[4][1]})
    -----------------------------------------
    Saturday scrim <t:{SUNDAY_TIMECODE + (HAMMERTIME_DIFFERENCE * 1)}:t>
    @{teamlist[5][0]} (sub: {teamlist[5][1]})
    -----------------------------------------
    Sunday scrim <t:{SUNDAY_TIMECODE + (HAMMERTIME_DIFFERENCE * 1)}:t>
    @{teamlist[6][0]} (sub: {teamlist[6][1]})

    *Subject to broadcaster availability"""  
    return discord_message_format



def main():
    '''  produces a stream schedule '''

    # get a formatted list of teams [name, bool scrim days...., score]
    print('Schedule Generation:\n\tRetrieving teams from Google Sheets...')
    teams = get_teams()

    # calculate team scores
    print('\tCalculating team priority scores...')
    calculate_team_scores(teams)

    # construct schedule
    print('\tConstructing the schedule....')
    order = get_schedule(teams)

    # write data to json file
    JSON_DUMP_OBJECT['Date Compiled'] = str(datetime.now())
    with open(TEAM_SCHEDULE_INFO_JSONFILE, "w") as f:
        f.write(dumps(JSON_DUMP_OBJECT))

    print('Schedue Generation Finished.')

    # output the formated schedule
    return format_schedule(order)


if __name__ == '__main__':
    print(main())

