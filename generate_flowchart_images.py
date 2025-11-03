"""
Script to generate flowchart images from the HTML file.
This script uses Playwright to render the HTML and take screenshots of each flowchart.
"""

import os
import sys

def generate_images_with_playwright():
    """Generate images using Playwright"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed.")
        print("Installing playwright...")
        os.system("pip install playwright")
        os.system("playwright install chromium")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Failed to install playwright. Please install manually:")
            print("  pip install playwright")
            print("  playwright install chromium")
            return False
    
    html_file = "flowcharts.html"
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found!")
        return False
    
    output_dir = "flowchart_images"
    os.makedirs(output_dir, exist_ok=True)
    
    flowchart_titles = [
        "Main Program Flow",
        "Browser Startup Flow",
        "Main Tracking Loop Detail",
        "Window Management Flow",
        "URL Change Tracking Flow",
        "Scroll Detection Flow",
        "Query Extraction Flow",
        "Cleanup Flow"
    ]
    
    print(f"Generating images from {html_file}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Load the HTML file
        file_path = os.path.abspath(html_file)
        # Convert Windows path to file:// URL format
        if sys.platform == "win32":
            file_url = file_path.replace('\\', '/')
            # Windows file:// URLs need three slashes: file:///C:/path
            page.goto(f"file:///{file_url}")
        else:
            page.goto(f"file://{file_path}")
        
        # Wait for Mermaid to render
        page.wait_for_timeout(3000)
        
        for i, title in enumerate(flowchart_titles, 1):
            try:
                # Find the flowchart container using XPath
                h2_xpath = f"//h2[contains(text(), '{title}')]"
                page.wait_for_selector(h2_xpath, timeout=5000)
                
                # Find the parent container (flowchart-container div)
                container_xpath = f"//h2[contains(text(), '{title}')]/ancestor::div[contains(@class, 'flowchart-container')]"
                container = page.locator(container_xpath)
                
                # Take screenshot of the container
                output_file = os.path.join(output_dir, f"{i:02d}_{title.lower().replace(' ', '_')}.png")
                container.screenshot(path=output_file)
                print(f"  ✓ Generated: {output_file}")
                
            except Exception as e:
                print(f"  ✗ Failed to generate image for '{title}': {str(e)}")
                import traceback
                traceback.print_exc()
        
        browser.close()
    
    print(f"\nAll images saved to '{output_dir}/' directory")
    return True

def generate_images_with_selenium():
    """Generate images using Selenium (alternative method)"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        print("Selenium is not installed. Please install it:")
        print("  pip install selenium")
        return False
    
    html_file = "flowcharts.html"
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found!")
        return False
    
    output_dir = "flowchart_images"
    os.makedirs(output_dir, exist_ok=True)
    
    flowchart_titles = [
        "Main Program Flow",
        "Browser Startup Flow",
        "Main Tracking Loop Detail",
        "Window Management Flow",
        "URL Change Tracking Flow",
        "Scroll Detection Flow",
        "Query Extraction Flow",
        "Cleanup Flow"
    ]
    
    print(f"Generating images from {html_file} using Selenium...")
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        file_path = os.path.abspath(html_file).replace('\\', '/')
        driver.get(f"file:///{file_path}")
        
        # Wait for Mermaid to render
        import time
        time.sleep(3)
        
        for i, title in enumerate(flowchart_titles, 1):
            try:
                # Find the flowchart container by h2 text
                h2_element = driver.find_element(By.XPATH, f"//h2[contains(text(), '{title}')]")
                container = h2_element.find_element(By.XPATH, "./..")
                
                # Take screenshot
                output_file = os.path.join(output_dir, f"{i:02d}_{title.lower().replace(' ', '_')}.png")
                container.screenshot(output_file)
                print(f"  ✓ Generated: {output_file}")
                
            except Exception as e:
                print(f"  ✗ Failed to generate image for '{title}': {str(e)}")
        
        driver.quit()
        print(f"\nAll images saved to '{output_dir}/' directory")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("SearchTracker Flowchart Image Generator")
    print("=" * 50)
    print("\nChoose method:")
    print("1. Playwright (recommended)")
    print("2. Selenium (alternative)")
    print("3. Just open HTML in browser (manual)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        success = generate_images_with_playwright()
    elif choice == "2":
        success = generate_images_with_selenium()
    elif choice == "3":
        html_file = os.path.abspath("flowcharts.html")
        if sys.platform == "win32":
            os.startfile(html_file)
        elif sys.platform == "darwin":
            os.system(f"open {html_file}")
        else:
            os.system(f"xdg-open {html_file}")
        print(f"\nOpened {html_file} in your default browser.")
        print("You can take screenshots manually or use browser's Print to PDF feature.")
        success = True
    else:
        print("Invalid choice!")
        success = False
    
    if not success:
        print("\nAlternative: Open flowcharts.html in your browser and take screenshots manually.")
        sys.exit(1)

