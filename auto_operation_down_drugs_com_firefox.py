import sys
import time
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import re
from urllib.parse import urlparse

import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


def setup_firefox_driver(headless: bool = False, download_dir: str = None) -> webdriver.Firefox:
    """Setup Firefox driver with appropriate options."""
    firefox_options = Options()
    
    if headless:
        firefox_options.add_argument("--headless")
    
    # Set preferences for better PDF handling and printing
    download_directory = download_dir or str(Path.cwd())
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_options.set_preference("browser.download.dir", download_directory)
    firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
    firefox_options.set_preference("pdfjs.disabled", True)
    firefox_options.set_preference("plugin.scan.plid.all", False)
    firefox_options.set_preference("plugin.scan.Acrobat", "99.0")
    
    # Essential print to PDF settings
    firefox_options.set_preference("print.always_print_silent", True)
    firefox_options.set_preference("print.show_print_progress", False)
    firefox_options.set_preference("print.printer_Mozilla_Save_to_PDF.print_to_file", True)
    firefox_options.set_preference("print_printer", "Mozilla Save to PDF")
    firefox_options.set_preference("print.print_printer", "Mozilla Save to PDF")
    
    # Additional PDF settings
    firefox_options.set_preference("print.save_print_settings", True)
    firefox_options.set_preference("print.print_bgcolor", True)
    firefox_options.set_preference("print.print_bgimages", True)
    
    try:
        driver = webdriver.Firefox(options=firefox_options)
        return driver
    except Exception as e:
        print(f"Error setting up Firefox driver: {e}")
        print("Please make sure geckodriver is installed and in PATH")
        print("Install with: brew install geckodriver (macOS) or download from https://github.com/mozilla/geckodriver/releases")
        sys.exit(1)


def get_drugs_com_links_with_ids(excel_path: str) -> List[Dict]:
    """Read Excel file and extract www.drugs.com links with their IDs."""
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
        
        # Filter for www.drugs.com domain
        drugs_data = df[df['domain'] == 'www.drugs.com'].copy()
        
        # Create list of dictionaries with id and link
        result = []
        for _, row in drugs_data.iterrows():
            result.append({
                'id': row[id_column],
                'link': row['link']
            })
        
        print(f"Found {len(result)} www.drugs.com links with IDs")
        return result
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []


def save_page_as_pdf_firefox(driver: webdriver.Firefox, url: str, pdf_path: str, timeout: int = 15) -> bool:
    """Navigate to URL and save page as PDF using Firefox."""
    try:
        print(f"Opening: {url}")
        driver.get(url)
        
        # Wait for page to load completely
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for document ready state
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Additional wait for dynamic content and images
        time.sleep(3)
        
        # Get page title for verification
        page_title = driver.title
        print(f"Page title: {page_title}")
        
        # Scroll to trigger lazy loading and ensure all content is loaded
        try:
            # Get initial height
            last_height = driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to the bottom
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait for new content to load
                time.sleep(2)
                
                # Calculate new scroll height and compare to last height
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Scroll back to top
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            print(f"Scrolling error (non-critical): {e}")
        
        # Use Firefox's print to PDF functionality with proper settings
        try:
            # Method 1: Try Selenium 4.0+ print_page method first
            try:
                print("Trying Selenium print_page method...")
                pdf_data = driver.print_page()
                if pdf_data and len(pdf_data) > 0:
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_data)
                    print(f"PDF saved successfully using print_page: {pdf_path} ({len(pdf_data)} bytes)")
                    return True
                else:
                    print("print_page returned empty data")
            except AttributeError:
                print("Selenium print_page method not available")
            except Exception as e:
                print(f"print_page failed: {e}")
            
            # Method 2: Use JavaScript to set print settings and trigger print
            print("Trying JavaScript print method...")
            try:
                # Set the output file path via JavaScript
                driver.execute_script(f"""
                    // Configure print settings
                    window.print_to_file_path = "{pdf_path}";
                """)
                
                # Configure print options via CDP if available
                try:
                    driver.execute_cdp_cmd("Page.printToPDF", {
                        "landscape": False,
                        "displayHeaderFooter": False,
                        "printBackground": True,
                        "scale": 1.0,
                        "paperWidth": 8.27,
                        "paperHeight": 11.7,
                        "marginTop": 0.4,
                        "marginBottom": 0.4,
                        "marginLeft": 0.4,
                        "marginRight": 0.4,
                        "path": pdf_path
                    })
                    
                    # Wait and check if file was created
                    time.sleep(2)
                    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                        file_size = os.path.getsize(pdf_path)
                        print(f"PDF saved successfully using CDP: {pdf_path} ({file_size} bytes)")
                        return True
                        
                except Exception as e:
                    print(f"CDP method failed: {e}")
                
                # Fallback: Use window.print() 
                driver.execute_script("window.print();")
                time.sleep(5)  # Wait longer for print dialog
                
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    file_size = os.path.getsize(pdf_path)
                    print(f"PDF saved successfully using window.print: {pdf_path} ({file_size} bytes)")
                    return True
                else:
                    print(f"PDF file not created or is empty: {pdf_path}")
                    
            except Exception as e:
                print(f"JavaScript print method failed: {e}")
            
            return False
                
        except Exception as e:
            print(f"Print execution error: {e}")
            return False
        
    except TimeoutException:
        print(f"Timeout loading {url}")
        return False
    except WebDriverException as e:
        print(f"WebDriver error for {url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error for {url}: {e}")
        return False


