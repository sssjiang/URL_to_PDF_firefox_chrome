import sys
import time
import json
import base64
import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException


def setup_chrome_driver(headless: bool = False, download_dir: str = None) -> webdriver.Chrome:
    """Setup Chrome driver with appropriate options including download directory."""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Additional options for better compatibility
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Set download preferences
    if download_dir:
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True  # Disable PDF viewer
        }
        chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Please make sure ChromeDriver is installed and in PATH")
        sys.exit(1)


def get_drugs_com_links_with_ids(excel_path: str, target_domain: str) -> List[Dict]:
    """Read Excel file and extract links from specified domain with their IDs."""
    try:
        df = pd.read_excel(excel_path)
        
        if 'domain' not in df.columns or 'link' not in df.columns:
            raise KeyError("Required columns 'domain' and 'link' not found in Excel file")
        
        # Check for ID column (could be 'id', 'ID', 'Id', or index)
        id_column = None
        for col in ['id', 'ID', 'Id', 'index', 'Index']:
            if col in df.columns:
                id_column = col
                break
        
        # If no ID column found, use row index + 1
        if id_column is None:
            print("No ID column found, using row index as ID")
            df['generated_id'] = range(1, len(df) + 1)
            id_column = 'generated_id'
        
        # Filter for specified domain
        mims_data = df[df['domain'] == target_domain].copy()
        
        # Create list of dictionaries with id and link
        result = []
        for _, row in mims_data.iterrows():
            result.append({
                'id': row[id_column],
                'link': row['link']
            })
        
        print(f"Found {len(result)} {target_domain} links with IDs")
        return result
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []


def download_pdf_via_button(driver: webdriver.Chrome, url: str, pdf_path: str, download_dir: str, timeout: int = 30) -> bool:
    """Navigate to URL and download PDF via download button."""
    try:
        print(f"Opening: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Ensure the document is fully ready
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        # Additional wait for dynamic content
        time.sleep(3)
        
        # Try to find download button with various selectors
        download_selectors = [
            "a[href*='.pdf']",  # Direct PDF links
            "button[data-action*='download']",  # Download action buttons
            "a[class*='download']",  # Download class links
            "button[class*='download']",  # Download class buttons
            ".download-btn",  # Common download button class
            ".btn-download",  # Another common pattern
            "#download",  # Download ID
            "a[title*='download' i]",  # Download in title (case insensitive)
            "button[title*='download' i]",  # Download in title for buttons
            "[aria-label*='download' i]",  # ARIA label containing download
            "a[onclick*='download']",  # JavaScript download links
            "button[onclick*='download']",  # JavaScript download buttons
            ".fa-download",  # Font Awesome download icon
            ".icon-download"  # Generic download icon
        ]
        
        download_element = None
        used_selector = None
        
        for selector in download_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Filter for visible elements
                    visible_elements = [el for el in elements if el.is_displayed() and el.is_enabled()]
                    if visible_elements:
                        download_element = visible_elements[0]  # Take the first visible one
                        used_selector = selector
                        break
            except:
                continue
        
        if not download_element:
            print("No download button found, falling back to print PDF")
            return save_page_as_pdf(driver, url, pdf_path, timeout)
        
        print(f"Found download element using selector: {used_selector}")
        print(f"Element text: {download_element.text[:50]}...")
        
        # Clear download directory before download
        for file in os.listdir(download_dir):
            if file.endswith('.pdf'):
                try:
                    os.remove(os.path.join(download_dir, file))
                except:
                    pass
        
        # Click the download button
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", download_element)
            time.sleep(1)
            download_element.click()
            print("Download button clicked")
        except Exception as e:
            print(f"Error clicking download button: {e}")
            # Try JavaScript click as fallback
            try:
                driver.execute_script("arguments[0].click();", download_element)
                print("Download button clicked via JavaScript")
            except Exception as js_e:
                print(f"JavaScript click also failed: {js_e}")
                return False
        
        # Wait for download to complete
        print("Waiting for download to complete...")
        download_completed = False
        max_wait_time = 60  # Maximum wait time in seconds
        check_interval = 1  # Check every second
        
        for _ in range(max_wait_time):
            time.sleep(check_interval)
            
            # Check for downloaded PDF files
            pdf_files = [f for f in os.listdir(download_dir) if f.endswith('.pdf') and not f.endswith('.crdownload')]
            
            if pdf_files:
                # Find the most recently downloaded file
                latest_file = None
                latest_time = 0
                
                for file in pdf_files:
                    file_path = os.path.join(download_dir, file)
                    file_time = os.path.getctime(file_path)
                    if file_time > latest_time:
                        latest_time = file_time
                        latest_file = file
                
                if latest_file:
                    source_path = os.path.join(download_dir, latest_file)
                    shutil.move(source_path, pdf_path)
                    print(f"Downloaded and moved: {latest_file} -> {os.path.basename(pdf_path)}")
                    download_completed = True
                    break
        
        if not download_completed:
            print("Download timeout or failed, falling back to print PDF")
            return save_page_as_pdf(driver, url, pdf_path, timeout)
        
        return True
        
    except Exception as e:
        print(f"Error during download: {e}")
        print("Falling back to print PDF")
        return save_page_as_pdf(driver, url, pdf_path, timeout)


def save_page_as_pdf(driver: webdriver.Chrome, url: str, pdf_path: str, timeout: int = 30) -> bool:
    """Navigate to URL and save page as PDF."""
    try:
        print(f"Opening: {url}")
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Ensure the document is fully ready
        WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        # Emulate screen media so content hidden under @media print shows
        try:
            driver.execute_cdp_cmd("Emulation.setEmulatedMedia", {"media": "print"})
        except Exception:
            pass
        
        # Additional wait for dynamic content
        time.sleep(2)
        
        # Wait for web fonts to load (if supported)
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return (document.fonts && document.fonts.status) ? document.fonts.status : 'loaded'") == "loaded"
            )
        except Exception:
            pass
        
        # Wait for all images to load
        try:
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("""
                    var images = document.getElementsByTagName('img');
                    for (var i = 0; i < images.length; i++) {
                        if (!images[i].complete || images[i].naturalHeight === 0) {
                            return false;
                        }
                    }
                    return true;
                """)
            )
            print("All images loaded successfully")
        except TimeoutException:
            print("Some images may not have loaded completely")
        except Exception:
            pass
        
        # Wait for PDF links and embedded content to load
        try:
            WebDriverWait(driver, 20).until(
                lambda d: d.execute_script("""
                    // Check for PDF links
                    var pdfLinks = document.querySelectorAll('a[href*=".pdf"], iframe[src*=".pdf"], embed[src*=".pdf"], object[data*=".pdf"]');
                    
                    // Check for any loading indicators
                    var loadingElements = document.querySelectorAll('[class*="loading"], [class*="spinner"], [id*="loading"], [id*="spinner"]');
                    var isLoading = Array.from(loadingElements).some(el => 
                        getComputedStyle(el).display !== 'none' && 
                        getComputedStyle(el).visibility !== 'hidden'
                    );
                    
                    // Check if any AJAX requests are still pending
                    var ajaxComplete = (typeof jQuery !== 'undefined') ? jQuery.active === 0 : true;
                    
                    // Check document ready state and no pending network requests
                    var networkIdle = (typeof performance !== 'undefined' && performance.getEntriesByType) ?
                        performance.getEntriesByType('resource').filter(r => r.duration === 0).length === 0 : true;
                    
                    return !isLoading && ajaxComplete && networkIdle;
                """)
            )
            print("PDF content and links loaded successfully")
        except TimeoutException:
            print("PDF content loading timeout - proceeding anyway")
        except Exception:
            print("Could not verify PDF content loading")
            pass
        
        # Additional wait to ensure all async content is loaded
        time.sleep(3)
                

        
        # Get page title for filename reference
        page_title = driver.title
        print(f"Page title: {page_title}")
        
        # Use Chrome's built-in print to PDF functionality
        print_options = {
            'landscape': False,
            'displayHeaderFooter': False,
            'printBackground': True,
            'preferCSSPageSize': True,
            'paperWidth': 8.27,  # A4 width in inches
            'paperHeight': 11.7,  # A4 height in inches
            'marginTop': 0.4,
            'marginBottom': 0.4,
            'marginLeft': 0.4,
            'marginRight': 0.4,
            'scale': 1.0,
        }
        
        # Execute the print command
        result = driver.execute_cdp_cmd("Page.printToPDF", print_options)
        
        # Decode the base64 PDF data and save to file
        pdf_data = base64.b64decode(result['data'])
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_data)
        
        print(f"PDF saved: {pdf_path}")
        return True
        
    except TimeoutException:
        print(f"Timeout loading {url}")
        return False
    except WebDriverException as e:
        print(f"WebDriver error for {url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error for {url}: {e}")
        return False



