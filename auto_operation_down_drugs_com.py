import sys
import time
import json
import base64
from pathlib import Path
from typing import List, Optional

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


def setup_chrome_driver(headless: bool = False) -> webdriver.Chrome:
    """Setup Chrome driver with appropriate options."""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument("--headless=new")
    
    # Additional options for better compatibility
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Please make sure ChromeDriver is installed and in PATH")
        sys.exit(1)


def get_drugs_com_links(excel_path: str) -> List[str]:
    """Read Excel file and extract www.drugs.com links."""
    try:
        df = pd.read_excel(excel_path)
        
        if 'domain' not in df.columns or 'link' not in df.columns:
            raise KeyError("Required columns 'domain' and 'link' not found in Excel file")
        
        # Filter for www.drugs.com domain
        drugs_links = df[df['domain'] == 'www.drugs.com']['link'].tolist()
        
        print(f"Found {len(drugs_links)} www.drugs.com links")
        return drugs_links
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []


def save_page_as_pdf(driver: webdriver.Chrome, url: str, pdf_path: str, timeout: int = 10) -> bool:
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
        
        # Scroll to trigger lazy-loaded content
        try:
            last_height = 0
            while True:
                height = driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
                if height <= last_height:
                    break
                step = 800
                y = last_height
                while y < height:
                    driver.execute_script("window.scrollTo(0, arguments[0]);", y)
                    time.sleep(0.2)
                    y += step
                last_height = height
                time.sleep(0.5)
            driver.execute_script("window.scrollTo(0, 0)")
        except Exception:
            pass
        
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


def create_safe_filename(url: str, title: str, index: int) -> str:
    """Create a safe filename for PDF from URL and title."""
    # Extract domain from URL for folder organization
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')
    
    # Clean title for filename (remove special characters)
    import re
    safe_title = re.sub(r'[^\w\s-]', '', title).strip()
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    
    # Limit length and add index
    if len(safe_title) > 50:
        safe_title = safe_title[:50]
    
    filename = f"{index:03d}_{domain}_{safe_title}.pdf"
    return filename


def main():
    """Main function to automate browser operations for drugs.com links."""
    # Default paths
    workspace_dir = Path(__file__).resolve().parent
    default_excel = workspace_dir / "aitep_references_need_fulltext_with_domain.xlsx"
    
    # Create PDF output directory
    pdf_output_dir = workspace_dir / "drugs_com_pdfs"
    pdf_output_dir.mkdir(exist_ok=True)
    
    # Parse command line arguments
    excel_path = sys.argv[1] if len(sys.argv) > 1 else str(default_excel)
    headless = "--headless" in sys.argv
    max_links = 10  # Increase limit since we're saving PDFs
    
    print(f"Reading Excel file: {excel_path}")
    print(f"PDF output directory: {pdf_output_dir}")
    print(f"Headless mode: {headless}")
    
    # Get drugs.com links
    drugs_links = get_drugs_com_links(excel_path)
    
    if not drugs_links:
        print("No www.drugs.com links found. Exiting.")
        return
    
    # Limit number of links to process
    if len(drugs_links) > max_links:
        print(f"Processing first {max_links} links out of {len(drugs_links)} total")
        drugs_links = drugs_links[:max_links]
    
    # Setup browser
    print("Setting up Chrome driver...")
    driver = setup_chrome_driver(headless=headless)
    
    successful_downloads = 0
    failed_downloads = 0
    
    try:
        for i, link in enumerate(drugs_links, 1):
            print(f"\nProcessing link {i}/{len(drugs_links)}")
            
            # First load the page to get title
            try:
                driver.get(link)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                page_title = driver.title or "Unknown_Title"
            except:
                page_title = "Unknown_Title"
            
            # Create safe filename
            filename = create_safe_filename(link, page_title, i)
            pdf_path = pdf_output_dir / filename
            
            # Save page as PDF
            if save_page_as_pdf(driver, link, str(pdf_path)):
                successful_downloads += 1
                print(f"✓ Successfully saved: {filename}")
            else:
                failed_downloads += 1
                print(f"✗ Failed to save: {filename}")
            
            # Add delay between requests to be respectful
            if i < len(drugs_links):
                print("Waiting 3 seconds before next request...")
                time.sleep(3)
    
    finally:
        print("\nClosing browser...")
        driver.quit()
        print(f"\nPDF Generation Summary:")
        print(f"✓ Successful downloads: {successful_downloads}")
        print(f"✗ Failed downloads: {failed_downloads}")
        print(f"📁 PDF files saved to: {pdf_output_dir}")
        print("Browser automation completed.")


if __name__ == "__main__":
    main()
