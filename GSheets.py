# not using gspread because it could not be used with oauth2 user permission delegation
from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build
import credentials

# define authentication method (IPCC user) optimally move the credentials away to a json file
import UCCXConfig


def createauth():
    creds = GoogleCredentials(None,
            credentials.googleusername,
            credentials.googlesecret,
            credentials.googlerefresh,
            None,
            'https://accounts.google.com/o/oauth2/token',
            'sms-proxy')
    return creds

def createsheet(creds, title):
    # build the sheet service
    service = build('sheets', 'v4', credentials=creds)

    # define the spreadsheet
    spreadsheet = {
        'properties': {
            'title': title
        }
    }
    # create the spreadsheet
    spreadsheet = service.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()

    # print out creation
    print('Spreadsheet ID: {0}'.format(spreadsheet.get('spreadsheetId')))
    return(spreadsheet.get('spreadsheetId'))

def getskillheader():
    return ['Skill Name','Skill Level','User ID','Extension','First Name','Last Name','Team']

def getteamheader():
    return ['Team Name','Primary Supervisor','Secondary Supervisors','Assigned CSQS','Assigned Resources']

def gettriggerheader():
    return ['Number', 'Description','Application']

def getformattedskillmap(skillmap):
    skillmapformat = []
    skillmapformat.append(getskillheader())
    for agent in skillmap:
        skillmapformat.append(
            [agent['skillName'], agent['skillLevel'], agent['userID'], agent['extension'], agent['firstName'],
             agent['lastName'], agent['team']])
    return skillmapformat


def getformattedteams(teams,agents):
    #teams.append({'teamId': team.find('teamId').text,'teamName': team.find('teamname').text, 'primarySupervisor': primarySupervisor, '
    teamformat = []
    teamformat.append(getteamheader())
    for team in teams:
        print(team['teamName'])
        agentlist = UCCXConfig.getagentsfromteam(agents,team['teamName'])
        # first add two cells containing the teamname and primary supervisor
        teamformat.append(
            [team['teamName'], team['primarySupervisor']])

        # next add a vertical list of secondary supervisors
        i = 0
        # determine how many rows the sheet already has
        length = len(teamformat)

        for secsup in team['secondarySupervisor']:
            # handle the first value different since it needs to be added at the end of the row instead of creating a new one
            if i == 0:
                teamformat[-1].append(secsup)
                # don't need this step for the rest of the loop
                i = -1
            else:
                # add the supervisor on a new line, 3th column
                teamformat.append(['','',secsup])



        # add csq to the report:
        print(team['csqs'])
        i = 0
        for csq in team['csqs']:
            # handle the first value different since it needs to be added at the end of the row instead of creating a new one
            if i == 0:
                # the length-variable contains the number of rows which was in the file including the last written team
                teamformat[length-1].append(csq)
                # counts how many csqs are already written
                i = i + 1
            else:
                # this subclose will list the rest of the csqs vertically in the 4th columb
                # checks if we are still in writable fields
                if len(teamformat) >= length+i:
                    teamformat[length-1+i].append(csq)
                    i = i + 1
                else:
                    # adds csq on a new line
                    teamformat.append(['', '', '', csq])
                    i = i + 1

        # if  the list of sec csqs is shorter than the list of sec sups, fill the list with additional whitespace
        # this will prevent those spaces to be filled with agents
        while (len(teamformat) >= length+i):
            if len(team['csqs']) < len(team['secondarySupervisor']):
                teamformat[length - 1 + i].append('')
                i = i + 1


        # now add assigned resources
        i = 0
        
        for agent in agentlist:
            if i == 0:
                # appends the agent to the last full line written
                teamformat[length-1].append(agent)
                i = i + 1
            else:
                # checks if we are still in writable fields
                if len(teamformat) >= length+i:
                    teamformat[length-1+i].append(agent)
                    i = i + 1
                else:
                    # adds new line
                    teamformat.append(['', '', '','', agent])
                    i = i + 1


        #for i, agent in agentlist:
        #    if i == 0:
        #        teamformat[-1].[0].append(agent[0])
        #    else:
        #        teamformat.append([agent])



        # , team['secondarySupervisor'], team['csqs'], agentlist
        teamformat.append([''])
    return teamformat

def getformattedtriggers(triggers):
    triggersformat = []
    triggersformat.append(gettriggerheader())
    for trigger in triggers:
        triggersformat.append(
            [trigger['Extension'], trigger['Description'], trigger['Application']])
    return triggersformat