def main():
    """Main function to automate browser operations for specified domain links."""
    # Configuration variables
    target_domain = "www.carlroth.com"
    output_dir_name = "carlroth_com_pdfs"
    
    # Default paths
    workspace_dir = Path(__file__).resolve().parent
    default_excel = workspace_dir / "aitep_references_need_fulltext_with_domain.xlsx"
    
    # Create PDF output directory
    pdf_output_dir = workspace_dir / output_dir_name
    pdf_output_dir.mkdir(exist_ok=True)
    
    # Create temporary download directory
    temp_download_dir = workspace_dir / "temp_downloads"
    temp_download_dir.mkdir(exist_ok=True)
    
    # Parse command line arguments
    excel_path = sys.argv[1] if len(sys.argv) > 1 else str(default_excel)
    headless = "--headless" in sys.argv
    max_links = 60  # Increase limit since we're saving PDFs
    
    print(f"Reading Excel file: {excel_path}")
    print(f"PDF output directory: {pdf_output_dir}")
    print(f"Headless mode: {headless}")
    
    # Get links with IDs for specified domain
    drugs_data = get_drugs_com_links_with_ids(excel_path, target_domain)
    
    if not drugs_data:
        print(f"No {target_domain} links found. Exiting.")
        return
    
    # Limit number of links to process
    if len(drugs_data) > max_links:
        print(f"Processing first {max_links} links out of {len(drugs_data)} total")
        drugs_data = drugs_data[:max_links]
    
    # Setup browser with download directory
    print("Setting up Chrome driver...")
    driver = setup_chrome_driver(headless=headless, download_dir=str(temp_download_dir))
    
    successful_downloads = 0
    failed_downloads = 0
    
    try:
        for i, data in enumerate(drugs_data, 1):
            print(f"\nProcessing link {i}/{len(drugs_data)}")
            
            link = data['link']
            link_id = data['id']
            
            # Create filename using ID
            filename = f"{link_id}.pdf"
            pdf_path = pdf_output_dir / filename
            
            print(f"ID: {link_id}, Link: {link}")
            
            # Try to download PDF via button first, fallback to print PDF
            if download_pdf_via_button(driver, link, str(pdf_path), str(temp_download_dir)):
                successful_downloads += 1
                print(f"✓ Successfully saved: {filename}")
            else:
                failed_downloads += 1
                print(f"✗ Failed to save: {filename}")
            
            # Add delay between requests to be respectful
            if i < len(drugs_data):
                print("Waiting 3 seconds before next request...")
                time.sleep(3)
    
    finally:
        print("\nClosing browser...")
        driver.quit()
        
        # Clean up temporary download directory
        try:
            shutil.rmtree(temp_download_dir)
            print("Cleaned up temporary download directory")
        except Exception as e:
            print(f"Could not clean up temp directory: {e}")
        
        print(f"\nPDF Generation Summary:")
        print(f"✓ Successful downloads: {successful_downloads}")
        print(f"✗ Failed downloads: {failed_downloads}")
        print(f"📁 PDF files saved to: {pdf_output_dir}")
        print("Browser automation completed.")


if __name__ == "__main__":
    main()