def check_page_for_errors(driver: webdriver.Firefox) -> bool:
    """Check if the page contains error indicators like 'Page Not Found'."""
    try:
        # Get page title and body text
        page_title = driver.title.lower() if driver.title else ""
        
        # Get page body text (first 1000 characters to avoid huge text)
        body_text = driver.execute_script(
            "return document.body ? document.body.innerText.toLowerCase() : '';"
        )[:1000]
        
        # Check for common error indicators
        error_indicators = [
            "page not found",
            "404",
            "not found",
            "error",
            "page cannot be found",
            "the page you requested",
            "invalid url",
            "broken link",
            "page does not exist"
        ]
        
        # Check in title
        for indicator in error_indicators:
            if indicator in page_title:
                print(f"Error detected in title: '{indicator}' found")
                return True
        
        # Check in body text
        for indicator in error_indicators:
            if indicator in body_text:
                print(f"Error detected in content: '{indicator}' found")
                return True
        
        return False
        
    except Exception as e:
        print(f"Error checking page content: {e}")
        return False


def move_and_rename_mozilla_pdf(source_dir: str, target_dir: str, record_id: str, is_error_page: bool = False) -> bool:
    """Move and rename mozilla.pdf file based on record ID."""
    try:
        mozilla_pdf_path = os.path.join(source_dir, "mozilla.pdf")
        
        if not os.path.exists(mozilla_pdf_path):
            print(f"mozilla.pdf not found in {source_dir}")
            return False
        
        # Create target filename based on ID and error status
        if is_error_page:
            safe_filename = f"{record_id}_(error).pdf"
        else:
            safe_filename = f"{record_id}.pdf"
        
        target_path = os.path.join(target_dir, safe_filename)
        
        # Move and rename the file
        os.rename(mozilla_pdf_path, target_path)
        
        file_size = os.path.getsize(target_path)
        print(f"✓ Renamed and moved mozilla.pdf to: {safe_filename} ({file_size} bytes)")
        return True
        
    except Exception as e:
        print(f"Error moving/renaming mozilla.pdf: {e}")
        return False


def create_safe_filename(url: str, title: str, index: int) -> str:
    """Create a safe filename for PDF from URL and title."""
    # Extract domain from URL
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    
    # Clean title for filename (remove special characters)
    safe_title = re.sub(r'[^\w\s-]', '', title).strip()
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    
    # Limit length and add index
    if len(safe_title) > 50:
        safe_title = safe_title[:50]
    
    filename = f"{index:03d}_{domain}_{safe_title}.pdf"
    return filename