def updatesheet(creds, spreadsheet_id, values):
    # build the sheet service
    service = build('sheets', 'v4', credentials=creds)

    body = {
        'values': values
    }

    value_input_option = 'RAW'
    range_name = 'A1'

    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption=value_input_option, body=body).execute()
    return result

def createfilterskills(creds, spreadsheet_id):
    # create a filter on skills
    my_range = {
        'sheetId': 0,
        'startRowIndex': 0,
        'startColumnIndex': 0,
        'endColumnIndex': 7
    }
    addFilterViewRequest = {
        'addFilterView': {
            'filter': {
                'title': 'Sort on Skill',
                'range': my_range,
                'sortSpecs': [{
                    'dimensionIndex': 0,
                    'sortOrder': 'ASCENDING'
                }],
                'criteria': {
                }
            }
        }
    }

    body = {'requests': [addFilterViewRequest]}
    service = build('sheets', 'v4', credentials=creds)
    addFilterViewResponse = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    return addFilterViewResponse


def createfilteragents(creds, spreadsheet_id):
    # create a filter on agents
    my_range = {
        'sheetId': 0,
        'startRowIndex': 0,
        'startColumnIndex': 0,
        'endColumnIndex': 7
    }
    addFilterViewRequest = {
        'addFilterView': {
            'filter': {
                'title': 'Sort on Agent User ID',
                'range': my_range,
                'sortSpecs': [{
                    'dimensionIndex': 2,
                    'sortOrder': 'ASCENDING'
                }],
                'criteria': {
                }
            }
        }
    }

    body = {'requests': [addFilterViewRequest]}
    service = build('sheets', 'v4', credentials=creds)
    addFilterViewResponse = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    return addFilterViewResponse


def createfilterlevel(creds, spreadsheet_id):
    # create a filter on skill level
    my_range = {
        'sheetId': 0,
        'startRowIndex': 0,
        'startColumnIndex': 0,
        'endColumnIndex': 7
    }
    addFilterViewRequest = {
        'addFilterView': {
            'filter': {
                'title': 'Sort on Skill Level',
                'range': my_range,
                'sortSpecs': [{
                    'dimensionIndex': 1,
                    'sortOrder': 'DESCENDING'
                }],
                'criteria': {
                }
            }
        }
    }

    body = {'requests': [addFilterViewRequest]}
    service = build('sheets', 'v4', credentials=creds)
    addFilterViewResponse = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    return addFilterViewResponse


def createfilterteam(creds, spreadsheet_id):
    # create a filter on skill level
    my_range = {
        'sheetId': 0,
        'startRowIndex': 0,
        'startColumnIndex': 0,
        'endColumnIndex': 7
    }
    addFilterViewRequest = {
        'addFilterView': {
            'filter': {
                'title': 'Sort on Team',
                'range': my_range,
                'sortSpecs': [{
                    'dimensionIndex': 6,
                    'sortOrder': 'ASCENDING'
                }],
                'criteria': {
                }
            }
        }
    }

    body = {'requests': [addFilterViewRequest]}
    service = build('sheets', 'v4', credentials=creds)
    addFilterViewResponse = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    return addFilterViewResponse

def updatepermissions(creds, spreadsheet_id):
    # this function is currently not working because more oauth permissions are required, a new oauth link should be made
    file_id = '1wFV9n6D-GjMpCXOsOq6bMv4Y-e10188cPcT9pFQMUQQ'


    drive_service = build('drive', 'v3', credentials=createauth())

    def callback(request_id, response, exception):
        if exception:
            # Handle error
            print(exception)
        else:
            print("Permission Id: %s" % response.get('id'))

    batch = drive_service.new_batch_http_request(callback=callback)


    user_permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': 'dimension.data@tvh.com'
    }
    batch.add(drive_service.permissions().create(
            fileId=file_id,
            body=user_permission,
            fields='id',
    ))
    domain_permission = {
        'type': 'domain',
        'role': 'reader',
        'domain': 'tvh.com'
    }
    batch.add(drive_service.permissions().create(
            fileId=file_id,
            body=domain_permission,
            fields='id',
    ))
    batch.execute()
    # <HttpError 403 when requesting https://www.googleapis.com/drive/v3/files/1wFV9n6D-GjMpCXOsOq6bMv4Y-e10188cPcT9pFQMUQQ/permissions?fields=id&alt=json returned "Insufficient Permission: Request had insufficient authentication scopes.">