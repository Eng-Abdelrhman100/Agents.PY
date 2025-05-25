import os
import json
import subprocess
import time
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
import requests
from whatsapp_agent import WhatsAppAgent
from gmail_client import GmailClient

load_dotenv()

def get_voice_command():
    print("🎤 Awaiting your command...")
    return input(">> ")

def display_on_screen(text):
    print(f"\n📢 Response:\n{text}\n{'='*40}")

  
# إعداد Gemini API
GEMINI_API_KEY = "AIzaSyDbKsUWGZq72Q6mTxlPwr2kNyM7Cihex-k"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"


def query_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    return "Error: Unable to process request"

# إعداد Gmail API
# SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
# def get_gmail_service():
#     creds = None
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#         creds = flow.run_local_server(port=0)
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
#     return build('gmail', 'v1', credentials=creds)    

# def get_recent_emails(n=5):
#     # creds = Credentials.from_authorized_user_file('token.json')
#     service = get_gmail_service()

#     response = service.users().messages().list(userId='me', maxResults=n).execute()
#     messages = response.get('messages', [])
#     emails = []

#     for i, msg in enumerate(messages):
#         msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
#         headers = msg_detail['payload']['headers']
#         subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
#         sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
#         snippet = msg_detail.get('snippet', '')
#         emails.append(f"Email #{i+1}\nFrom: {sender}\nSubject: {subject}\nSnippet: {snippet}")

#     return "\n\n---\n\n".join(emails)

def main():
    
    gmail_client = GmailClient()  # Initialize Gmail client

    try:
        while True:
            command = get_voice_command().lower()

            if "whatsapp" in command:
                # تشغيل العميل لو مش شغال
                # if whatsapp_agent is None:
                    # print("⌛ Starting WhatsApp agent...")
                    # whatsapp_agent = WhatsAppAgent()
            
                # بعد التشغيل نسأل الرقم والرسالة
                  
                to = input("To Number (+2...): ").strip()
                msg = input("Message: ").strip()

                # نرسل الرسالة ونطبع الرد
                response = whatsapp_agent.send_message(to, msg)
                display_on_screen(response)

            elif "send email" in command or "ابعت ايميل" in command:
                to = input("to: ").strip()
                subject = input("subject: ").strip()
                msg = input("message: ").strip()
                result = gmail_client.send_email(to, subject, msg)
                print(result)

            elif "last senders" in command or "مرسلين الايميلات" in command:
                n = int(input("how many emails ?"))
                senders = gmail_client.get_senders_from_last_n_emails(n)
                print("Recent Email Senders:")
                for s in senders:
                    print("-", s)

            elif "email content" in command or "محتوى الايميل" in command:
                msg_id = input("Enter Email ID: ")
                content = gmail_client.get_email_content(msg_id)
                print("Email Content: ")
                print(content)

            elif "recent emails" in command or "الايميلات الأخيرة" in command:
                n = int(input("how many emails ?"))
                summary = gmail_client.get_email_summary(n)
                print(summary)

            elif command in ["exit", "quit", "خروج"]:
                    print("👋 Exiting program...")
                    break

            else:
                    response = query_gemini(command)
                    display_on_screen(response)


    finally:
        # تأكد إغلاق العميل لو اشتغل
        if whatsapp_agent:
            print("🧹 Closing WhatsApp agent...")
            whatsapp_agent.close()
            print("✅ WhatsApp agent closed.")

if __name__ == "__main__":
    whatsapp_agent = WhatsAppAgent()  # Initialize WhatsApp agent
    main()