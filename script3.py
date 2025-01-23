import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import mimetypes  # For file MIME type detection

# Google Drive API Setup
def upload_to_google_drive(file_name, folder_id):
    try:
        # Retrieve the GCP credentials JSON from an environment variable
        creds_json = os.getenv('GCP_CREDENTIALS_JSON')  # Secret stored in environment variable

        if not creds_json:
            raise ValueError("Google Cloud credentials not found in environment variable 'GCP_CREDENTIALS_JSON'")

        # Write the secret JSON to a temporary file
        creds_file_path = '/tmp/gcp_credentials.json'
        with open(creds_file_path, 'w') as f:
            f.write(creds_json)

        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        credentials = Credentials.from_service_account_file(creds_file_path, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)

        # Use mimetypes module to guess the file MIME type
        file_mime = mimetypes.guess_type(file_name)[0]

        # File metadata
        file_metadata = {
            'name': os.path.basename(file_name),  # Use the file name
            'parents': [folder_id]  # Folder ID in Google Drive
        }

        # Upload file
        media = MediaFileUpload(file_name, mimetype=file_mime, resumable=True)
        uploaded_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"File uploaded successfully! File ID: {uploaded_file.get('id')}")
    except Exception as e:
        print(f"Failed to upload file to Google Drive: {e}")

# Specify download directory
download_dir = "/tmp"
os.makedirs(download_dir, exist_ok=True)

# Initialize WebDriver with headless settings
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "directory_upgrade": True
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=options)
driver.maximize_window()

def login():
    try:
        # Enter credentials
        username_field = driver.find_element(By.XPATH, "//input[@placeholder='Username']")
        password_field = driver.find_element(By.XPATH, "//input[@placeholder='Password']")
        username_field.send_keys("Santosh.hr")
        password_field.send_keys("Swastiks@1")

        # Click login button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        login_button.click()
        time.sleep(5)  # Allow time for the login to complete
        print("Logged in successfully!")
    except Exception as e:
        print("Login failed:", e)
        driver.quit()
        exit()

# Open the login page
driver.get("https://reports.bizom.in/users/login?redirect=%2Freports%2Fview%2F14085%3Furl%3Dreports%2Fview%2F14085")
login()
time.sleep(5)

try:
    # Click the date range button
    date_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "reportrangeparent0"))
    )
    date_button.click()
    print("Date button clicked successfully!")
    time.sleep(2)

    # Scroll to and click the 'This Month' button
    this_month_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//li[contains(text(), 'This Month')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", this_month_button)
    driver.execute_script("arguments[0].click();", this_month_button)
    print("'This Month' button clicked successfully!")
except Exception as e:
    print("Failed to click the 'This Month' button:", e)

time.sleep(2)

try:
    # Click the update button
    update_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "reportsUpdateButton"))
    )
    update_button.click()
    print("Update button clicked successfully!")
except Exception as e:
    print("Failed to click the Update button:", e)

time.sleep(5)

try:
    # Open download dropdown
    dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "option-dropdown"))
    )
    dropdown.click()
    print("Dropdown clicked successfully!")
except Exception as e:
    print("Failed to click the dropdown:", e)

try:
    # Click the download button
    download_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "downloadReportIcon"))
    )
    download_button.click()
    print("Download button clicked successfully!")
except Exception as e:
    print("Failed to click the download button:", e)

# Wait for file to download
time.sleep(30)

# Convert downloaded file to CSV
def convert_to_csv(file_path):
    csv_file_path = file_path.rsplit('.', 1)[0] + '.csv'
    try:
        if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        elif file_path.endswith(".txt") or file_path.endswith(".csv"):
            df = pd.read_csv(file_path, sep=None, engine='python')
        else:
            raise ValueError("Unsupported file format. Unable to convert.")
        df.to_csv(csv_file_path, index=False, encoding='utf-8')
        print(f"Converted to CSV: {csv_file_path}")
        return csv_file_path
    except Exception as e:
        print(f"Failed to convert file to CSV: {e}")
        return None

downloaded_files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
if downloaded_files:
    latest_file = max(downloaded_files, key=os.path.getctime)
    print(f"File downloaded: {latest_file}")
    csv_file = convert_to_csv(latest_file)

    if csv_file:
        folder_id = "1ExUiSHsJSfgrsLAtGk3MOqAM5_pvC22h"
        upload_to_google_drive(csv_file, folder_id)
else:
    print("No file downloaded.")

driver.quit()
