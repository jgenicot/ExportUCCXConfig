import datetime
import requests
import UCCXConfig
import exportcsv
import GSheets
import credentials

from requests.auth import HTTPBasicAuth

# disables ssl warnings, need to import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def main():
    hostname = credentials.hostname
    apiusername = credentials.apiusername
    apipassword = credentials.apipassword

    # define title gsheet
    datestr = datetime.datetime.now().strftime('%d/%m/%Y')
    title = 'Agent-Skill Mapping ' + datestr

    #title = 'TVHA Agent-Skill Mapping ' + datestr


    # retrieve a list of dictionaries, each dictionary is an uccx-resource (agents)
    print('Retrieving agents from UCCX...')
    agents = UCCXConfig.getagents(hostname, apiusername, apipassword)
    print(len(agents), 'agents retrieved\n')

    # put the skillmapping in a separate data structure
    print('Retrieving skills from UCCX...')
    skillmap = UCCXConfig.getskillmap(hostname, apiusername, apipassword, agents)
    skills = UCCXConfig.getskilllist(agents,skillmap)
    print(skills)


    # write result to CSV
    exportcsv.exportskillmap(skills,'skillmap.csv')


    # write result to Google Sheets
    # first format the data
    gsheetexport = GSheets.getformattedskillmap(skills)

    #authenticate
    print('Authenticating to the Google API ...')
    auth = GSheets.createauth()

    # create a new spreadsheet
    sheetid = GSheets.createsheet(auth,title)
    print('Google Sheet created: https://docs.google.com/spreadsheets/d/{0}/edit#gid=0'.format(sheetid))

    # populate the sheet
    result = GSheets.updatesheet(auth,sheetid,gsheetexport)
    print('{0} cells updated.'.format(result.get('updatedCells')))

    #create filters
    result = GSheets.createfilteragents(auth,sheetid)
    print('{0} filter created.'.format(result.get('filterViewId')))

    result = GSheets.createfilterskills(auth,sheetid)
    print('{0} filter created.'.format(result.get('filterViewId')))

    result = GSheets.createfilterlevel(auth,sheetid)
    print('{0} filter created.'.format(result.get('filterViewId')))

    result = GSheets.createfilterteam(auth,sheetid)
    print('{0} filter created.'.format(result.get('filterViewId')))

    # share file
    # not implemented

    # create teams overview
    print('Retrieving teams from UCCX...')
    teams = UCCXConfig.getteams(hostname, apiusername, apipassword)
    print(len(teams), 'teams retrieved\n')

    # create a new spreadsheet
    sheetid = GSheets.createsheet(auth,'teams')
    print('Google Sheet created: https://docs.google.com/spreadsheets/d/{0}/edit#gid=0'.format(sheetid))

    # write result to Google Sheets
    # first format the data
    print(teams)
    gsheetexport = GSheets.getformattedteams(teams,agents)

    # populate the sheet
    result = GSheets.updatesheet(auth,sheetid,gsheetexport)
    print('{0} cells updated.'.format(result.get('updatedCells')))



    return 0



if __name__ == '__main__':
    main()
