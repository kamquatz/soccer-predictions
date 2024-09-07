
import uuid, random
from datetime import datetime
from utils.helper import Helper
from utils.postgres_crud import PostgresCRUD
from utils.waapi import WaAPI

class Broadcast():
    def __init__(self):        
        self.helper = Helper()
        self.postgres_crud = PostgresCRUD()
        self.waapi = WaAPI()

    def send_welcome_message(self, phone):        
        message = '''Welcome to TipsPesa Sure Betting Tips.
We will send Predictions everyday with a unique link to view all predicted games.
Terms and conditions apply.'''

        self.waapi.send_message(phone, message)
        
        message = self.upcoming_message()
        self.waapi.send_message(phone, message)

    def send_goodbye_message(self, phone):        
        message = '''It's sad to see you leave.
We will NOT send you any more Predictions.
To Subscribe back, Reply with the word "subscribe".'''

        self.waapi.send_message(phone, message)
        
    def yesterday_message(self):
        matches, played, won = self.helper.fetch_matches('-1', '=')
        
        if len(matches) > 0:
            message = f'''Yesterday *{won}* of {played} Predicted Matches Won
            
'''
            for match in matches:
                if match.status is not None:
                    message = message + f'''{match.home_team} vs {match.away_team} - {match.prediction} [{match.home_results}-{match.away_results}]
'''

            message = message + ''' ...
            
Details - https://tipspesa.uk/yesterday/guest
Reply with 1 to get Today Sure Tips'''

            return message.strip()  
        else:
            return None
        

    def upcoming_message(self):
        matches, played, won = self.helper.fetch_matches('', '=', '')
        
        if len(matches) > played:
            today_codes = str(uuid.uuid5(uuid.NAMESPACE_DNS, datetime.now().strftime('%Y%m%d'))).split('-')
            
            message = f'''*Today Predictions*
'''
            for match in matches:
                #if match.status is None:
                message = message + f'''{match.home_team} vs {match.away_team} - {match.prediction}
'''

            message = message + f''' ...
            
All Tips - https://tipspesa.uk/{random.choice(today_codes)}'''

            return message.strip()
        else:
            return None
    
    def send_message(self, message, status):  
        active_subscribers = self.postgres_crud.fetch_subscribers(status)
        for subscriber in active_subscribers:
            phone = subscriber[0]
            self.waapi.send_message(phone, message)            
     
    def __call__(self):
        """
        class entry point
        """
        
        #message = self.yesterday_message()
        
        message = self.upcoming_message()
        self.send_message(message, 1)
              
            
if __name__ == "__main__":
    Broadcast()()