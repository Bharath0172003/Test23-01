import os
import pandas as pd
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from mimetypes import MimeTypes
import time

# Specify download directory
download_dir = "/tmp"  # Change to "/tmp" for GitHub Actions or Linux-based systems
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

def login():
    try:
        username_field = driver.find_element(By.XPATH, "//input[@placeholder='Username']")
        password_field = driver.find_element(By.XPATH, "//input[@placeholder='Password']")
        username_field.send_keys("Santosh.hr")
        password_field.send_keys("Swastiks@1")
        
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "login"))
        )
        login_button.click()
        time.sleep(5)
        print("Logged in successfully!")
    except Exception as e:
        print("Login failed:", e)
        driver.quit()
        exit()

# Open the login page
driver.get("https://reports.bizom.in/users/login?redirect=%2Freports%2Fview%2F14085%3Furl%3Dreports%2Fview%2F14085")
login()

# Check page content after login
print("Page content after login:", driver.page_source[:500])  # Print the first 500 characters of the page source

# Click Update Button
try:
    update_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "reportsUpdateButton"))
    )
    update_button.click()
    print("Update button clicked successfully!")
except Exception as e:
    print("Failed to click the Update button:", e)
    print(driver.page_source)  # Print the page source for debugging

time.sleep(5)

# Click Download Dropdown
try:
    dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "option-dropdown"))
    )
    dropdown.click()
    print("Dropdown clicked successfully!")
except Exception as e:
    print("Failed to click the dropdown:", e)
    print(driver.page_source)  # Print the page source for debugging

# Click Download Button
try:
    download_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "downloadReportIcon"))
    )
    download_button.click()
    print("Download button clicked successfully!")
except Exception as e:
    print("Failed to click the download button:", e)
    print(driver.page_source)  # Print the page source for debugging

# Wait and check for file download
downloaded_files = []
max_wait_time = 60  # Max wait time of 60 seconds
start_time = time.time()

while len(downloaded_files) == 0 and (time.time() - start_time) < max_wait_time:
    time.sleep(5)  # Wait for 5 seconds before checking again
    downloaded_files = [os.path.join(download_dir, f) for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]

# Check if any files are downloaded
if downloaded_files:
    latest_file = max(downloaded_files, key=os.path.getctime)
    print(f"File downloaded: {latest_file}")
else:
    print("No file downloaded after waiting.")

driver.quit()

# If no file is downloaded, skip the upload to Google Drive
if not downloaded_files:
    print("No file to upload.")
else:
    from googleapiclient.http import MediaFileUpload

    # Convert file to CSV if needed
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

    # Upload to Google Drive
    def upload_to_google_drive(file_name, folder_id=None):
        try:
            SCOPES = ['https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_file(
                r'/path/to/your/service-account-file.json',  # Replace with your service account file path
                scopes=SCOPES
            )
            service = build('drive', 'v3', credentials=creds)

            mime = MimeTypes()
            file_mime = mime.guess_type(file_name)[0]

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

    # Folder ID should be the unique part from the URL
    folder_id = '1vlqI9CZt9jgwbImKwB74pB-d7f-iOFdw'  # Replace with the actual folder ID from the URL
    latest_file = convert_to_csv(latest_file)  # Convert to CSV before uploading if needed
    upload_to_google_drive(latest_file, folder_id)
