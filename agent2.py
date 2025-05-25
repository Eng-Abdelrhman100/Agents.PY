import os
import requests
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# إعداد Gemini API
GEMINI_API_KEY = "AIzaSyDbKsUWGZq72Q6mTxlPwr2kNyM7Cihex-k"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"

# إعداد Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

# إرسال طلب إلى Gemini API
def query_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    return "Error: Unable to process request"

# إعداد Selenium WebDriver
def setup_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # معطل مؤقتًا لتسجيل الدخول
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-setuid-sandbox")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("user-data-dir=./chrome_profile")  # لحفظ جلسة WhatsApp
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# تسجيل الدخول إلى WhatsApp Web
def whatsapp_login(driver):
    driver.get("https://web.whatsapp.com/")
    print("Please scan the QR code to log in to WhatsApp...")
    try:
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.XPATH, '//div[@title="Search"]'))
        )
        print("Successfully logged in to WhatsApp!")
    except Exception as e:
        print(f"Error during login: {str(e)}")
        raise

# إرسال رسالة عبر WhatsApp Web
def send_whatsapp_message(to_number, message):
    driver = setup_driver()
    try:
        whatsapp_login(driver)
        to_number = to_number.replace("+", "").replace(" ", "")
        driver.get(f"https://web.whatsapp.com/send?phone={to_number}")
        input_box = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//div[@title="Type a message"]'))
        )
        input_box.send_keys(message)
        send_button = driver.find_element(By.XPATH, '//button[@aria-label="Send"]')
        send_button.click()
        time.sleep(3)
        return f"WhatsApp Message Sent to {to_number}"
    except Exception as e:
        return f"Error sending message: {str(e)}"
    finally:
        driver.quit()

# قراءة وتصنيف الإيميلات
def process_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    emails = results.get('messages', [])
    email_data = []
    
    for email in emails:
        msg = service.users().messages().get(userId='me', id=email['id']).execute()
        subject = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'), 'No Subject')
        snippet = msg['snippet']
        
        prompt = f"Classify this email as Important, Normal, or Spam based on subject: '{subject}' and snippet: '{snippet}'"
        classification = query_gemini(prompt)
        
        prompt = f"Summarize this email in 20 words or less: Subject: {subject}, Snippet: {snippet}"
        summary = query_gemini(prompt)
        
        email_data.append({
            'id': email['id'],
            'subject': subject,
            'classification': classification,
            'summary': summary
        })
    
    return email_data

# توليد رد على إيميل
def generate_email_response(email_id, subject, snippet):
    prompt = f"Generate a concise, professional reply for this email: Subject: {subject}, Snippet: {snippet}"
    response = query_gemini(prompt)
    return response

# عرض النصوص (محاكاة)
def display_on_screen(text):
    print(f"Displayed: {text}")

# التحكم النصي
def get_voice_command():
    return input("Enter command (e.g., 'Send whatsapp to +201287842104 message Hello' or 'exit'): ")

# معالجة الأوامر
def process_command(command):
    my_phone = "+201287842104"
    if "call" in command.lower():
        phone_number = command.split()[-1]
        result = send_whatsapp_message(phone_number, f"Calling from {my_phone}")
        display_on_screen(result)
    elif "whatsapp" in command.lower():
        parts = command.split()
        to_number = parts[parts.index("to") + 1]
        message = " ".join(parts[parts.index("message") + 1:])
        result = send_whatsapp_message(to_number, message)
        display_on_screen(result)
    elif "check emails" in command.lower():
        emails = process_emails()
        for email in emails:
            display_on_screen(f"Email: {email['subject']} | {email['classification']} | Summary: {email['summary']}")
    elif "reply to email" in command.lower():
        email_id = command.split()[-1]
        service = get_gmail_service()
        msg = service.users().messages().get(userId='me', id=email_id).execute()
        subject = next((header['value'] for header in msg['payload']['headers'] if header['name'] == 'Subject'), 'No Subject')
        snippet = msg['snippet']
        response = generate_email_response(email_id, subject, snippet)
        display_on_screen(f"Generated Reply: {response}")

# الوكيل الرئيسي
def main():
    print("AI Agent Running on Local Machine with WhatsApp Web Automation...")
    while True:
        command = get_voice_command()
        if "exit" in command.lower():
            break
        process_command(command)

if __name__ == "__main__":
    main()