def alternative_pdf_save_method(driver: webdriver.Firefox, pdf_path: str) -> bool:
    """Alternative PDF save method using Firefox's built-in capabilities."""
    try:
        # Method 1: Use Selenium's print_page (if available in newer versions)
        try:
            # This is available in Selenium 4.0+
            pdf_data = driver.print_page()
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            print(f"PDF saved using Selenium print_page: {pdf_path}")
            return True
        except AttributeError:
            print("Selenium print_page method not available, trying alternative...")
        
        # Method 2: Execute CDP command for PDF (if supported)
        try:
            # Set print parameters
            print_options = {
                'landscape': False,
                'displayHeaderFooter': False,
                'printBackground': True,
                'scale': 1.0,
                'paperWidth': 8.27,
                'paperHeight': 11.7,
                'marginTop': 0.4,
                'marginBottom': 0.4,
                'marginLeft': 0.4,
                'marginRight': 0.4,
            }
            
            # This might work with newer Firefox versions
            result = driver.execute_cdp_cmd("Page.printToPDF", print_options)
            
            if 'data' in result:
                import base64
                pdf_data = base64.b64decode(result['data'])
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_data)
                print(f"PDF saved using CDP command: {pdf_path}")
                return True
                
        except Exception as e:
            print(f"CDP method failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"Alternative PDF save method failed: {e}")
        return False


def main():
    """Main function to automate browser operations for drugs.com links using Firefox."""
    # Default paths
    workspace_dir = Path(__file__).resolve().parent
    default_excel = workspace_dir / "aitep_references_need_fulltext_with_domain.xlsx"
    
    # Create PDF output directories
    pdf_output_dir = workspace_dir / "drugs_com_pdfs_mozilla_renamed"
    pdf_output_dir.mkdir(exist_ok=True)
    
    # Parse command line arguments
    headless = "--headless" in sys.argv
    
    # Filter out --headless from args to get the Excel file path
    args_without_headless = [arg for arg in sys.argv[1:] if arg != "--headless"]
    excel_path = args_without_headless[0] if args_without_headless else str(default_excel)
    
    max_links = 103  # Process up to 103 links
    
    print(f"Reading Excel file: {excel_path}")
    print(f"PDF output directory: {pdf_output_dir}")
    print(f"Headless mode: {headless}")
    
    # Get drugs.com links with IDs
    drugs_data = get_drugs_com_links_with_ids(excel_path)
    
    if not drugs_data:
        print("No www.drugs.com links found. Exiting.")
        return
    
    # Limit number of links to process
    if len(drugs_data) > max_links:
        print(f"Processing first {max_links} links out of {len(drugs_data)} total")
        drugs_data = drugs_data[:max_links]
    
    # Setup browser with workspace as download directory
    print("Setting up Firefox driver...")
    driver = setup_firefox_driver(headless=headless, download_dir=str(workspace_dir))
    
    successful_downloads = 0
    failed_downloads = 0
    
    try:
        for i, data in enumerate(drugs_data, 1):
            record_id = data['id']
            link = data['link']
            
            print(f"\nProcessing link {i}/{len(drugs_data)} (ID: {record_id})")
            
            # Navigate to the page and wait for load
            try:
                print(f"Opening: {link}")
                driver.get(link)
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(3)  # Additional wait for dynamic content
                
                page_title = driver.title or "Unknown_Title"
                print(f"Page title: {page_title}")
                
            except Exception as e:
                print(f"Error loading page: {e}")
                failed_downloads += 1
                continue
            
            # Check if page contains errors
            is_error_page = check_page_for_errors(driver)
            
            if is_error_page:
                print(f"⚠️  Error page detected for ID {record_id}")
            else:
                print(f"✓ Valid page detected for ID {record_id}")
            
            # Use Firefox's print to PDF functionality (this creates mozilla.pdf)
            try:
                # Use Ctrl+P to trigger print dialog, which should create mozilla.pdf
                driver.execute_script("window.print();")
                time.sleep(5)  # Wait for PDF generation
                
                # Check if mozilla.pdf was created and move/rename it
                success = move_and_rename_mozilla_pdf(
                    str(workspace_dir), 
                    str(pdf_output_dir), 
                    str(record_id),
                    is_error_page
                )
                
                if success:
                    successful_downloads += 1
                    if is_error_page:
                        print(f"✓ Successfully processed ID {record_id} (error page)")
                    else:
                        print(f"✓ Successfully processed ID {record_id}")
                else:
                    failed_downloads += 1
                    print(f"✗ Failed to process ID {record_id}")
                    
            except Exception as e:
                print(f"Error during PDF generation for ID {record_id}: {e}")
                failed_downloads += 1
            
            # Add delay between requests
            if i < len(drugs_data):
                print("Waiting 3 seconds before next request...")
                time.sleep(3)
    
    finally:
        print("\nClosing browser...")
        driver.quit()
        print(f"\nFirefox PDF Generation Summary:")
        print(f"✓ Successful downloads: {successful_downloads}")
        print(f"✗ Failed downloads: {failed_downloads}")
        print(f"📁 PDF files saved to: {pdf_output_dir}")
        print("Firefox automation completed.")


if __name__ == "__main__":
    main()