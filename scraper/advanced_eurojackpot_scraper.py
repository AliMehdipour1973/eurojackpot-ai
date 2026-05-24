#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced EuroJackpot Data Scraper
اسکریپت پیشرفته برای استخراج داده‌های یوروجکپات با پشتیبانی کامل از فیلتر شکن
"""

import requests
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import json
import time
import logging
import random
import os
import sys
import subprocess
import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
from typing import Optional, Dict, List, Tuple, Any
from urllib.parse import urljoin, urlparse
import re
import tkinter as tk
from tkinter import simpledialog
import getpass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

class AdvancedEuroJackpotScraper:
    def __init__(self, config_path: str = "configs/proxy_config.json"):
        """
        Initialize the advanced EuroJackpot scraper
        
        Args:
            config_path: Path to configuration file
        """
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(str(env_path))
        else:
            load_dotenv()
        self.config = self.load_config(config_path)
        self.session = requests.Session()
        self.setup_logging()
        self.setup_session()
        self.init_database()
        
        # Target URLs for different sources
        self.target_urls = {
            'westlotto': 'https://www.westlotto.de/en/information/numbers-and-figures/eurojackpot',
            'eurojackpot_org': 'https://www.eurojackpot.org/en/results/',
            'lotto_de': 'https://www.lotto.de/en/lotteries/eurojackpot/numbers'
        }
        
        # Psiphon3 executable path
        self.psiphon_path = "psiphon3.exe"

    def _prompt_password(self) -> str:
        """Get DB password from env or prompt the user with a GUI dialog."""
        env_pwd = os.getenv("DB_PASSWORD")
        if env_pwd:
            return env_pwd

        try:
            root = tk.Tk()
            root.withdraw()
            password = simpledialog.askstring("Database Login", "Enter database password:", show='*')
            root.destroy()
            if password:
                return password
        except Exception as exc:
            self.logger.warning(f"GUI password prompt failed, falling back to console input: {exc}")

        # Fallback to console prompt (no echo)
        return getpass.getpass("Enter database password: ")

    def _get_db_connection_params(self, dbname: Optional[str]) -> Dict[str, Any]:
        """Get host, port, user, password, dbname. Env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD) overrides config so Neon/cloud works via .env only."""
        name = (dbname or os.getenv("DB_NAME") or "eurojackpot_ai").strip() or "eurojackpot_ai"
        host = os.getenv("DB_HOST")
        port_str = os.getenv("DB_PORT")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        from_env = host is not None and host.strip() != ""
        if from_env:
            host = host.strip()
            port = int(port_str) if port_str and str(port_str).strip() else 5432
            user = (user or "postgres").strip()
            password = password or self._prompt_password()
            return {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "dbname": name,
            }
        config_path = None
        if name == "eurojackpot_ai":
            config_path = PROJECT_ROOT / "configs" / "derived_tables_config.standardized.json"
        elif name == "backtest_ai":
            config_path = PROJECT_ROOT / "configs" / "backtesting_ai_config.metadata.json"
        if config_path and config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                db = cfg.get("database", cfg)
                if isinstance(db, dict) and db.get("name"):
                    password_env = db.get("password_env", "DB_PASSWORD")
                    password = os.getenv(password_env) or self._prompt_password()
                    host = os.getenv("DB_HOST") or db.get("host", "localhost")
                    port_str = os.getenv("DB_PORT")
                    port = int(port_str) if (port_str and str(port_str).strip()) else int(db.get("port", 5432))
                    user = os.getenv("DB_USER") or db.get("user", "postgres")
                    return {
                        "host": host.strip() if isinstance(host, str) else host,
                        "port": port,
                        "user": user.strip() if isinstance(user, str) else user,
                        "password": password,
                        "dbname": db.get("name", name),
                    }
            except Exception:
                pass
        password = self._prompt_password()
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "postgres"),
            "password": password,
            "dbname": name,
        }

    def _connect_with_params(
        self,
        host: str,
        port: int,
        dbname_final: str,
        user: str,
        password: str,
        use_ssl: bool,
    ):
        """Try to connect with given params; return connection or None on failure."""
        try:
            if use_ssl:
                return psycopg2.connect(
                    host=host, port=port, dbname=dbname_final, user=user,
                    sslmode="require",
                )
            return psycopg2.connect(
                host=host, port=port, dbname=dbname_final, user=user, password=password
            )
        except (psycopg2.OperationalError, psycopg2.Error):
            return None

    def _open_connection(self, dbname: Optional[str] = None):
        """Open a PostgreSQL connection using DATABASE_URL from environment."""
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return psycopg2.connect(db_url)
        params = self._get_db_connection_params(dbname)
        host = params["host"]
        port = params["port"]
        user = params["user"]
        password = params["password"]
        dbname_final = params["dbname"]
        self.logger.info(
            "Connecting to database %s at %s:%s",
            dbname_final, host, port,
        )
        use_ssl = os.getenv("DB_SSLMODE") == "require" or (host and "neon.tech" in host)
        if use_ssl and password:
            os.environ["PGPASSWORD"] = password
        try:
            conn = self._connect_with_params(host, port, dbname_final, user, password, use_ssl)
            if conn is not None:
                return conn
            if (
                (host in ("localhost", "127.0.0.1", "::1") or host is None)
                and port == 5432
                and not use_ssl
            ):
                self.logger.info("Retrying database connection on port 5433 (common for PostgreSQL on Windows).")
                conn = self._connect_with_params(host, 5433, dbname_final, user, password, use_ssl)
                if conn is not None:
                    return conn
            raise psycopg2.OperationalError("Database connection failed (tried port %s and 5433)." % port)
        finally:
            os.environ.pop("PGPASSWORD", None)
            params["password"] = ""
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file. Relative paths are resolved from project root."""
        if not os.path.isabs(config_path):
            config_path = str(PROJECT_ROOT / config_path)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Use basic logging since logger not initialized yet
            logging.warning(f"Config file not found: {config_path}, using defaults")
            return self.get_default_config()
        except Exception as e:
            # Use basic logging since logger not initialized yet
            logging.error(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "proxy_settings": {
                "enabled": False,
                "proxy_type": "http",
                "proxy_host": "127.0.0.1",
                "proxy_port": 8080
            },
            "scraping_settings": {
                "request_delay": {"min": 1, "max": 3},
                "max_retries": 3
            },
            "database_settings": {
                "path": "database/eurojackpot.db"
            }
        }
    
    def setup_logging(self):
        """Setup logging configuration. Log file is under project root."""
        log_config = self.config.get('logging_settings', {})
        log_file = log_config.get('log_file', 'logs/eurojackpot_scraper.log')
        if not os.path.isabs(log_file):
            log_file = str(PROJECT_ROOT / log_file)
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=getattr(logging, log_config.get('level', 'INFO')),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_session(self):
        """Setup requests session with proxy if enabled"""
        proxy_config = self.config.get('proxy_settings', {})
        
        if proxy_config.get('enabled', False):
            proxy_type = proxy_config.get('proxy_type', 'http')
            proxy_host = proxy_config.get('proxy_host', '127.0.0.1')
            proxy_port = proxy_config.get('proxy_port', 8080)
            proxy_username = proxy_config.get('proxy_username', '')
            proxy_password = proxy_config.get('proxy_password', '')
            
            # Build proxy URL
            if proxy_username and proxy_password:
                proxy_url = f"{proxy_type}://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
            else:
                proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
            
            self.session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            self.logger.info(f"Proxy configured: {proxy_type}://{proxy_host}:{proxy_port}")
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def init_database(self):
        """Verify core.draws and core.draw_details exist on Neon."""
        conn = self._open_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'core'
                      AND table_name IN ('draws', 'draw_details')
                """)
                found = {row[0] for row in cursor.fetchall()}
                missing = {'draws', 'draw_details'} - found
                if missing:
                    raise RuntimeError(
                        f"Required tables missing in core schema: {missing}. "
                        f"Run SQL schema files first."
                    )
            self.logger.info("Database verified: core.draws and core.draw_details ready.")
        finally:
            conn.close()
    
    def test_connection(self) -> bool:
        """Test database connection and verify schema is ready."""
        try:
            conn = self._open_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            (SELECT COUNT(*) FROM core.draws) AS draws_count,
                            (SELECT COUNT(*) FROM core.draw_details) AS details_count
                    """)
                    row = cursor.fetchone()
                    self.logger.info(
                        "Connection OK — core.draws: %d rows, core.draw_details: %d rows",
                        row[0], row[1]
                    )
                    return True
            finally:
                conn.close()
        except Exception as e:
            self.logger.error("Connection test failed: %s", e)
            return False
    
    def start_psiphon3(self) -> bool:
        """Start Psiphon3 VPN and wait for connection"""
        try:
            self.logger.info("Starting Psiphon3 VPN...")
            
            # Check if psiphon3.exe exists
            if not os.path.exists(self.psiphon_path):
                self.logger.error(f"Psiphon3 executable not found at: {self.psiphon_path}")
                return False
            
            # Start Psiphon3 in background
            self.logger.info(f"Launching {self.psiphon_path}...")
            process = subprocess.Popen(
                [self.psiphon_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Store process reference for cleanup
            self.psiphon_process = process
            
            self.logger.info("Psiphon3 started successfully")
            self.logger.info("Waiting 30 seconds for VPN connection to establish...")
            
            # Wait 30 seconds for VPN to establish connection
            time.sleep(30)
            
            # Test VPN connection
            if self.test_vpn_connection():
                self.logger.info("VPN connection established successfully!")
                return True
            else:
                self.logger.warning("VPN connection test failed, but continuing...")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"Failed to start Psiphon3: {e}")
            return False
    
    def test_vpn_connection(self) -> bool:
        """Test if VPN connection is working"""
        try:
            # Test with a simple request
            test_url = "https://httpbin.org/ip"
            response = self.make_request(test_url, timeout=10)
            
            if response and response.status_code == 200:
                self.logger.info("VPN connection test successful")
                return True
            else:
                self.logger.warning("VPN connection test failed")
                return False
                
        except Exception as e:
            self.logger.warning(f"VPN connection test error: {e}")
            return False
    
    def stop_psiphon3(self):
        """Stop Psiphon3 VPN if running"""
        try:
            if hasattr(self, 'psiphon_process') and self.psiphon_process:
                self.logger.info("Stopping Psiphon3...")
                self.psiphon_process.terminate()
                self.psiphon_process.wait(timeout=10)
                self.logger.info("Psiphon3 stopped successfully")
        except Exception as e:
            self.logger.warning(f"Error stopping Psiphon3: {e}")
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get random headers to avoid detection"""
        user_agents = self.config.get('scraping_settings', {}).get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ])
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and random delays"""
        max_retries = self.config.get('scraping_settings', {}).get('max_retries', 3)
        delay_config = self.config.get('scraping_settings', {}).get('request_delay', {'min': 1, 'max': 3})
        
        for attempt in range(max_retries):
            try:
                # Add random delay between requests
                if attempt > 0:
                    delay = random.uniform(delay_config.get('min', 1), delay_config.get('max', 3))
                    time.sleep(delay)
                
                # Update headers for each request
                headers = self.get_random_headers()
                kwargs['headers'] = headers
                
                # Get timeout from kwargs or use default
                timeout = kwargs.pop('timeout', 30)
                
                # Make request
                if method.upper() == 'GET':
                    response = self.session.get(url, timeout=timeout, **kwargs)
                elif method.upper() == 'POST':
                    response = self.session.post(url, timeout=timeout, **kwargs)
                else:
                    response = self.session.request(method, url, timeout=timeout, **kwargs)
                
                if response.status_code == 200:
                    self.logger.info(f"Successfully fetched: {url}")
                    return response
                elif response.status_code == 403:
                    self.logger.warning(f"Access forbidden (403) for {url} - may need different proxy or headers")
                elif response.status_code == 429:
                    self.logger.warning(f"Rate limited (429) for {url} - waiting longer")
                    time.sleep(random.uniform(5, 10))
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.ProxyError as e:
                self.logger.warning(f"Proxy error (attempt {attempt + 1}): {e}")
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Timeout error (attempt {attempt + 1}): {e}")
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                wait_time = random.uniform(2, 5) * (attempt + 1)  # Exponential backoff
                self.logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
                    
        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    def scrape_westlotto(self) -> list:
        """Scrape EuroJackpot data from westlotto.de (robust, full columns)"""
        import re
        url = "https://www.westlotto.de/eurojackpot/gewinnzahlen/gewinnzahlen.html"
        session = self.session
        results = []
        try:
            # واکشی صفحه اصلی برای دریافت سال‌ها
            response = self.make_request(url)
            if not response:
                return results
            soup = BeautifulSoup(response.text, "html.parser")
            jahr_options = soup.find('select', {'name': 'jahr'})
            jahre = []
            if jahr_options:
                for opt in jahr_options.find_all('option'):
                    val = opt.get('value')
                    if val and re.match(r'\d{4}', val):
                        jahre.append(val)
            all_dates = []
            for jahr in jahre:
                resp = self.make_request(url, params={'jahr': jahr})
                if not resp or resp.status_code != 200:
                    continue
                soup_jahr = BeautifulSoup(resp.text, "html.parser")
                date_options = soup_jahr.find('select', {'name': 'datum'})
                if date_options:
                    for opt in date_options.find_all('option'):
                        val = opt.get('value')
                        if val and re.match(r'\d{2}\.\d{2}\.\d{4}', val):
                            all_dates.append(val)
            all_dates = sorted(list(set(all_dates)), key=lambda d: [int(d[6:]), int(d[3:5]), int(d[:2])])
            for date_str in all_dates:
                m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", date_str)
                if not m:
                    continue
                day, month, year = map(int, m.groups())
                draw_date_int = int(f"{year}{month:02d}{day:02d}")
                
                today_int = int(datetime.datetime.now().strftime('%Y%m%d'))
                
                if draw_date_int < 20220325 or draw_date_int > today_int:
                    continue
                params = {'datum': date_str}
                resp = self.make_request(url, params=params)
                if not resp or resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                day_of_week = datetime.date(year, month, day).isoweekday()
                # اعداد قرعه‌کشی
                main_numbers = [None]*5
                euro_numbers = [None]*2
                number_spans = soup.find_all("span", class_="polygon-label")
                if number_spans and len(number_spans) >= 7:
                    nums = [int(span.get_text(strip=True)) for span in number_spans[:7]]
                    main_numbers = nums[:5]
                    euro_numbers = nums[5:7]
                # فروش بلیت
                ticket_sales = 0
                sales_h4 = soup.find(lambda tag: tag.name in ['h4', 'p', 'div'] and tag.get_text().strip().startswith('Spieleinsatz'))
                sales_text = None
                if sales_h4:
                    sales_span = sales_h4.find('span')
                    if sales_span:
                        sales_text = sales_span.get_text(strip=True)
                    else:
                        m2 = re.search(r'Spieleinsatz:\s*([\d\.]+,\d{2})', sales_h4.get_text())
                        if m2:
                            sales_text = m2.group(1)
                if not sales_text:
                    m2 = re.search(r'Spieleinsatz:\s*([\d\.]+,\d{2})', soup.get_text())
                    if m2:
                        sales_text = m2.group(1)
                if sales_text:
                    cleaned_sales = sales_text.replace('EUR', '').replace('€', '').strip()
                    try:
                        ticket_sales = int(float(cleaned_sales.replace('.', '').replace(',', '.')))
                    except Exception:
                        ticket_sales = 0
                # جدول جوایز
                prize_levels = [0]*12
                winners_levels = [0]*12
                table = soup.find("table", class_="table--foldable")
                if table:
                    rows = table.find_all("tr")
                    for row in rows:
                        tds = row.find_all("td")
                        if len(tds) < 3:
                            continue
                        prize_name = tds[0].get_text(strip=True)
                        winners = tds[1].get_text(strip=True)
                        prize_amount_text = tds[2].get_text(strip=True)
                        m3 = re.match(r"(\d+)", prize_name)
                        idx = int(m3.group(1))-1 if m3 else None
                        # مبلغ جایزه
                        prize_amount = 0
                        if prize_amount_text and ("EUR" in prize_amount_text or "€" in prize_amount_text):
                            cleaned = prize_amount_text.replace("EUR", "").replace("€", "").replace(".", "").replace(",", ".").strip()
                            try:
                                prize_amount = float(cleaned)
                            except Exception:
                                prize_amount = 0
                        # تعداد برندگان
                        winners_count = 0
                        if winners:
                            try:
                                winners_count = int(winners.replace('.', '').replace(',', ''))
                            except Exception:
                                winners_count = 0
                        if idx is not None and 0 <= idx < 12:
                            prize_levels[idx] = prize_amount
                            winners_levels[idx] = winners_count
                # تبدیل قطعی Noneها به 0
                def safe_float(x):
                    try:
                        return float(x)
                    except Exception:
                        return 0.0
                def safe_int(x):
                    try:
                        return int(float(x))
                    except Exception:
                        return 0
                prize_levels = [safe_float(x) for x in prize_levels]
                winners_levels = [safe_int(x) for x in winners_levels]
                # ساخت دیکشنری ردیف
                row_dict = {
                    'draw_date': draw_date_int,
                    'day_of_week': day_of_week,
                    'main_number_1': main_numbers[0],
                    'main_number_2': main_numbers[1],
                    'main_number_3': main_numbers[2],
                    'main_number_4': main_numbers[3],
                    'main_number_5': main_numbers[4],
                    'euro_number_1': euro_numbers[0],
                    'euro_number_2': euro_numbers[1],
                    'ticket_sales_amount': ticket_sales,
                }
                for i in range(12):
                    row_dict[f'prize_tier_{i+1}'] = prize_levels[i]
                    row_dict[f'winners_tier_{i+1}'] = winners_levels[i]
                results.append(row_dict)
                time.sleep(0.5)
        except Exception as e:
            self.logger.error(f"Error scraping WestLotto: {e}")
        return results
    
    def scrape_eurojackpot_org(self) -> List[Dict]:
        """Scrape results from EuroJackpot.org using API"""
        self.logger.info("Scraping EuroJackpot.org using API...")
        results = []
        
        try:
            # First get available dates from main page
            response = self.make_request(self.target_urls['eurojackpot_org'])
            if not response:
                return results
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for date selector
            date_select = soup.find('select')
            if not date_select:
                self.logger.warning("No date selector found")
                return results
            
            # Get available dates
            dates = []
            for option in date_select.find_all('option'):
                if option.get('value'):
                    dates.append(option['value'])
            
            self.logger.info(f"Found {len(dates)} available dates")
            
            # Fetch results for all available dates
            self.logger.info(f"Processing {len(dates)} available dates...")
            for i, date in enumerate(dates):
                try:
                    api_url = f"https://www.eurojackpot.org/results/?date={date}"
                    api_response = self.make_request(api_url)
                    
                    if api_response and api_response.status_code == 200:
                        # Check if response is JSON
                        content_type = api_response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            try:
                                data = api_response.json()
                                result = self.parse_api_data(data)
                                standard = self.map_to_standard_result(result) if result else None
                                if standard:
                                    results.append(standard)
                                    self.logger.info(f"Successfully scraped result for {date}")
                            except (ValueError, json.JSONDecodeError) as e:
                                self.logger.warning(f"Failed to parse JSON response for {date}: {e}")
                        else:
                            # Try to parse HTML response
                            soup = BeautifulSoup(api_response.content, 'html.parser')
                            # Look for JSON data in script tags or try to extract from HTML
                            json_results = self.extract_json_results(soup)
                            if json_results:
                                mapped = [self.map_to_standard_result(item) for item in json_results]
                                mapped = [m for m in mapped if m]
                                results.extend(mapped)
                                self.logger.info(f"Successfully scraped {len(mapped)} results from HTML for {date}")
                    
                    # Add delay between requests
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.warning(f"Error fetching results for {date}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error scraping EuroJackpot.org: {e}")
        
        return results
    
    def parse_api_data(self, data: Dict) -> Optional[Dict]:
        """Parse API response data with complete information"""
        try:
            if not data or 'numbers' not in data:
                return None
            
            # Extract date
            date_info = data.get('date', {})
            year = date_info.get('year', '')
            month = date_info.get('month', '')
            day = date_info.get('day', '')
            
            # Handle both string and integer values
            if isinstance(month, str):
                month = int(month) if month.isdigit() else 1
            if isinstance(day, str):
                day = int(day) if day.isdigit() else 1
            if isinstance(year, str):
                year = int(year) if year.isdigit() else 2025
                
            draw_date = f"{year}-{month:02d}-{day:02d}"
            
            # Extract numbers
            numbers = data.get('numbers', {})
            main_numbers = numbers.get('numbers', [])
            euro_numbers = numbers.get('extraNumbers', [])
            
            parsed_draw_date = self.parse_date(draw_date)
            if parsed_draw_date is None:
                return None

            if len(main_numbers) >= 5 and len(euro_numbers) >= 2:
                result = {
                    'draw_date': parsed_draw_date,
                    'main_numbers': main_numbers[:5],
                    'euro_numbers': euro_numbers[:2]
                }
                
                # Extract additional information if available
                if 'ticketSales' in data:
                    result['ticket_sales_amount'] = data['ticketSales']
                elif 'jackpot' in data:
                    # Use jackpot as a proxy for ticket sales (higher jackpot = more sales)
                    result['jackpot_amount'] = data['jackpot']
                if 'nr' in data:
                    result['draw_number'] = data['nr']
                
                # Extract odds and winners information
                odds = data.get('odds', {})
                if odds:
                    result['odds'] = {}
                    result['winners'] = {}
                    result['prizes'] = {}
                    
                    for rank_key, rank_data in odds.items():
                        if isinstance(rank_data, dict):
                            result['odds'][rank_key] = rank_data
                            result['winners'][rank_key] = rank_data.get('winners', 0)
                            result['prizes'][rank_key] = rank_data.get('prize', 0)
                
                return result
            
        except Exception as e:
            self.logger.warning(f"Error parsing API data: {e}")
        
        return None

    def map_to_standard_result(self, raw_result: Dict) -> Optional[Dict]:
        """Map source-specific result into core.draws and core.draw_details standard row format."""
        if not raw_result:
            return None

        draw_date = raw_result.get('draw_date')
        if draw_date is None:
            return None
        try:
            draw_date = int(draw_date)
        except Exception:
            return None

        main_numbers = raw_result.get('main_numbers')
        euro_numbers = raw_result.get('euro_numbers')

        if not main_numbers:
            main_numbers = [
                raw_result.get('main_number_1'), raw_result.get('main_number_2'), raw_result.get('main_number_3'),
                raw_result.get('main_number_4'), raw_result.get('main_number_5')
            ]
        if not euro_numbers:
            euro_numbers = [raw_result.get('euro_number_1'), raw_result.get('euro_number_2')]

        if len(main_numbers) < 5 or len(euro_numbers) < 2:
            return None
        try:
            main_numbers = [int(x) for x in main_numbers[:5]]
            euro_numbers = [int(x) for x in euro_numbers[:2]]
        except Exception:
            return None

        standardized = {
            'draw_date': draw_date,
            'day_of_week': self.get_day_of_week(draw_date),
            'main_number_1': main_numbers[0],
            'main_number_2': main_numbers[1],
            'main_number_3': main_numbers[2],
            'main_number_4': main_numbers[3],
            'main_number_5': main_numbers[4],
            'euro_number_1': euro_numbers[0],
            'euro_number_2': euro_numbers[1],
            'ticket_sales_amount': raw_result.get('ticket_sales_amount', 0),
        }
        for i in range(1, 13):
            standardized[f'prize_tier_{i}'] = raw_result.get(f'prize_tier_{i}', 0)
            standardized[f'winners_tier_{i}'] = raw_result.get(f'winners_tier_{i}', 0)
        return standardized
    
    def extract_json_results(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract results from JSON data in script tags"""
        results = []
        
        try:
            # Look for JSON data in script tags
            script_tags = soup.find_all('script', type='application/json')
            if not script_tags:
                script_tags = soup.find_all('script')
            
            for script in script_tags:
                if script.string:
                    try:
                        # Try to find JSON data
                        json_match = re.search(r'\{.*\}', script.string, re.DOTALL)
                        if json_match:
                            json_data = json.loads(json_match.group())
                            parsed_results = self.parse_json_data(json_data)
                            results.extend(parsed_results)
                    except (json.JSONDecodeError, AttributeError):
                        continue
            
        except Exception as e:
            self.logger.warning(f"Error extracting JSON results: {e}")
        
        return results
    
    def parse_json_data(self, data: Dict) -> List[Dict]:
        """Parse JSON data to extract results"""
        results = []
        
        try:
            # Common JSON structures for lottery results
            possible_paths = [
                ['results'],
                ['data', 'results'],
                ['draws'],
                ['data', 'draws'],
                ['eurojackpot', 'results'],
                ['lottery', 'results']
            ]
            
            for path in possible_paths:
                current_data = data
                for key in path:
                    if isinstance(current_data, dict) and key in current_data:
                        current_data = current_data[key]
                    else:
                        current_data = None
                        break
                
                if current_data and isinstance(current_data, list):
                    for item in current_data:
                        result = self.parse_single_json_result(item)
                        if result:
                            results.append(result)
                    break
            
        except Exception as e:
            self.logger.warning(f"Error parsing JSON data: {e}")
        
        return results
    
    def parse_single_json_result(self, item: Dict) -> Optional[Dict]:
        """Parse a single JSON result item"""
        try:
            # Try different field names for date
            date_fields = ['date', 'drawDate', 'draw_date', 'drawingDate']
            date_value = None
            for field in date_fields:
                if field in item:
                    date_value = item[field]
                    break
            
            if not date_value:
                return None
            
            # Try different field names for numbers
            number_fields = {
                'main': ['mainNumbers', 'main_numbers', 'numbers', 'winningNumbers'],
                'euro': ['euroNumbers', 'euro_numbers', 'additionalNumbers', 'extraNumbers']
            }
            
            main_numbers = []
            euro_numbers = []
            
            for field in number_fields['main']:
                if field in item and isinstance(item[field], list):
                    main_numbers = item[field]
                    break
            
            for field in number_fields['euro']:
                if field in item and isinstance(item[field], list):
                    euro_numbers = item[field]
                    break
            
            parsed_draw_date = self.parse_date(date_value)
            if parsed_draw_date is None:
                return None

            if len(main_numbers) >= 5 and len(euro_numbers) >= 2:
                return {
                    'draw_date': parsed_draw_date,
                    'main_numbers': main_numbers[:5],
                    'euro_numbers': euro_numbers[:2]
                }
            
        except Exception as e:
            self.logger.warning(f"Error parsing single JSON result: {e}")
        
        return None
    
    def parse_table_results(self, table) -> List[Dict]:
        """Parse results from HTML table"""
        results = []
        
        try:
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 7:  # Need at least date + 5 main + 2 euro numbers
                    continue
                
                try:
                    # Extract date from first cell
                    date_text = cells[0].get_text(strip=True)
                    draw_date = self.parse_date(date_text)
                    if draw_date is None:
                        continue
                    
                    # Extract main numbers (usually 5 numbers)
                    main_numbers = []
                    for i in range(1, 6):
                        try:
                            num_text = cells[i].get_text(strip=True)
                            num = int(re.sub(r'[^\d]', '', num_text))  # Remove non-digits
                            main_numbers.append(num)
                        except (ValueError, IndexError):
                            continue
                    
                    # Extract euro numbers (usually 2 numbers)
                    euro_numbers = []
                    for i in range(6, 8):
                        try:
                            num_text = cells[i].get_text(strip=True)
                            num = int(re.sub(r'[^\d]', '', num_text))  # Remove non-digits
                            euro_numbers.append(num)
                        except (ValueError, IndexError):
                            continue
                    
                    if len(main_numbers) == 5 and len(euro_numbers) == 2:
                        results.append({
                            'draw_date': draw_date,
                            'main_numbers': main_numbers,
                            'euro_numbers': euro_numbers
                        })
                
                except Exception as e:
                    self.logger.warning(f"Error parsing table row: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing table results: {e}")
        
        return results
    
    def parse_date(self, date_str: str) -> Optional[int]:
        """Parse date string to YYYYMMDD format (integer). Returns None if invalid."""
        try:
            # Clean the date string
            date_str = re.sub(r'[^\d\-\.\/]', '', str(date_str))
            
            # Try different date formats
            formats = [
                '%d.%m.%Y',
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%Y.%m.%d',
                '%d.%m.%y',
                '%d/%m/%y'
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.datetime.strptime(date_str, fmt)
                    return int(parsed_date.strftime('%Y%m%d'))
                except ValueError:
                    continue
            
            # If no format matches, try to extract numbers
            numbers = re.findall(r'\d+', date_str)
            if len(numbers) >= 3:
                # Try to construct date from numbers
                if len(numbers[0]) == 4:  # YYYY format
                    year, month, day = int(numbers[0]), int(numbers[1]), int(numbers[2])
                else:  # DD format
                    day, month, year = int(numbers[0]), int(numbers[1]), int(numbers[2])
                
                try:
                    parsed_date = datetime.datetime(year, month, day)
                    return int(parsed_date.strftime('%Y%m%d'))
                except ValueError as e:
                    logging.warning(f"Invalid date values: year={year}, month={month}, day={day}: {e}")
            
            # Invalid date string
            return None
            
        except Exception as e:
            logging.error(f"Failed to parse draw date: {e}")
            return None
    
    def get_day_of_week(self, draw_date: int) -> int:
        """Get day of week from YYYYMMDD format (1=Monday, 7=Sunday)"""
        try:
            # Convert YYYYMMDD to datetime
            date_str = str(draw_date)
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            
            dt = datetime.datetime(year, month, day)
            # weekday() returns 0=Monday, 6=Sunday, so add 1
            return dt.weekday() + 1
            
        except Exception as e:
            logging.error(f"Failed to calculate day of week for {draw_date}: {e}")
            return 1  # Default to Monday
    
    def _open_connection_with_params(self, host: str, port: int, user: str, password: str, dbname: str):
        """Open a PostgreSQL connection with explicit params. Uses SSL when host contains neon.tech. Avoids password in connection string when SSL is used (PGPASSWORD + immediate cleanup)."""
        use_ssl = "neon.tech" in (host or "")
        if use_ssl:
            if password:
                os.environ["PGPASSWORD"] = password
            try:
                conn = psycopg2.connect(
                    host=host, port=port, dbname=dbname, user=user,
                    sslmode="require",
                )
                return conn
            finally:
                os.environ.pop("PGPASSWORD", None)
        return psycopg2.connect(
            host=host, port=port, dbname=dbname, user=user, password=password
        )

    def _clip_numeric_12_2(self, v):
        """Clip numeric to NUMERIC(12,2) range for insert."""
        if v is None:
            return 0.0
        try:
            x = float(v)
            if x > 9999999999.99:
                return 9999999999.99
            if x < -9999999999.99:
                return -9999999999.99
            return round(x, 2)
        except (TypeError, ValueError):
            return 0.0

    def _clip_numeric_10_2(self, v):
        """Clip numeric to NUMERIC(10,2) range for insert."""
        if v is None:
            return 0.0
        try:
            x = float(v)
            if x > 99999999.99:
                return 99999999.99
            if x < -99999999.99:
                return -99999999.99
            return round(x, 2)
        except (TypeError, ValueError):
            return 0.0

    def _upsert_draws(self, conn, results: list) -> int:
        """Upsert draw numbers into core.draws."""
        query = """
            INSERT INTO core.draws
                (draw_date, n1, n2, n3, n4, n5, e1, e2)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (draw_date) DO UPDATE SET
                n1 = EXCLUDED.n1,
                n2 = EXCLUDED.n2,
                n3 = EXCLUDED.n3,
                n4 = EXCLUDED.n4,
                n5 = EXCLUDED.n5,
                e1 = EXCLUDED.e1,
                e2 = EXCLUDED.e2,
                updated_at = NOW()
        """
        count = 0
        with conn.cursor() as cursor:
            for r in results:
                try:
                    main = sorted([
                        r['main_number_1'], r['main_number_2'],
                        r['main_number_3'], r['main_number_4'],
                        r['main_number_5']
                    ])
                    euro = sorted([r['euro_number_1'], r['euro_number_2']])
                    cursor.execute(query, (
                        r['draw_date'],
                        main[0], main[1], main[2], main[3], main[4],
                        euro[0], euro[1]
                    ))
                    count += 1
                except Exception as e:
                    self.logger.warning(
                        "core.draws upsert failed for draw_date=%s: %s",
                        r.get('draw_date'), e
                    )
                    conn.rollback()
                    continue
        conn.commit()
        self.logger.info("core.draws: %d rows upserted.", count)
        return count

    def _upsert_draw_details(self, conn, results: list) -> int:
        """Upsert prize and winner data into core.draw_details."""
        query = """
            INSERT INTO core.draw_details (
                draw_date, day_of_week, ticket_sales_amount,
                prize_tier_1,  prize_tier_2,  prize_tier_3,
                prize_tier_4,  prize_tier_5,  prize_tier_6,
                prize_tier_7,  prize_tier_8,  prize_tier_9,
                prize_tier_10, prize_tier_11, prize_tier_12,
                winners_tier_1,  winners_tier_2,  winners_tier_3,
                winners_tier_4,  winners_tier_5,  winners_tier_6,
                winners_tier_7,  winners_tier_8,  winners_tier_9,
                winners_tier_10, winners_tier_11, winners_tier_12
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (draw_date) DO UPDATE SET
                day_of_week          = EXCLUDED.day_of_week,
                ticket_sales_amount  = EXCLUDED.ticket_sales_amount,
                prize_tier_1         = EXCLUDED.prize_tier_1,
                prize_tier_2         = EXCLUDED.prize_tier_2,
                prize_tier_3         = EXCLUDED.prize_tier_3,
                prize_tier_4         = EXCLUDED.prize_tier_4,
                prize_tier_5         = EXCLUDED.prize_tier_5,
                prize_tier_6         = EXCLUDED.prize_tier_6,
                prize_tier_7         = EXCLUDED.prize_tier_7,
                prize_tier_8         = EXCLUDED.prize_tier_8,
                prize_tier_9         = EXCLUDED.prize_tier_9,
                prize_tier_10        = EXCLUDED.prize_tier_10,
                prize_tier_11        = EXCLUDED.prize_tier_11,
                prize_tier_12        = EXCLUDED.prize_tier_12,
                winners_tier_1       = EXCLUDED.winners_tier_1,
                winners_tier_2       = EXCLUDED.winners_tier_2,
                winners_tier_3       = EXCLUDED.winners_tier_3,
                winners_tier_4       = EXCLUDED.winners_tier_4,
                winners_tier_5       = EXCLUDED.winners_tier_5,
                winners_tier_6       = EXCLUDED.winners_tier_6,
                winners_tier_7       = EXCLUDED.winners_tier_7,
                winners_tier_8       = EXCLUDED.winners_tier_8,
                winners_tier_9       = EXCLUDED.winners_tier_9,
                winners_tier_10      = EXCLUDED.winners_tier_10,
                winners_tier_11      = EXCLUDED.winners_tier_11,
                winners_tier_12      = EXCLUDED.winners_tier_12,
                updated_at           = NOW()
        """
        count = 0
        with conn.cursor() as cursor:
            for r in results:
                try:
                    cursor.execute(query, (
                        r['draw_date'],
                        r.get('day_of_week', 0),
                        r.get('ticket_sales_amount', 0),
                        r.get('prize_tier_1',  0), r.get('prize_tier_2',  0),
                        r.get('prize_tier_3',  0), r.get('prize_tier_4',  0),
                        r.get('prize_tier_5',  0), r.get('prize_tier_6',  0),
                        r.get('prize_tier_7',  0), r.get('prize_tier_8',  0),
                        r.get('prize_tier_9',  0), r.get('prize_tier_10', 0),
                        r.get('prize_tier_11', 0), r.get('prize_tier_12', 0),
                        r.get('winners_tier_1',  0), r.get('winners_tier_2',  0),
                        r.get('winners_tier_3',  0), r.get('winners_tier_4',  0),
                        r.get('winners_tier_5',  0), r.get('winners_tier_6',  0),
                        r.get('winners_tier_7',  0), r.get('winners_tier_8',  0),
                        r.get('winners_tier_9',  0), r.get('winners_tier_10', 0),
                        r.get('winners_tier_11', 0), r.get('winners_tier_12', 0),
                    ))
                    count += 1
                except Exception as e:
                    self.logger.warning(
                        "core.draw_details upsert failed for draw_date=%s: %s",
                        r.get('draw_date'), e
                    )
                    conn.rollback()
                    continue
        conn.commit()
        self.logger.info("core.draw_details: %d rows upserted.", count)
        return count

    def save_results(self, results: list) -> int:
        """Save scraped results to Neon (core.draws + core.draw_details)."""
        if not results:
            return 0
        self.logger.info("Saving %d results to Neon...", len(results))
        try:
            conn = self._open_connection()
            try:
                draws_count   = self._upsert_draws(conn, results)
                details_count = self._upsert_draw_details(conn, results)
                self.logger.info(
                    "Save complete: %d draws, %d details.",
                    draws_count, details_count
                )
                return draws_count
            finally:
                conn.close()
        except Exception as e:
            self.logger.exception("save_results failed: %s", e)
            return 0
    
    def run_scraper(self) -> int:
        """Main method to run the scraper"""
        self.logger.info("Starting advanced EuroJackpot scraper...")
        
        # Start Psiphon3 VPN first
        self.logger.info("Step 1: Starting Psiphon3 VPN...")
        if not self.start_psiphon3():
            self.logger.warning("Failed to start Psiphon3, continuing without VPN...")
        all_results = []
        try:
            self.logger.info(f"Trying WestLotto...")
            results = self.scrape_westlotto()
            if results:
                self.logger.info(f"Found {len(results)} results from WestLotto")
                all_results.extend(results)
            else:
                self.logger.warning(f"No results found from WestLotto")
            if not all_results:
                self.logger.warning("No results found from WestLotto")
                return 0
            saved_count = self.save_results(all_results)
            self.logger.info(f"Scraping completed. Saved {saved_count} results.")
            return saved_count
        except Exception as e:
            self.logger.error(f"Scraper failed: {e}")
            return 0
        finally:
            self.logger.info("Stopping Psiphon3 VPN...")
            self.stop_psiphon3()
            self.session.close()


def main():
    """Main function to run the advanced scraper"""
    print("Advanced EuroJackpot Scraper with Psiphon3 VPN")
    print("=" * 50)
    print("This scraper will:")
    print("1. Start Psiphon3 VPN")
    print("2. Wait 30 seconds for VPN connection")
    print("3. Extract EuroJackpot data")
    print("4. Save data to database")
    print("5. Stop VPN connection")
    print("=" * 50)
    
    try:
        # Initialize scraper
        print("\nInitializing scraper...")
        scraper = AdvancedEuroJackpotScraper()
        
        if not scraper.test_connection():
            print("Connection test failed. Check DATABASE_URL in .env")
            sys.exit(1)
        print("Connection test passed.")
        
        # Run scraper
        print("Starting scraping process...")
        saved_count = scraper.run_scraper()
        
        print(f"\nScraping completed successfully!")
        print(f"Results saved: {saved_count}")
        db_info = os.getenv("DATABASE_URL", "SQLite (Fallback)").split('@')[-1] if "@" in os.getenv("DATABASE_URL", "") else "Local/PostgreSQL"
        print(f"Database: {db_info}")
        print(f"Tables: core.draws, core.draw_details")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        print("VPN connection will be stopped...")
    except Exception as e:
        print(f"\nError: {e}")
        print("VPN connection will be stopped...")
        sys.exit(1)


if __name__ == "__main__":
    main()
