import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText
import json


class GmailClient:
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        if not self.creds or not self.creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
            self.creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        self.service = build('gmail', 'v1', credentials=self.creds)

    def list_messages(self, label_ids=None, max_results=10):
        try:
            results = self.service.users().messages().list(userId='me', labelIds=label_ids or [], maxResults=max_results).execute()
            messages = results.get('messages', [])
            return messages
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def get_message(self, msg_id):
        try:
            message = self.service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            return message
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def get_senders_from_last_n_emails(self, n=5, label_ids=None):
        messages = self.list_messages(label_ids=label_ids, max_results=n)
        senders = []
        for msg in messages:
            msg_detail = self.get_message(msg['id'])
            if not msg_detail:
                continue
            headers = msg_detail['payload']['headers']
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            senders.append(sender)
        return senders

    def get_email_summary(self, n=5, label_ids=None):
        messages = self.list_messages(label_ids=label_ids, max_results=n)
        emails = []
        for i, msg in enumerate(messages):
            msg_detail = self.get_message(msg['id'])
            if not msg_detail:
                continue
            headers = msg_detail['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            snippet = msg_detail.get('snippet', '')
            emails.append(f"Email #{i+1}\nFrom: {sender}\nSubject: {subject}\nSnippet: {snippet}")
        return "\n\n---\n\n".join(emails)

    def get_email_content(self, msg_id):
        msg_detail = self.get_message(msg_id)
        if not msg_detail:
            return None

        parts = msg_detail['payload'].get('parts')
        body = None
        if parts:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8')
                        break
        else:
            data = msg_detail['payload']['body'].get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')

        return body or "No content found."

    def send_email(self, to, subject, message_text):
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = 'me'
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            message = self.service.users().messages().send(userId='me', body={'raw': raw}).execute()
            return f"Email sent successfully. ID: {message['id']}"
        except HttpError as error:
            return f"An error occurred: {error}"
