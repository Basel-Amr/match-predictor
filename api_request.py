import os
import requests
import json

# Constants
API_TOKEN = '4c936cda044a4c2eaa3ed158b90e66d3'  # Replace with your actual API token
BASE_URL = 'https://api.football-data.org/v4'
HEADERS = {'X-Auth-Token': API_TOKEN}
LOGO_DOWNLOAD_PATH = r'D:\Football_Prediction_Game\assets\API_Requests'

# Ensure the logo directory exists
os.makedirs(LOGO_DOWNLOAD_PATH, exist_ok=True)

# ===== FUNCTION: Get all leagues =====
def get_leagues():
    url = f'{BASE_URL}/competitions'
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('competitions', [])
    else:
        print(f"[ERROR] {response.status_code} - {response.text}")
        return []

# ===== FUNCTION: Select league and save teams + matches =====
def select_league_and_get_details():
    leagues = get_leagues()
    if not leagues:
        print("No leagues available.")
        return

    print("\nAvailable Leagues:")
    for i, league in enumerate(leagues):
        print(f"{i+1}. {league['name']} ({league['area']['name']})")

    try:
        idx = int(input("Choose a league number: ")) - 1
        selected = leagues[idx]
        league_id = selected['id']
        league_name_clean = selected['name'].replace(" ", "_").replace("/", "_")

        # Get teams
        teams_url = f"{BASE_URL}/competitions/{league_id}/teams"
        teams = requests.get(teams_url, headers=HEADERS).json().get('teams', [])
        with open(os.path.join(LOGO_DOWNLOAD_PATH, f"{league_name_clean}_teams.txt"), 'w', encoding='utf-8') as f:
            for team in teams:
                f.write(f"{team['name']}: {team.get('crest')}\n")
        print(f"[✓] Teams saved to {league_name_clean}_teams.txt")

        # Get matches
        matches_url = f"{BASE_URL}/competitions/{league_id}/matches"
        matches = requests.get(matches_url, headers=HEADERS).json().get('matches', [])
        with open(os.path.join(LOGO_DOWNLOAD_PATH, f"{league_name_clean}_matches.json"), 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=4)
        print(f"[✓] Matches saved to {league_name_clean}_matches.json")

    except Exception as e:
        print(f"[ERROR] {e}")

# ===== FUNCTION: World Cup Matches =====
def get_world_cup_matches():
    url = f"{BASE_URL}/competitions/WC/matches"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('matches', [])
    else:
        print(f"[ERROR] {response.status_code} - {response.text}")
        return []

# ===== FUNCTION: Team Matches =====
def get_team_matches(team_name):
    url = f"{BASE_URL}/teams"
    print("[!] API does not support direct listing of all teams globally.")
    print("Please get the team ID from a league first.")
    return []

# ===== FUNCTION: Get Match Score by Match ID =====
def get_match_score(match_id):
    url = f"{BASE_URL}/matches/{match_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get('match', {}).get('score', {}).get('fullTime', {})
    else:
        print(f"[ERROR] {response.status_code} - {response.text}")
        return {}

# ===== FUNCTION: Club World Cup (CWC) Data =====
def get_club_world_cup_data():
    comp_code = 'CWC'
    option = input("Do you want 'teams' or 'matches'? ").strip().lower()

    if option not in ['teams', 'matches']:
        print("[X] Invalid option. Type 'teams' or 'matches'.")
        return

    url = f"{BASE_URL}/competitions/{comp_code}/{option}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        if option == 'teams':
            for team in data.get('teams', []):
                print(f"• {team['name']}")
        else:
            for m in data.get('matches', []):
                h, a = m['homeTeam']['name'], m['awayTeam']['name']
                score = m['score']['fullTime']
                print(f"{h} vs {a} | Score: {score['home']} - {score['away']}")
    else:
        print(f"[ERROR] {response.status_code} - {response.text}")

# ===== MENU DRIVER =====
def main():
    while True:
        print("\n⚽ Football API Menu:")
        print("1. List all leagues")
        print("2. Choose league -> Save teams and matches")
        print("3. Get FIFA World Cup matches")
        print("4. Get matches for a team (requires team ID)")
        print("5. Get match score (by match ID)")
        print("6. Get Club World Cup (teams or matches)")
        print("7. Exit")

        ch = input("Choose an option (1-7): ")

        if ch == '1':
            for l in get_leagues():
                print(f"{l['name']} ({l['code']})")
        elif ch == '2':
            select_league_and_get_details()
        elif ch == '3':
            for m in get_world_cup_matches():
                print(f"{m['homeTeam']['name']} vs {m['awayTeam']['name']} on {m['utcDate']}")
        elif ch == '4':
            team = input("Enter team name (you must find team ID first): ")
            get_team_matches(team)
        elif ch == '5':
            match_id = input("Enter match ID: ")
            score = get_match_score(match_id)
            print(f"Score: {score}")
        elif ch == '6':
            get_club_world_cup_data()
        elif ch == '7':
            break
        else:
            print("[X] Invalid choice.")

if __name__ == '__main__':
    main()