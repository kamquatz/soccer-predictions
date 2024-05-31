import pytz
import requests, csv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class Extract:    
    def __init__(self):
        self.base_url = 'https://footystats.org/predictions/'
        self.csv_predictions = './docs/predictions.csv' 
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
            }
        self.predicted_matches = []

    def fetch_matches(self, endpoint):     
        url = self.base_url + endpoint
        matches = []

        # Send the request with headers
        response = requests.get(url, headers=self.headers)

        # Check if the request was successful
        if response.status_code == 200:
            html_content = response.text

            # Parse the HTML content
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extracting data
            match_divs = soup.find_all('div', class_='betWrapper')
            for match_div in match_divs:                
                try:
                    odds = float(match_div.find('div', class_='odds').text.strip().replace('Odds',''))
                    match_data = [data_elem.text.strip() for data_elem in match_div.find_all('div', class_='data')]
                    stat_data = [data_elem.text.strip() for data_elem in match_div.find_all('div', class_='statData')]

                    teams = match_data[0].split(' vs ')
                    start_time = datetime.strptime(match_data[1], "%dth %B at %I:%M%p").replace(year=datetime.now().year).strftime("%d-%m-%Y %H:%M:%S")

                    home_perc = float(stat_data[0].replace('%',''))
                    away_perc = float(stat_data[1].replace('%',''))

                    points_per_game_home = float(stat_data[2])
                    points_per_game_away = float(stat_data[3])

                    average_goals_home = float(stat_data[4])
                    average_goals_away = float(stat_data[5])                    

                    match = {
                        "home_team" : teams[0],
                        "away_team" : teams[1],
                        "odd" : odds,
                        "start_time" : start_time,
                        "home_perc" : home_perc,
                        "away_perc" : away_perc,
                        "points_per_game_home" : points_per_game_home,
                        "points_per_game_away" : points_per_game_away,
                        "average_goals_home" : average_goals_home,
                        "average_goals_away" : average_goals_away
                    }

                    if datetime.now().strftime('%Y-%m-%d') == datetime.strptime(start_time, ("%d-%m-%Y %H:%M:%S")).strftime('%Y-%m-%d'):
                        matches.append(match)

                except Exception as e:
                    pass

        else:
            print("Failed to retrieve the page. Status code:", response.status_code)

        return matches

    def predict(self, matches):
        team_names = []
        for match in matches:
            teams = f'{match["home_team"]} vs {match["away_team"]}'
            predictions = []

            if (match["average_goals_home"] - match["average_goals_away"]) > 1.5:
                predictions.append('1')
            elif (match["average_goals_away"] - match["average_goals_home"]) > 1.5:
                predictions.append('2')

            if (match["average_goals_home"] > 2 and match["average_goals_away"] > 2): # or (match["average_goals_home"] > 1 and match["average_goals_away"] > 2):
                predictions.append('GG')
            elif match["average_goals_home"] < 1 and match["average_goals_away"] < 1:
                predictions.append('NG')
            
            total_possible_goals = match["average_goals_home"] + match["average_goals_away"]
            if total_possible_goals > 4:
                predictions.append('OV2.5')
            elif total_possible_goals > 2:
                predictions.append('OV1.5')
            
            if teams not in team_names and predictions:
                team_names.append(teams)
                match["prediction"] = ' & '.join(map(str, predictions))
                self.predicted_matches.append(match)

    def append_to_csv(self, start_time, home_team, away_team, prediction, home_prob, away_prob, overall_prob, odds):
        try:
            with open(self.csv_predictions, mode='a', newline='') as csv_file:
                fieldnames = ['start_time', 'parent_match_id', 'home_team', 'away_team', 'prediction', 'home_prob', 'away_prob', 'overall_prob', 'status', 'odd']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                # Check if the file is empty, if so write the header
                if csv_file.tell() == 0:
                    writer.writeheader()

                writer.writerow({
                    'start_time': start_time,
                    'parent_match_id': '',
                    'home_team': home_team,
                    'away_team': away_team,
                    'prediction': prediction,
                    'home_prob': home_prob,
                    'away_prob': away_prob,
                    'overall_prob': overall_prob,
                    'status': '',
                    'odd': odds
                })

        except Exception as e:
            print(f"An error occurred in append_to_csv: {e}")

    def get_start_time(self, match):
        return match["start_time"]

    def update_match(self, match):
        try:
            url = "https://tipspesa.uk/match-update"                     
            
            params = f'update_match=update_match&kickoff={match["start_time"]}&home={match["home_team"]}&away={match["away_team"]}&prediction={match["prediction"]}&probability={round((match["home_perc"]+match["away_perc"])/2)}&interval=0&odd={match["odd"]}'

            headers = {
                "Accept": "application/json",
                "User-Agent": "PostmanRuntime/7.32.2"
            }

            response = requests.post(f'{url}?{params}', headers=headers)

            if response.status_code == 200:
                #reponse_json = json.loads(response.content)
                print(response.content)
                
            else:
                error_response = response.text
                # Process the error response if needed
                print(f"Error: {error_response}")

        except requests.RequestException as e:
            print(f"Request failed: {e}")
               
    def __call__(self):   
        to_return = [] 
        matches_1x2 = self.fetch_matches('1x2')     
        matches_btts = self.fetch_matches('btts') 
        matches_over_15 = self.fetch_matches('over-15-goals') 
        matches_over_25 = self.fetch_matches('over-25-goals')

        matches = matches_1x2 + matches_btts + matches_over_15 + matches_over_25
        
        self.predict(matches)
        sorted_matches = sorted(self.predicted_matches, key=self.get_start_time)

        for match in sorted_matches:
            # Parse the start_time string into a naive datetime object
            start_time_dt = datetime.strptime(match["start_time"], '%d-%m-%Y %H:%M:%S')

            # Timezone for East Africa Time (EAT)
            eat_tz = pytz.timezone('Africa/Nairobi')

            # Convert UTC time to EAT
            start_time_eat = start_time_dt.astimezone(eat_tz)

            match["start_time"] = start_time_eat.replace(tzinfo=None) #utc_time.astimezone(eat_tz).astimezone(eat_tz)
            
            if  match["prediction"] != 'OV1.5' and 'NG' not in match["prediction"]:
                # match["prediction"] = match["prediction"].replace('GG & OV1.5', 'OV1.5')
                # match["prediction"] = match["prediction"].replace('GG & OV2.5', 'OV1.5')
                # match["prediction"] = match["prediction"].replace('1 & OV1.5', 'OV1.5')
                # match["prediction"] = match["prediction"].replace('1 & OV2.5', 'OV2.5')
                # match["prediction"] = match["prediction"].replace('2 & OV1.5', 'OV1.5')
                # match["prediction"] = match["prediction"].replace('2 & OV2.5', 'OV1.5')
                # match["prediction"] = match["prediction"].replace('GG', 'OV1.5')
                                 
                to_return.append(match)
                
                self.update_match(match)

        return to_return
