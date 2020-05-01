import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import kandbox_planner.config as config

token_path = config.google_calendar_token_path
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarChannelAdapter:
  def send(self, username= None, event= None):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)


    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API 
    '''
    
    '''
    res = service.events().insert(calendarId='primary', body=event).execute()
    print (   'id:', res['id'], 'iCalUID:',res['iCalUID'], 'htmlLink:---', res.get('htmlLink') )



if __name__ == '__main__':
    a = GoogleCalendarChannelAdapter()
    event = { 
        'summary': 'Pest Control for The_Company',
        'location': 'London',
        'description': """Kill rats.  \n To  <a href="http://www.google.com" class="menu-link" target="_blank">google</a>, to  <a href="http://www.kandbox.com" class="menu-link" target="_blank">company</a>, """,
        'start': {
            'dateTime': '2020-01-22T15:00:00-00:00',
            'timeZone': 'Europe/London',
        },
        'end': {
            'dateTime': '2020-01-22T17:50:00-00:00',
            'timeZone': 'Europe/London',
        }, 
        'attendees': [
            {'email': 'duan@example.com'},
            {'email': 'duanq@e.com'},
        ],
        'reminders': {
            'useDefault': False,
            'overrides': [
            {'method': 'email', 'minutes': 24 * 60},
            {'method': 'popup', 'minutes': 10},
            ],
        },
        'extendedProperties': {'private': {'planner': 'rhythm', 'id': '123'}},
    }
    a.send(event = event)
