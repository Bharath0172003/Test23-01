from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import mimetypes  # Add this import

# Specify download directory
download_dir = "/tmp"
os.makedirs(download_dir, exist_ok=True)

# Initialize WebDriver with headless settings
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Set download preferences for Chrome
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "directory_upgrade": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
driver.maximize_window()

# Login function
def login():
    try:
        username_field = driver.find_element(By.XPATH, "//input[@placeholder='Username']")
        password_field = driver.find_element(By.XPATH, "//input[@placeholder='Password']")
        username_field.send_keys("Santosh.hr")
        password_field.send_keys("Swastiks@1")
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)
        print("Logged in successfully!")
    except Exception as e:
        print("Login failed:", e)
        driver.quit()
        exit()

driver.get("https://swastiksmasala.bizom.in/users/login")
login()

driver.get("https://swastiksmasala.bizom.in/users/ajaxuserindex")
time.sleep(5)

# Click All Users
try:
    download_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "allusersid"))
    )
    download_button.click()
    print("All User button clicked successfully!")
except Exception as e:
    print("Failed to click the All User button:", e)
time.sleep(2)

# Click Download Button
try:
    download_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "userdownloadcsv"))
    )
    download_button.click()
    print("Download button clicked successfully!")
except Exception as e:
    print("Failed to click the download button:", e)

# Wait time to allow the file to download
time.sleep(20)

# Convert file to CSV
def convert_to_csv(file_path):
    try:
        if file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
        elif file_path.endswith((".txt", ".csv")):
            df = pd.read_csv(file_path, sep=None, engine="python")
        else:
            raise ValueError("Unsupported file format.")
        csv_file_path = file_path.rsplit(".", 1)[0] + ".csv"
        df.to_csv(csv_file_path, index=False)
        print(f"Converted to CSV: {csv_file_path}")
        return csv_file_path
    except Exception as e:
        print(f"Failed to convert file to CSV: {e}")
        return None

# Get the latest downloaded file
downloaded_files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
if downloaded_files:
    latest_file = max(downloaded_files, key=os.path.getctime)
    print(f"File downloaded: {latest_file}")
    latest_file = convert_to_csv(latest_file)  # Convert the file to CSV
else:
    print("No file downloaded.")
    latest_file = None

driver.quit()

# Upload to Google Drive
def upload_to_google_drive(file_name, folder_id=None):
    try:
        # Retrieve the GCP credentials JSON from GitHub Secrets
        creds_json = os.getenv('GCP_CREDENTIALS_JSON')  # Secret stored in GitHub

        # Write the secret JSON to a temporary file
        creds_file_path = '/tmp/gcp_credentials.json'
        with open(creds_file_path, 'w') as f:
            f.write(creds_json)

        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(creds_file_path, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        # Use mimetypes module to guess file MIME type
        file_mime = mimetypes.guess_type(file_name)[0]

        file_metadata = {'name': os.path.basename(file_name)}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_name, mimetype=file_mime)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        print(f"File uploaded to Google Drive with ID: {file.get('id')}")
    except Exception as e:
        print("Failed to upload to Google Drive:", e)

# Google Drive folder ID
folder_id = "1TaDSIYndqnkYwuOIfLlQhdaPkTJ5ecTG"
if latest_file:
    upload_to_google_drive(latest_file, folder_id)
else:
    print("No file to upload.")


