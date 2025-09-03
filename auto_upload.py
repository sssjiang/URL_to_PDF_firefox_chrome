import os
import time
import re
import sys
import json
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException


def setup_chrome_driver(headless: bool = False) -> webdriver.Chrome:
    """Setup Chrome driver with appropriate options."""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless")
    
    # Basic Chrome options for better stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Please make sure chromedriver is installed and in PATH")
        print("Install with: brew install chromedriver (macOS) or download from https://chromedriver.chromium.org/")
        exit(1)


def get_pdf_files_and_ids(directory_path: str) -> List[Tuple[str, str]]:
    """
    Read directory and extract PDF files with their IDs.
    Returns list of tuples: (file_path, id)
    """
    directory = Path(directory_path)
    if not directory.exists():
        print(f"Directory {directory_path} does not exist!")
        return []
    
    pdf_files = []
    
    # Get all PDF files in directory
    for file_path in directory.glob("*.pdf"):
        # Extract ID from filename (assuming format: id.pdf)
        filename = file_path.stem  # Get filename without extension
        
        # Check if filename is a valid ID (numeric)
        if filename.isdigit():
            pdf_files.append((str(file_path), filename))
        else:
            print(f"Skipping file {file_path.name} - filename is not a valid ID")
    
    # Handle case-insensitive PDF extensions
    for file_path in directory.glob("*.PDF"):
        filename = file_path.stem
        if filename.isdigit():
            pdf_files.append((str(file_path), filename))
        else:
            print(f"Skipping file {file_path.name} - filename is not a valid ID")
    
    # Sort by ID for consistent processing order
    pdf_files.sort(key=lambda x: int(x[1]))
    
    print(f"Found {len(pdf_files)} PDF files with valid IDs")
    return pdf_files


