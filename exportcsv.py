# writes content to csv file duplicates users in case of multiple skills

import csv


def exportskillmap(skillmap,filename):
    #this function will only write agents with skills to the file
    with open(filename, mode='w', newline='') as exportfile:
        csvwriter = csv.writer(exportfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # print header
        csvwriter.writerow(['Skill Name','Skill Level','User ID','Extension','First Name','Last Name','Team'])
        for agent in skillmap:
            csvwriter.writerow([agent['skillName'],agent['skillLevel'],agent['userID'],agent['extension'],agent['firstName'], agent['lastName'], agent['team']])
