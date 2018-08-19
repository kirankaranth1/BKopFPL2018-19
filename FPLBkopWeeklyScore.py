from __future__ import print_function
import requests
import json
from operator import itemgetter
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from googleapiclient.http import MediaFileUpload


# Get a player's score given player ID and gw number
def get_player_score(playerId, gw):
    url = "https://fantasy.premierleague.com/drf/entry/" + str(playerId) + "/event/" + str(gw) + "/picks"

    while True:
        try:
            r = requests.get(url)
        except:
            print("\nFound exception\n")
            continue
        break

    result = json.loads(r.text)
    points = result['entry_history']['points']
    deductions = result['entry_history']['event_transfers_cost']

    weekly_score = int(points) - int(deductions)
    total_score = int(result['entry_history']['total_points'])
    return weekly_score, total_score


# Get a team's total and individual scores given team composition in player 1, player ID1, player 2 , player ID2 format
def get_team_score_weekly_overall(team_composition, gw):
    print("Fetching " + str(team_composition))
    tcompList = team_composition.split(',')
    player_name_1 = tcompList[0].strip()
    player_name_2 = tcompList[2].strip()
    player_id_1 = tcompList[1].strip()
    player_id_2 = tcompList[3].strip()

    player_1_weekly_score, player_1_total_score = get_player_score(player_id_1, gw)
    player_2_weekly_score, player_2_total_score = get_player_score(player_id_2, gw)

    weekly_team_score = player_name_1 + "," + str(player_1_weekly_score) + "," + player_name_2 + "," + str(player_2_weekly_score) + "," + str(player_1_weekly_score + player_2_weekly_score)
    overall_team_score = player_name_1 + "," + str(player_1_total_score) + "," + player_name_2 + "," + str(player_2_total_score) + "," + str(player_1_total_score + player_2_total_score)

    return weekly_team_score, overall_team_score


def upload_to_google_drive(filename):
    # If modifying these scopes, delete the file token.json.
    SCOPES = 'https://www.googleapis.com/auth/drive'

    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))

    if "Week" in filename:
        print(filename,"Week")
        file_metadata = {
            'name': filename.split('\\')[1],
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': ["1v9bxRvtvuP4NHy-yFfpT4QHUEzMq6Zkz"]
        }
    else:
        print(filename, "Overall")
        file_metadata = {
            'name': filename.split('\\')[1],
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': ["1-anHeSywvAfOe2Uis5YpoumboxSVzmPv"]
        }

    media = MediaFileUpload(filename,
                            mimetype='text/csv',
                            resumable=True)

    service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()


gw = input("Enter Gameweek number: ")

with open('TeamsWithIdsTable.csv') as teamFile:
    teams = teamFile.readlines()

weekly_filename = "Weekly\Gameweek_"+str(gw)+"_Teams_Leaderboard.csv"
overall_filename = "Overall\Overall_Teams_Leaderboard_after_gw"+str(gw)+".csv"

output_file_weekly = open(weekly_filename, "w")
output_file_overall = open(overall_filename, "w")

weekly_dict = {}
overall_dict = {}

for team in teams:
    w, o = get_team_score_weekly_overall(team, gw)
    w_key = ', '.join(w.split(',')[:-1])
    w_value = w.split(',')[-1]
    weekly_dict[w_key] = int(w_value)

    o_key = ', '.join(o.split(',')[:-1])
    o_value = o.split(',')[-1]
    overall_dict[o_key] = int(o_value)

output_file_weekly.write("Player 1" + ","+ "Player 1 gameweek score" + "," + "Player 2" + ","+ "Player 2 gameweek score" + "," + "Total team score for gameweek" + "\n")
for weekly_key, weekly_value in sorted(weekly_dict.items(), key=itemgetter(1), reverse=True):
    output_file_weekly.write(weekly_key + ","+ str(weekly_value) + "\n")

output_file_overall.write("Player 1" + "," + "Player 1 total score," + "Player 2" + ","+ "Player 2 total score" + "," + "Total team score so far" + "\n")
for overall_key, overall_value in sorted(overall_dict.items(), key=itemgetter(1), reverse=True):
    output_file_overall.write(overall_key + "," + str(overall_value) + "\n")
output_file_weekly.close()
output_file_overall.close()

upload_to_google_drive(weekly_filename)
upload_to_google_drive(overall_filename)