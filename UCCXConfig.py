from time import sleep

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET

from urllib3 import Retry



def getagents(hostname, username, password):
    # Loading Resources ...
    resources = requests.get('https://'+hostname+'/adminapi/resource', auth=HTTPBasicAuth(username, password), verify=False)
    #  200 if success

    # Creating Tree...

    root = ET.fromstring(resources.content)
    # Tree created...
    # Putting relevant values as a dictionary in a list for improved ease of handling ...
    agents = []

    # parses resource files, go trough each resource tag
    for agent in root.findall('resource'):
        # dict returning the team name
        # print(agent.find('team').attrib)
        # print(type(agent.find('team').attrib))
        agents.append({'userID': agent.find('userID').text, 'firstName': agent.find('firstName').text,
                       'lastName': agent.find('lastName').text, 'extension': agent.find('extension').text,
                       'team': agent.find('team').attrib['name']})
    return agents


def getskills(hostname, username, password, userid):
    # retrieves the skills  and skillevel attributed to a specific agent
    # Loading Resources ...

    # this snippet implements backoff timer and retries when hammering the UCCX with api requests
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    resources = session.get('https://' + hostname + '/adminapi/resource/' + userid, auth=HTTPBasicAuth(username, password), verify=False)
    #  200 if success

    # Creating Tree...
    root = ET.fromstring(resources.content)
    # Putting relevant values as a dictionary in a list for improved ease of handling ...
    skills = []
    # in contrary to findall, iter search in all sub-elements, not only in the directly descending ones of the root
    for skill in root.iter('skillCompetency'):
        #debug information
        #print(skill.find('competencelevel').text)
        #print(skill.find('skillNameUriPair').attrib['name'])
        skills.append({'level': skill.find('competencelevel').text, 'name': skill.find('skillNameUriPair').attrib['name']})

    return skills


def getskillmap(hostname, username, password, agents):
    # separate datastructure to map skills to agent names
    skillmap = []
    i = 1
    for agent in agents:
        skill = getskills(hostname, username, password, agent['userID'])
        skillmap.append({'userID': agent['userID'], 'skills': skill})
        print(i,'/',len(agents))
        i += 1
    return skillmap


def getskilllist(agents,skillmap):
    # combines agents and skills in one array of dictionaries for better manipulation, does not include no skills agents
    skills = []
    for agent in agents:
        # reads skills of the agent:
        for agentskill in skillmap:
            if agentskill['userID'] == agent['userID']:
                agentskills = agentskill['skills']
        for skill in agentskills:
            skills.append({'userID': agent['userID'], 'extension': agent['extension'],'firstName': agent['firstName'], 'lastName': agent['lastName'], 'team': agent['team'], 'skillName': skill['name'], 'skillLevel': skill['level']})
    return skills


