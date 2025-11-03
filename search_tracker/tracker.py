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
        self.scroll_metrics_file = os.path.join(self.data_dir, 'scroll_metrics.csv')
        self.url_durations_file = os.path.join(self.data_dir, 'url_durations.csv')
        self.dwell_summary_file = os.path.join(self.data_dir, 'dwell_summary.csv')
        self.scroll_summary_file = os.path.join(self.data_dir, 'scroll_summary.csv')
        self.query_summary_file = os.path.join(self.data_dir, 'query_summary.csv')
        self.graph_summary_file = os.path.join(self.data_dir, 'graph_summary.csv')
        self.edges_file = os.path.join(self.data_dir, 'edges.csv')
        self.domain_edges_file = os.path.join(self.data_dir, 'domain_edges.csv')
        
        # Setup all CSV files
        self.setup_csv()
        self.setup_tabs_csv()
        self.setup_new_tabs_csv()
        self.setup_scrolls_csv()
        self.setup_scroll_metrics_csv()
        self.setup_url_durations_csv()
        self.setup_dwell_summary_csv()
        self.setup_scroll_summary_csv()
        self.setup_query_summary_csv()
        self.setup_graph_summary_csv()
        
        self.is_running = True
        self.original_window = None
        self.recorded_windows = set()
        self.window_data = {}
        self.last_recorded_url = None
        self.last_urls = {}
        self.last_saved_query = None
        self.last_scroll_position = {}
        self.last_scroll_time = {}
        self.max_scroll_position = {}
        self.min_scroll_position = {}
        self.scroll_agg = {}  # per-window aggregates: {window: {sum_abs_dy, sum_dt, max_abs_sv}}
        self.url_start_times = {}
        self.dwell_durations = []  # list of per-visit dwell durations (seconds)
        # Query tracking for session-level metrics
        self._queries_list = []
        self._queries_set = set()
        self._first_query_time = None
        self._last_query_time = None
        # Graph tracking: URLs (V), domains, and transitions (E)
        self._visited_urls = set()
        self._visited_domains = set()
        self._edges = []  # list of (from_url, to_url, timestamp)
        self._domain_edges = []  # list of (from_domain, to_domain, timestamp)
        
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
    def setup_scroll_metrics_csv(self):
        if not os.path.exists(self.scroll_metrics_file):
            with open(self.scroll_metrics_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'url',
                    'y_px',
                    'dy_px',
                    'dt_s',
                    'sv_px_per_s',
                    's_max_px',
                    's_min_px',
                    'page_h_px',
                    'S_norm'  # (s_max - s_min)/H in [0,1]
                ])
    def setup_scroll_summary_csv(self):
        if not os.path.exists(self.scroll_summary_file):
            with open(self.scroll_summary_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'url',
                    'start_timestamp',
                    'end_timestamp',
                    'S_norm',
                    'avg_abs_sv_px_per_s',
                    'max_abs_sv_px_per_s'
                ])
    def setup_url_durations_csv(self):
        if not os.path.exists(self.url_durations_file):
            with open(self.url_durations_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['url', 'start_timestamp', 'end_timestamp', 'duration_seconds'])
    def setup_dwell_summary_csv(self):
        if not os.path.exists(self.dwell_summary_file):
            with open(self.dwell_summary_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['session_start', 'N', 'avg_dwell_seconds', 'total_dwell_seconds'])
    def setup_query_summary_csv(self):
        if not os.path.exists(self.query_summary_file):
            with open(self.query_summary_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'session_start',
                    'Q_d',                # total queries count |Q|
                    'Q_new',              # number of distinct queries
                    'T_s_seconds',        # total search time
                    'R_q'                 # reformulation rate Q_new / T_s
                ])
    def setup_graph_summary_csv(self):
        if not os.path.exists(self.graph_summary_file):
            with open(self.graph_summary_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'session_start',
                    'V',                  # number of unique URLs
                    'E',                  # number of transitions
                    'B',                  # breadth = unique domains
                    'L',                  # depth = |E| / B
                    'domain_E',           # number of domain transitions
                    'domain_B',           # same as B (unique domains)
                    'domain_L'            # |domain_E| / domain_B
                ])
        if not os.path.exists(self.edges_file):
            with open(self.edges_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'from_url', 'to_url'])
        if not os.path.exists(self.domain_edges_file):
            with open(self.domain_edges_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'from_domain', 'to_domain'])
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
            now = datetime.now()
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    now.isoformat(),
                    query
                ])
            print(f"Recorded search query: \"{query}\"")
            # Maintain session-level query metrics
            norm_q = (query or '').strip().lower()
            self._queries_list.append(norm_q)
            if norm_q:
                self._queries_set.add(norm_q)
            if self._first_query_time is None:
                self._first_query_time = now
            self._last_query_time = now
        except Exception as e:
            print(f"Error saving search query: {str(e)}")
    def record_scroll(self, window_handle, current_url):
        try:
            # Get current scroll position and page height from the page
            js = (
                "return {"
                "  y: Math.max(window.pageYOffset || 0, document.documentElement.scrollTop || 0, document.body.scrollTop || 0),"
                "  H: Math.max(document.body.scrollHeight || 0, document.body.offsetHeight || 0, document.documentElement.clientHeight || 0, document.documentElement.scrollHeight || 0, document.documentElement.offsetHeight || 0)"
                "};"
            )
            page_state = self.driver.execute_script(js)
            current_position = int(page_state.get('y', 0) or 0)
            page_height = int(page_state.get('H', 0) or 0)

            last_position = self.last_scroll_position.get(window_handle, current_position)
            last_time = self.last_scroll_time.get(window_handle, time.monotonic())
            dy = current_position - last_position
            dt = max(0.0, time.monotonic() - last_time)
            sv = (dy / dt) if dt > 0 else 0.0

            # Update max scroll position per window
            prev_max = self.max_scroll_position.get(window_handle, 0)
            s_max = max(prev_max, current_position)
            # Update min scroll position per window
            prev_min = self.min_scroll_position.get(window_handle, current_position)
            s_min = min(prev_min, current_position)
            # S = (s_max - s_min)/H in [0,1]
            S_norm = ((float(s_max) - float(s_min)) / float(page_height)) if page_height > 0 else 0.0
            S_norm = max(0.0, min(1.0, S_norm))

            # Aggregate velocity stats per window
            agg = self.scroll_agg.get(window_handle, {'sum_abs_dy': 0.0, 'sum_dt': 0.0, 'max_abs_sv': 0.0})
            agg['sum_abs_dy'] += abs(dy)
            agg['sum_dt'] += dt
            agg['max_abs_sv'] = max(agg['max_abs_sv'], abs(sv))
            self.scroll_agg[window_handle] = agg

            # Record fine-grained movement (threshold to reduce noise)
            if abs(dy) > 10:
                with open(self.scrolls_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        dy,
                        current_url
                    ])
                # Also record metrics snapshot
                with open(self.scroll_metrics_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        current_url,
                        current_position,
                        dy,
                        f"{dt:.4f}",
                        f"{sv:.2f}",
                        s_max,
                        s_min,
                        page_height,
                        f"{S_norm:.4f}"
                    ])

            # Persist window-scoped state
            self.last_scroll_position[window_handle] = current_position
            self.last_scroll_time[window_handle] = time.monotonic()
            self.max_scroll_position[window_handle] = s_max
            self.min_scroll_position[window_handle] = s_min
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
                    self.dwell_durations.append(duration)
            self.url_start_times[url] = current_time
        except Exception as e:
            print(f"Error recording URL duration: {str(e)}")
            import traceback
            traceback.print_exc()
    def record_url_change(self, url, window_handle):
        try:
            if window_handle in self.last_urls and self.last_urls[window_handle]:
                previous_url = self.last_urls[window_handle]
                # Graph: add transition edge previous_url -> url
                try:
                    now = datetime.now()
                    with open(self.edges_file, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            now.isoformat(),
                            previous_url,
                            url
                        ])
                    self._edges.append((previous_url, url, now))
                    # Also write domain-level edge
                    try:
                        from urllib.parse import urlparse
                        p_from = urlparse(previous_url)
                        p_to = urlparse(url)
                        d_from = (p_from.netloc or '').lower()
                        d_to = (p_to.netloc or '').lower()
                        if d_from and d_to:
                            with open(self.domain_edges_file, 'a', newline='', encoding='utf-8') as df:
                                dwriter = csv.writer(df)
                                dwriter.writerow([now.isoformat(), d_from, d_to])
                            self._domain_edges.append((d_from, d_to, now))
                    except Exception:
                        pass
                except Exception:
                    pass
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
                        self.dwell_durations.append(duration)
                    del self.url_start_times[previous_url]
                # Write scroll summary for the previous URL if available
                try:
                    agg = self.scroll_agg.get(window_handle, None)
                    if agg is not None:
                        s_max = self.max_scroll_position.get(window_handle, 0)
                        s_min = self.min_scroll_position.get(window_handle, 0)
                        page_h = 0
                        try:
                            page_h = int(self.driver.execute_script("return Math.max(document.body.scrollHeight || 0, document.body.offsetHeight || 0, document.documentElement.clientHeight || 0, document.documentElement.scrollHeight || 0, document.documentElement.offsetHeight || 0);") or 0)
                        except Exception:
                            page_h = 0
                        S_norm = ((float(s_max) - float(s_min)) / float(page_h)) if page_h > 0 else 0.0
                        S_norm = max(0.0, min(1.0, S_norm))
                        avg_abs_sv = (agg['sum_abs_dy'] / agg['sum_dt']) if agg['sum_dt'] > 0 else 0.0
                        with open(self.scroll_summary_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                previous_url,
                                self.url_start_times.get(previous_url, datetime.now()).isoformat() if previous_url in self.url_start_times else '',
                                datetime.now().isoformat(),
                                f"{S_norm:.4f}",
                                f"{avg_abs_sv:.2f}",
                                f"{agg['max_abs_sv']:.2f}"
                            ])
                    # Reset per-window scroll state for next URL
                    self.scroll_agg[window_handle] = {'sum_abs_dy': 0.0, 'sum_dt': 0.0, 'max_abs_sv': 0.0}
                    self.max_scroll_position[window_handle] = 0
                    self.min_scroll_position[window_handle] = self.last_scroll_position.get(window_handle, 0)
                except Exception as _:
                    pass
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
            # Track visited URL and domain
            try:
                self._visited_urls.add(url)
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.netloc:
                    self._visited_domains.add(parsed.netloc.lower())
            except Exception:
                pass
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
            # Capture parent URL before switching
            try:
                parent_url = self.driver.current_url
            except Exception:
                parent_url = None
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
                    self.record_new_tab_initial_url(new_tab_url, parent_url)
                    self.recorded_windows.add(handle)
                if user_active_handle in current_handles:
                    self.driver.switch_to.window(user_active_handle)
        except Exception as e:
            print(f"Error checking new tabs: {str(e)}")
            import traceback
            traceback.print_exc()
    def record_new_tab_initial_url(self, url, parent_url=None):
        try:
            with open(self.new_tabs_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    url
                ])
            print(f"New tab initial URL recorded in new_tabs.csv: {url}")
            # Graph: edge from parent to new tab URL (if parent known)
            if parent_url:
                try:
                    now = datetime.now()
                    with open(self.edges_file, 'a', newline='', encoding='utf-8') as ef:
                        ewriter = csv.writer(ef)
                        ewriter.writerow([now.isoformat(), parent_url, url])
                    self._edges.append((parent_url, url, now))
                    # Domain-level edge
                    try:
                        from urllib.parse import urlparse
                        p_from = urlparse(parent_url)
                        p_to = urlparse(url)
                        d_from = (p_from.netloc or '').lower()
                        d_to = (p_to.netloc or '').lower()
                        if d_from and d_to:
                            with open(self.domain_edges_file, 'a', newline='', encoding='utf-8') as df:
                                dwriter = csv.writer(df)
                                dwriter.writerow([now.isoformat(), d_from, d_to])
                            self._domain_edges.append((d_from, d_to, now))
                    except Exception:
                        pass
                except Exception:
                    pass
            # Track visited URL and domain
            try:
                self._visited_urls.add(url)
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.netloc:
                    self._visited_domains.add(parsed.netloc.lower())
            except Exception:
                pass
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
            self.driver.set_page_load_timeout(60)
            self.driver.set_script_timeout(90)
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
                    self.dwell_durations.append(duration)
            # Flush a final scroll summary for the active window/URL if possible
            try:
                active_handle = None
                try:
                    active_handle = self.driver.current_window_handle if self.driver else None
                except Exception:
                    active_handle = None
                if active_handle and active_handle in self.last_urls:
                    url = self.last_urls[active_handle]
                    agg = self.scroll_agg.get(active_handle, None)
                    if agg is not None:
                        s_max = self.max_scroll_position.get(active_handle, 0)
                        s_min = self.min_scroll_position.get(active_handle, 0)
                        page_h = 0
                        try:
                            page_h = int(self.driver.execute_script("return Math.max(document.body.scrollHeight || 0, document.body.offsetHeight || 0, document.documentElement.clientHeight || 0, document.documentElement.scrollHeight || 0, document.documentElement.offsetHeight || 0);") or 0)
                        except Exception:
                            page_h = 0
                        S_norm = ((float(s_max) - float(s_min)) / float(page_h)) if page_h > 0 else 0.0
                        S_norm = max(0.0, min(1.0, S_norm))
                        avg_abs_sv = (agg['sum_abs_dy'] / agg['sum_dt']) if agg['sum_dt'] > 0 else 0.0
                        with open(self.scroll_summary_file, 'a', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                url,
                                self.url_start_times.get(url, self.start_time).isoformat(),
                                current_time.isoformat(),
                                f"{S_norm:.4f}",
                                f"{avg_abs_sv:.2f}",
                                f"{agg['max_abs_sv']:.2f}"
                            ])
            except Exception as _:
                pass
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"Error during driver quit in cleanup: {str(e)}")
        finally:
            # Write session dwell summary D̄ = mean(D_i)
            try:
                N = len(self.dwell_durations)
                total_dwell = sum(self.dwell_durations) if N > 0 else 0.0
                avg_dwell = (total_dwell / N) if N > 0 else 0.0
                with open(self.dwell_summary_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        self.start_time.isoformat(),
                        N,
                        f"{avg_dwell:.2f}",
                        f"{total_dwell:.2f}"
                    ])
                print(f"Session dwell summary saved: N={N}, avg={avg_dwell:.2f}s")
            except Exception as e:
                print(f"Error writing dwell summary: {str(e)}")
            # Write session query summary: Q_d, Q_new, T_s, R_q
            try:
                Q_d = len(self._queries_list)
                Q_new = len(self._queries_set)
                if self._first_query_time and self._last_query_time:
                    T_s = (self._last_query_time - self._first_query_time).total_seconds()
                else:
                    T_s = 0.0
                R_q = (Q_new / T_s) if T_s > 0 else 0.0
                with open(self.query_summary_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        self.start_time.isoformat(),
                        Q_d,
                        Q_new,
                        f"{T_s:.2f}",
                        f"{R_q:.6f}"
                    ])
                print(f"Session query summary saved: Q_d={Q_d}, Q_new={Q_new}, T_s={T_s:.2f}s, R_q={R_q:.6f}")
            except Exception as e:
                print(f"Error writing query summary: {str(e)}")
            # Write session graph summary: URL-level and domain-level breadth/depth
            try:
                V = len(self._visited_urls)
                E = len(self._edges)
                B = len(self._visited_domains)
                L = (E / B) if B > 0 else 0.0
                domain_E = len(self._domain_edges)
                domain_B = B
                domain_L = (domain_E / domain_B) if domain_B > 0 else 0.0
                with open(self.graph_summary_file, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        self.start_time.isoformat(),
                        V,
                        E,
                        B,
                        f"{L:.4f}",
                        domain_E,
                        domain_B,
                        f"{domain_L:.4f}"
                    ])
                print(f"Session graph summary saved: V={V}, E={E}, B={B}, L={L:.4f}, domain_E={domain_E}, domain_L={domain_L:.4f}")
            except Exception as e:
                print(f"Error writing graph summary: {str(e)}")
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
        consecutive_errors = 0
        max_consecutive_errors = 3
        try:
            while self.is_running:
                try:
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
                    consecutive_errors = 0
                except WebDriverException as e:
                    consecutive_errors += 1
                    print(f"WebDriver error (attempt {consecutive_errors}/{max_consecutive_errors}): {str(e)}")
                    # Lightweight recovery: try to navigate to a safe page
                    try:
                        self.driver.get("https://www.google.com")
                        time.sleep(2)
                    except Exception:
                        pass
                    if consecutive_errors >= max_consecutive_errors:
                        print("Too many consecutive WebDriver errors; stopping.")
                        break
                except Exception as e:
                    consecutive_errors += 1
                    print(f"Loop error (attempt {consecutive_errors}/{max_consecutive_errors}): {str(e)}")
                    if consecutive_errors >= max_consecutive_errors:
                        print("Too many consecutive errors; stopping.")
                        break
        except KeyboardInterrupt:
            print("\nStopping tracking...")
        except Exception as e:
            print(f"\nFatal unexpected error: {str(e)}")
        finally:
            print("Final save and cleanup...")
            self.cleanup() 