def upload_file_to_aitep(driver: webdriver.Chrome, file_path: str, file_id: str, timeout: int = 30) -> Tuple[bool, str]:
    """
    Upload a single file to AITEP website.
    
    Args:
        driver: Chrome webdriver instance
        file_path: Full path to the PDF file
        file_id: ID extracted from filename
        timeout: Maximum time to wait for operations
    
    Returns:
        True if upload successful, False otherwise
    """
    try:
        # Construct the URL
        url = f"https://aitep.probot.hk/en/APIs/references/{file_id}"
        print(f"Opening URL: {url}")
        
        # Navigate to the page
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Set localStorage for user authentication
        userinfo = {
            "id": 71,
            "is_admin": 1,
            "username": "zelinqqq",
            "nickname": "zelinqqq",
            "email": "zelinjiang@cuhk.edu.hk",
            "mobile": "",
            "avatar": "/uploads/20250430/03c5ad5d4acfaa3d8be48f8910cb34fd.png",
            "score": 0,
            "allowed_ips": "",
            "token": "bee4eb8e-7084-40fa-9695-10eb6618f4ba",
            "user_id": 71,
            "createtime": 1756884426,
            "expiretime": 1759476426,
            "expires_in": 2592000,
            "login_ip": "137.189.241.14"
        }
        
        print("Setting localStorage userinfo...")
        driver.execute_script(f"localStorage.setItem('userinfo', '{json.dumps(userinfo)}');")
        
        # Refresh the page to apply the localStorage changes
        driver.refresh()
        
        # Wait for page to reload
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print(f"Page loaded for ID {file_id} with user authentication")
        
        # Step 1: Click the upload button with class "css-1p3hq3p ant-btn ant-btn-primary ant-btn-sm"
        print("Looking for upload button...")
        try:
            upload_button = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-1p3hq3p.ant-btn.ant-btn-primary.ant-btn-sm"))
            )
            
            print("Clicking upload button...")
            upload_button.click()
        except TimeoutException:
            # Try alternative selectors if the main one fails
            print("Primary upload button not found, trying alternative selectors...")
            try:
                # Try looking for any button with "ant-btn-primary" class
                upload_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".ant-btn.ant-btn-primary"))
                )
                print("Found alternative upload button, clicking...")
                upload_button.click()
            except TimeoutException:
                print("No upload button found on the page")
                return False, "Upload button not found"
        
        # Wait for modal/popup to appear
        time.sleep(2)
        
        # Step 2: Click the "Select File" button
        print("Looking for 'Select File' button...")
        try:
            select_file_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button//span[contains(text(), 'Select File')]"))
            )
            
            print("Clicking 'Select File' button...")
            select_file_button.click()
        except TimeoutException:
            # Try alternative approaches
            print("'Select File' button not found, trying alternative approaches...")
            try:
                # Try looking for any file input directly
                file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                print("Found file input directly, proceeding with upload...")
            except NoSuchElementException:
                # Try other common button texts
                try:
                    select_file_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Upload') or contains(text(), 'Choose File') or contains(text(), 'Browse')]"))
                    )
                    select_file_button.click()
                except TimeoutException:
                    print("No file selection button found")
                    return False, "File selection button not found"
        
        # Step 3: Handle file upload
        print(f"Uploading file: {file_path}")
        
        # Find the file input element (it might be hidden)
        file_input = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        
        # Send the file path to the input element
        file_input.send_keys(file_path)
        
        print("File selected, waiting for upload to complete...")
        
        # Wait for upload to complete by checking if "Select File" button disappears
        print("Monitoring upload progress...")
        max_wait_time = 240  # Maximum wait time in seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check if "Select File" button still exists
                select_file_button_check = driver.find_elements(By.XPATH, "//button//span[contains(text(), 'Select File')]")
                
                if not select_file_button_check:
                    # "Select File" button has disappeared, upload is complete
                    print("✓ Upload completed - 'Select File' button has disappeared")
                    break
                    
                # Check for progress indicators
                progress_elements = driver.find_elements(By.CSS_SELECTOR, ".ant-progress, .ant-upload-list-item")
                if progress_elements:
                    # Try to get upload progress percentage
                    try:
                        progress_text = driver.find_element(By.CSS_SELECTOR, ".ant-progress-text").text
                        print(f"Upload progress: {progress_text}")
                    except:
                        print("Upload in progress...")
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Error checking upload status: {e}")
                time.sleep(2)
        
        # Additional safety check - ensure we waited reasonable time
        elapsed_time = time.time() - start_time
        print(f"Upload monitoring completed after {elapsed_time:.1f} seconds")
        
        # Step 4: Click OK button
        print("Looking for 'OK' button...")
        try:
            ok_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button//span[contains(text(), 'OK')]"))
            )
            
            print("Clicking 'OK' button...")
            ok_button.click()
        except TimeoutException:
            # Try alternative button texts
            print("'OK' button not found, trying alternatives...")
            try:
                # Try common alternatives
                ok_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//button//span[contains(text(), 'Submit') or contains(text(), 'Confirm') or contains(text(), 'Save')]"))
                )
                ok_button.click()
                print("Found and clicked alternative confirmation button")
            except TimeoutException:
                print("No confirmation button found, upload may have completed automatically")
                # Sometimes uploads complete without needing to click OK
        
        # Wait for confirmation or page update
        time.sleep(3)
        
        print(f"✓ Successfully uploaded file for ID {file_id}")
        return True, "Upload successful"
        
    except TimeoutException as e:
        error_msg = f"Timeout error: {str(e)}"
        print(f"✗ Timeout error for ID {file_id}: {e}")
        return False, error_msg
    except WebDriverException as e:
        error_msg = f"WebDriver error: {str(e)}"
        print(f"✗ WebDriver error for ID {file_id}: {e}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"✗ Unexpected error for ID {file_id}: {e}")
        return False, error_msg


def create_log_file() -> str:
    """Create a log file for tracking upload results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"upload_log_{timestamp}.txt"
    return log_filename


def log_message(message: str, log_file: str = None):
    """Log message to both console and file."""
    print(message)
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")


def main():
    """Main function to automate file uploads to AITEP."""
    # Configuration
    pdf_directory = "/Users/zelinjiang/Downloads/journal"
    headless = "--headless" in sys.argv  # Allow headless mode via command line
    
    # Create log file
    log_file = create_log_file()
    
    log_message("=== AITEP File Upload Automation ===", log_file)
    log_message(f"Reading PDF files from: {pdf_directory}", log_file)
    log_message(f"Log file: {log_file}", log_file)
    log_message(f"Headless mode: {headless}", log_file)
    
    # Get list of PDF files and their IDs
    pdf_files = get_pdf_files_and_ids(pdf_directory)
    
    if not pdf_files:
        log_message("No valid PDF files found. Exiting.", log_file)
        return
    
    log_message(f"Found {len(pdf_files)} files to upload", log_file)
    
    # # For testing, only process the first file
    # if len(pdf_files) > 1:
    #     log_message("🧪 Testing mode: Only processing the first file", log_file)
    #     pdf_files = pdf_files[2:]  # Only take the first file
    
    # Setup Chrome driver
    log_message("Setting up Chrome driver...", log_file)
    driver = setup_chrome_driver(headless=headless)
    
    successful_uploads = 0
    failed_uploads = 0
    
    # Initialize results list for Excel export
    upload_results = []
    
    try:
        # Process each file
        for i, (file_path, file_id) in enumerate(pdf_files, 1):
            log_message(f"\n--- Processing file {i}/{len(pdf_files)} ---", log_file)
            log_message(f"File: {os.path.basename(file_path)}", log_file)
            log_message(f"ID: {file_id}", log_file)
            
            # Upload the file
            success, error_message = upload_file_to_aitep(driver, file_path, file_id)
            
            # Record result for Excel export
            upload_results.append({
                'ID': file_id,
                'Status': 'Success' if success else 'Failed',
                'Error_Message': error_message if not success else ''
            })
            
            if success:
                successful_uploads += 1
                log_message(f"✓ Upload successful for ID {file_id}", log_file)
            else:
                failed_uploads += 1
                log_message(f"✗ Upload failed for ID {file_id}: {error_message}", log_file)
            
            # Add delay between uploads to be respectful to the server
            if i < len(pdf_files):
                log_message("Waiting 3 seconds before next upload...", log_file)
                time.sleep(3)
    
    except KeyboardInterrupt:
        log_message("\nUpload process interrupted by user.", log_file)
    
    finally:
        log_message("\nClosing browser...", log_file)
        driver.quit()
        
        # Print summary
        log_message(f"\n=== Upload Summary ===", log_file)
        log_message(f"✓ Successful uploads: {successful_uploads}", log_file)
        log_message(f"✗ Failed uploads: {failed_uploads}", log_file)
        log_message(f"Total files processed: {successful_uploads + failed_uploads}", log_file)
        log_message(f"📄 Full log saved to: {log_file}", log_file)
        
        # Create Excel report
        if upload_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"upload_results_{timestamp}.xlsx"
            
            df = pd.DataFrame(upload_results)
            df.to_excel(excel_filename, index=False, sheet_name='Upload Results')
            
            log_message(f"📊 Excel report saved to: {excel_filename}", log_file)
            print(f"\n📊 Upload Results Summary:")
            print(f"Total processed: {len(upload_results)}")
            print(f"Successful: {successful_uploads}")
            print(f"Failed: {failed_uploads}")
            print(f"Excel report: {excel_filename}")
        
        log_message("Automation completed.", log_file)


if __name__ == "__main__":
    main()