def getteams(hostname, username, password):
    # Loading Resources ...
    resources = requests.get('https://'+hostname+'/adminapi/team', auth=HTTPBasicAuth(username, password), verify=False)
    #  200 if success

    # Creating Tree...

    root = ET.fromstring(resources.content)
    # Tree created...
    # Putting relevant values as a dictionary in a list for improved ease of handling ...
    # [{'teamName': 'Default', 'primarySupervisor': 'none'}, {'teamName': 'tesTteam', 'primarySupervisor': 'none'}, {'teamName': 'Benelux', 'primarySupervisor': 'Dominique Verscheure'}, {'teamName': 'Germany', 'primarySupervisor': 'Nathalie Caes'}, {'teamName': 'Iberia', 'primarySupervisor': 'Dominique Vanoverberghe'}, {'teamName': 'France', 'primarySupervisor': 'Ann-Maria Sobrie'}, {'teamName': 'Italy', 'primarySupervisor': 'Mirko Alpa'}, {'teamName': 'Nordic', 'primarySupervisor': 'Dyane Defevere'}, {'teamName': 'Eastern Europe', 'primarySupervisor': 'Anna Klimova'}, {'teamName': 'Pricing', 'primarySupervisor': 'Celine Galle'}, {'teamName': 'Ecommerce', 'primarySupervisor': 'Caroline Onraet'}, {'teamName': 'UK', 'primarySupervisor': 'Dorothy Douchy'}, {'teamName': 'AfriMed', 'primarySupervisor': 'Nordine Zanki'}, {'teamName': 'South Africa', 'primarySupervisor': 'Warren Farland'}, {'teamName': 'Gunco', 'primarySupervisor': 'Maarten De Bruycker'}, {'teamName': 'Service And Repair', 'primarySupervisor': 'Pedro Vuylsteke'}, {'teamName': 'APA France', 'primarySupervisor': 'Jean-Marie Chevalier'}, {'teamName': 'North East Europe', 'primarySupervisor': 'Dorota Wiechecka'}, {'teamName': 'South-East Europe', 'primarySupervisor': 'Claudia Rosenfeld'}, {'teamName': 'Turkey', 'primarySupervisor': 'Dominique Vanoverberghe'}]
    teams = []
    primarySupervisor = ''
    secondarySupervisors = []

    # parses resource files, go trough each resource tag
    for team in root.findall('team'):
        # clear primary and secondary supervisors
        primarySupervisor = 'none'
        secondarySupervisors = []
        # dict returning the team name
        # only add single values such as
        if team.find('primarySupervisor') is not None:
            primarySupervisor = team.find('primarySupervisor').attrib['name']
        else:
            primarySupervisor = 'none'
        # checks secondary supervisors and create array out of them by going through the secsup tags
        if team.find('secondarySupervisors') is not None:
            secsuptree = team.find('secondarySupervisors')
            for supervisor in secsuptree.iter('secondrySupervisor'):
                if supervisor.attrib['name'] is not None:
                    secondarySupervisors.append(supervisor.attrib['name'])
        else:
            secondarySupervisors = ['None']

        csqs = getteamcsq(hostname,username,password,team.find('teamId').text)
        teams.append({'teamId': team.find('teamId').text,'teamName': team.find('teamname').text, 'primarySupervisor': primarySupervisor, 'secondarySupervisor': secondarySupervisors, 'csqs': csqs})
    return teams


def getteamcsq(hostname,username,password,teamid):
    # this snippet implements backoff timer and retries when hammering the UCCX with api requests
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    resources = session.get('https://' + hostname + '/adminapi/team/' + teamid, auth=HTTPBasicAuth(username, password), verify=False)
    #  200 if success
    # Creating Tree...
    root = ET.fromstring(resources.content)
    # Putting relevant values as a dictionary in a list for improved ease of handling ...
    csqs = []
    # in contrary to findall, iter search in all sub-elements, not only in the directly descending ones of the root
    for csq in root.iter('csq'):
        csqs.append(csq.attrib['name'])
    if not csqs :
        csqs.append('None')
    return csqs


def getagentsfromteam(agents, teamname):
    listofagents = []
    for agent in agents:
        if (agent['team']) == teamname:
            listofagents.append(str(agent['firstName']) + ' ' + str(agent['lastName']))
    return listofagents


def getriggercontacts(hostname, username, password):
    # get a list of all triggers, format the content so it is useable as a contact list
    triggercontacts = []
    # use the uri in the get request to retrieve the triggers
    triggers = requests.get('https://' + hostname + '/adminapi/trigger', auth=HTTPBasicAuth(username, password), verify=False)
    root = ET.fromstring(triggers.content)
    # iterates the triggers and enumerates the names and values
    for trigger in root.findall('trigger'):
        # create a contact list with specific values from the triggers, don't add triggers with wildcard X
        if 'X' not in trigger.find('directoryNumber').text:
            triggercontacts.append({'Extension': trigger.find('directoryNumber').text, 'Description': trigger.find('description').text,
                           'Application': trigger.find('application').attrib['name']})
    # returns a list of a list of trigger dicts
    return triggercontacts
