import csv, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from prep.filters import Filters

class GoalPredictionModel:
    def __init__(self):
        self.csv_predictions = './data/predictions.csv' 
        self.features = ['host_score', 'guest_score']
        self.model = LogisticRegression()
        self.inserted_matches = set()
        self.read_existing_matches()

    def train_model(self, X_train, y_train):
        #print(f"Training model...")
        self.model.fit(X_train, y_train)

    def evaluate_model(self, X_test, y_test):
        predictions = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        #print(f"Model Accuracy: {round(accuracy*100)}%")

    def predict_for_future_matches(self, future_matches):
        predictions = self.model.predict(future_matches[self.features])
        return predictions

    def __call__(self, csv_match_data, start_time, home_team, away_team, target):        
        filters = Filters(csv_match_data)
        min_date = '2022-01-01'

        team_1_matches = filters.filter_matches_by_team(home_team)
        team_1_matches = filters.filter_matches_after(team_1_matches, min_date)

        team_2_matches = filters.filter_matches_by_team(away_team)
        team_2_matches = filters.filter_matches_after(team_2_matches, min_date)

        # Create instances of the GoalPredictionModel class  prediction
        model_team_1 = model_team_2 = GoalPredictionModel()

        # Train models
        model_team_1.train_model(team_1_matches[self.features], team_1_matches[target])
        model_team_2.train_model(team_2_matches[self.features], team_2_matches[target])

        # Evaluate models if needed
        model_team_1.evaluate_model(team_1_matches[self.features], team_1_matches[target])
        model_team_2.evaluate_model(team_2_matches[self.features], team_2_matches[target])

        # Predict for future matches
        future_predictions_team_1 = model_team_1.predict_for_future_matches(team_1_matches)
        future_predictions_team_2 = model_team_2.predict_for_future_matches(team_2_matches)

        # Assuming future_predictions_team_1 and future_predictions_team_2 are the prediction arrays
        sum_true_team_1 = future_predictions_team_1.sum()
        sum_true_team_2 = future_predictions_team_2.sum()

        # Calculate the count of False
        count_false_team_1 = len(future_predictions_team_1) - sum_true_team_1
        count_false_team_2 = len(future_predictions_team_2) - sum_true_team_2
        
        is_true = sum_true_team_1+sum_true_team_2
        is_false = count_false_team_1+count_false_team_2

        perc_true = round(is_true*100/(is_true+is_false))
        perc_fail = round(is_false*100/(is_true+is_false))

        if perc_true > 68:
            print(f'{start_time} {home_team} vs {away_team} = {target.upper()} - {perc_true}%')
            self.append_to_csv(start_time, home_team, away_team, target.upper(), perc_true)

    def read_existing_matches(self):
        try:
            with open(self.csv_predictions, mode='r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    match_identifier = (row['start_time'], row['home_team'], row['away_team'], row['prediction'], row['probability'])
                    self.inserted_matches.add(match_identifier)
        except FileNotFoundError:
            # Handle the case where the file doesn't exist yet
            pass

    def append_to_csv(self, start_time, home_team, away_team, prediction, probability):
        with open(self.csv_predictions, mode='a', newline='') as csv_file:
            fieldnames = ['start_time', 'home_team', 'away_team', 'prediction', 'probability']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Check if the file is empty, if so write the header
            if csv_file.tell() == 0:
                writer.writeheader()

            match_identifier = (start_time, home_team, away_team, prediction, probability)
            
            if match_identifier not in self.inserted_matches:
                writer.writerow({
                    'start_time': start_time,
                    'home_team': home_team,
                    'away_team': away_team,
                    'prediction': prediction,
                    'probability': probability
                })

                # Add the match identifier to the set
                self.inserted_matches.add(match_identifier)