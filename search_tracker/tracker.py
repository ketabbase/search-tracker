from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import csv
from datetime import datetime
import time
import os
import signal
import sys
import shutil
import tempfile
import urllib.parse

class SearchTracker:
    def __init__(self, data_dir=None):
        self.driver = None
        # Create data directory and timestamped subdirectory
        self.start_time = datetime.now()
        if data_dir is None:
            self.data_dir = os.path.join('data', self.start_time.strftime('%Y-%m-%d_%H-%M-%S'))
        else:
            self.data_dir = os.path.join(data_dir, self.start_time.strftime('%Y-%m-%d_%H-%M-%S'))
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up file paths with the data directory
        self.csv_file = os.path.join(self.data_dir, 'queries.csv')
        self.tabs_file = os.path.join(self.data_dir, 'navigation_links.csv')
        self.new_tabs_file = os.path.join(self.data_dir, 'new_tabs.csv')
        self.scrolls_file = os.path.join(self.data_dir, 'scrolls.csv')
        self.url_durations_file = os.path.join(self.data_dir, 'url_durations.csv')
        
        # Setup all CSV files
        self.setup_csv()
        self.setup_tabs_csv()
        self.setup_new_tabs_csv()
        self.setup_scrolls_csv()
        self.setup_url_durations_csv()
        
        self.is_running = True
        self.original_window = None
        self.recorded_windows = set()
        self.window_data = {}
        self.last_recorded_url = None
        self.last_urls = {}
        self.last_saved_query = None
        self.last_scroll_position = {}
        self.url_start_times = {}
        
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        print(f"Data will be saved in: {self.data_dir}")

    def signal_handler(self, signum, frame):
        print("\nReceived interrupt signal. Saving data and cleaning up...")
        self.is_running = False

    def setup_csv(self):
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Text'])
    def setup_tabs_csv(self):
        if not os.path.exists(self.tabs_file):
            with open(self.tabs_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['open_timestamp', 'url', 'close_timestamp'])
    def setup_new_tabs_csv(self):
        if not os.path.exists(self.new_tabs_file):
            with open(self.new_tabs_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['open_timestamp', 'initial_url'])
    def setup_scrolls_csv(self):
        if not os.path.exists(self.scrolls_file):
            with open(self.scrolls_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['start_timestamp', 'end_timestamp', 'scroll_distance', 'url'])
    def setup_url_durations_csv(self):
        if not os.path.exists(self.url_durations_file):
            with open(self.url_durations_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'start_timestamp', 'end_timestamp', 'duration_seconds'])
    def extract_search_query_from_url(self, url):
        try:
            q_index = url.find('q=')
            if q_index == -1:
                return None
            start = q_index + 2
            sca_index = url.find('&sca', start)
            if sca_index == -1:
                return None
            encoded_query = url[start:sca_index]
            # Decode URL-encoded query to get readable text
            decoded_query = urllib.parse.unquote_plus(encoded_query)
            return decoded_query
        except Exception as e:
            print(f"Error extracting query from URL: {str(e)}")
            return None
    def save_search_query(self, query):
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    query
                ])
            print(f"Recorded search query: \"{query}\"")
        except Exception as e:
            print(f"Error saving search query: {str(e)}")
    def record_scroll(self, window_handle, current_url):
        try:
            current_position = self.driver.execute_script("return window.pageYOffset;")
            if window_handle in self.last_scroll_position:
                last_position = self.last_scroll_position[window_handle]
                if current_position != last_position:
                    scroll_distance = current_position - last_position
                    if abs(scroll_distance) > 10:
                        with open(self.scrolls_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                datetime.now().isoformat(),
                                datetime.now().isoformat(),
                                scroll_distance,
                                current_url
                            ])
            self.last_scroll_position[window_handle] = current_position
        except Exception as e:
            print(f"Error recording scroll: {str(e)}")
    def record_url_duration(self, url, window_handle):
        try:
            current_time = datetime.now()
            if url in self.url_start_times:
                start_time = self.url_start_times[url]
                duration = (current_time - start_time).total_seconds()
                if duration > 1:
                    with open(self.url_durations_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            url,
                            start_time.isoformat(),
                            current_time.isoformat(),
                            duration
                        ])
                    print(f"Recorded duration for {url}: {duration:.2f} seconds")
            self.url_start_times[url] = current_time
        except Exception as e:
            print(f"Error recording URL duration: {str(e)}")
            import traceback
            traceback.print_exc()
    def record_url_change(self, url, window_handle):
        try:
            if window_handle in self.last_urls and self.last_urls[window_handle]:
                previous_url = self.last_urls[window_handle]
                if previous_url in self.url_start_times:
                    current_time = datetime.now()
                    start_time = self.url_start_times[previous_url]
                    duration = (current_time - start_time).total_seconds()
                    if duration > 1:
                        with open(self.url_durations_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                previous_url,
                                start_time.isoformat(),
                                current_time.isoformat(),
                                duration
                            ])
                        print(f"Recorded duration for {previous_url}: {duration:.2f} seconds")
                    del self.url_start_times[previous_url]
                with open(self.tabs_file, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                for i, row in enumerate(rows):
                    if row[1] == previous_url and not row[2]:
                        rows[i][2] = datetime.now().isoformat()
                        print(f"URL closed: {previous_url}")
                        break
                with open(self.tabs_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
            with open(self.tabs_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    url,
                    ''
                ])
                print(f"New URL recorded: {url}")
            self.last_urls[window_handle] = url
            self.url_start_times[url] = datetime.now()
        except Exception as e:
            print(f"Error recording URL change: {str(e)}")
            import traceback
            traceback.print_exc()
    def check_new_windows(self):
        try:
            current_handles = set(self.driver.window_handles)
            user_active_handle = self.driver.current_window_handle
            new_handles = current_handles - self.recorded_windows
            closed_handles = self.recorded_windows - current_handles
            for handle in closed_handles:
                if handle in self.last_urls and self.last_urls[handle]:
                    with open(self.tabs_file, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                    for i, row in enumerate(rows):
                        if row[1] == self.last_urls[handle] and not row[2]:
                            rows[i][2] = datetime.now().isoformat()
                            break
                    with open(self.tabs_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerows(rows)
                    del self.last_urls[handle]
                    self.recorded_windows.remove(handle)
            if new_handles:
                for handle in new_handles:
                    self.driver.switch_to.window(handle)
                    new_tab_url = self.driver.current_url
                    self.record_new_tab_initial_url(new_tab_url)
                    self.recorded_windows.add(handle)
                if user_active_handle in current_handles:
                    self.driver.switch_to.window(user_active_handle)
        except Exception as e:
            print(f"Error checking new tabs: {str(e)}")
            import traceback
            traceback.print_exc()
    def record_new_tab_initial_url(self, url):
        try:
            with open(self.new_tabs_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    url
                ])
            print(f"New tab initial URL recorded in new_tabs.csv: {url}")
        except Exception as e:
            print(f"Error recording new tab initial URL: {str(e)}")
            import traceback
            traceback.print_exc()
    def start_browser(self):
        print("Attempting to start Chrome browser...")
        user_data_dir_old = os.path.join(os.getcwd(), 'chrome_profile')
        if os.path.exists(user_data_dir_old):
            try:
                shutil.rmtree(user_data_dir_old)
                print(f"Cleaned up old user data directory: {user_data_dir_old}")
            except Exception as e:
                print(f"Warning: Could not remove old user data directory {user_data_dir_old}: {e}")
                print("This might be due to insufficient disk space or active processes. Please check your disk space!")
        print("Attempting to terminate existing Chrome processes...")
        for _ in range(3):
            try:
                if os.name == 'nt':
                    os.system('taskkill /f /im chrome.exe /T 2>nul')
                    os.system('taskkill /f /im chromedriver.exe /T 2>nul')
                else:
                    os.system('pkill -f chrome')
                    os.system('pkill -f chromedriver')
                time.sleep(1)
            except Exception as e:
                print(f"Error during process termination attempt: {e}")
        time.sleep(3)
        print("Processes terminated. Proceeding to launch browser...")
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--remote-debugging-port=0')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            options.add_argument('--disable-site-isolation-trials')
            options.add_argument('--log-level=3')
            options.add_argument('--silent')
            self.temp_profile_dir = tempfile.mkdtemp()
            options.add_argument(f'--user-data-dir={self.temp_profile_dir}')
            from selenium.webdriver.chrome.service import Service
            service = Service(port=0)
            print("Initializing WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(60)
            print("WebDriver initialized. Navigating to Google...")
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver.get("https://www.google.com")
                    print(f"Successfully loaded Google (attempt {attempt + 1})")
                    break
                except Exception as e:
                    print(f"Error loading Google (attempt {attempt + 1}): {str(e)}")
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(5)
            self.original_window = self.driver.current_window_handle
            self.recorded_windows.add(self.original_window)
            self.record_url_change(self.driver.current_url, self.original_window)
            print("Browser started successfully.")
            return True
        except Exception as e:
            print(f"Fatal Error starting browser: {str(e)}")
            try:
                if hasattr(self, 'driver') and self.driver:
                    self.driver.quit()
            except:
                pass
            try:
                if os.name == 'nt':
                    os.system('taskkill /f /im chrome.exe /T 2>nul')
                    os.system('taskkill /f /im chromedriver.exe /T 2>nul')
                else:
                    os.system('pkill -f chrome')
                    os.system('pkill -f chromedriver')
            except:
                pass
            if hasattr(self, 'temp_profile_dir') and os.path.exists(self.temp_profile_dir):
                try:
                    shutil.rmtree(self.temp_profile_dir)
                    print(f"Cleaned up temporary profile directory: {self.temp_profile_dir}")
                except Exception as clean_e:
                    print(f"Error during cleanup of temp profile dir {self.temp_profile_dir}: {clean_e}")
            return False
    def cleanup(self):
        print("Saving final data and cleaning up resources...")
        try:
            current_time = datetime.now()
            for url, start_time in list(self.url_start_times.items()):
                duration = (current_time - start_time).total_seconds()
                if duration > 1:
                    with open(self.url_durations_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            url,
                            start_time.isoformat(),
                            current_time.isoformat(),
                            duration
                        ])
                    print(f"Recorded final duration for {url}: {duration:.2f} seconds")
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"Error during driver quit in cleanup: {str(e)}")
        finally:
            self.driver = None
            if hasattr(self, 'temp_profile_dir') and os.path.exists(self.temp_profile_dir):
                try:
                    shutil.rmtree(self.temp_profile_dir)
                    print(f"Cleaned up temporary profile directory: {self.temp_profile_dir}")
                except Exception as e:
                    print(f"Error cleaning up temporary profile directory {self.temp_profile_dir}: {str(e)}")
            try:
                if os.name == 'nt':
                    os.system('taskkill /f /im chrome.exe /T 2>nul')
                    os.system('taskkill /f /im chromedriver.exe /T 2>nul')
                else:
                    os.system('pkill -f chrome')
                    os.system('pkill -f chromedriver')
            except Exception as e:
                print(f"Error during final process cleanup: {str(e)}")
    def run(self):
        if not self.start_browser():
            print("Failed to start browser. Please check console for errors and disk space.")
            return
        print("\nBrowser is open. Navigate to Google search result pages.")
        print("Search queries will be extracted from URLs and recorded in queries.csv")
        print("New tabs opened/closed will be recorded in navigation_links.csv")
        print("Scroll events will be recorded in scrolls.csv")
        print("URL durations will be recorded in url_durations.csv")
        print("Press Ctrl+C to stop tracking and save data.")
        try:
            while self.is_running:
                time.sleep(1)
                self.check_new_windows()
                current_active_handle = self.driver.current_window_handle
                current_url = self.driver.current_url
                if current_active_handle in self.last_urls and self.last_urls[current_active_handle] != current_url:
                    self.record_url_change(current_url, current_active_handle)
                elif current_active_handle not in self.last_urls:
                    self.record_url_change(current_url, current_active_handle)
                self.record_scroll(current_active_handle, current_url)
                query = self.extract_search_query_from_url(current_url)
                if query and query != self.last_saved_query:
                    self.save_search_query(query)
                    self.last_saved_query = query
        except KeyboardInterrupt:
            print("\nStopping tracking...")
        except WebDriverException as e:
            print(f"\nBrowser connection lost: {str(e)}")
            print("Attempting graceful cleanup.")
        except Exception as e:
            print(f"\nAn unexpected error occurred: {str(e)}")
        finally:
            print("Final save and cleanup...")
            self.cleanup() 