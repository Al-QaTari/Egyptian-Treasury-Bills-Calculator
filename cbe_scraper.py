# cbe_scraper.py (النسخة النهائية والنظيفة)
import os
import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver

# from selenium.common.exceptions import TimeoutException <-- تم حذفه
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional, Callable
import pytz
import platform

import constants as C
from db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def setup_driver() -> Optional[webdriver.Chrome]:
    """
    Initializes a headless Chrome WebDriver with environment-specific settings.
    """
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={C.USER_AGENT}")
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        if platform.system() == "Linux" and os.path.exists("/usr/bin/chromium"):
            logger.info(
                "Linux/Cloud environment detected. Using pre-installed chromium."
            )
            options.binary_location = "/usr/bin/chromium"
            service = Service(executable_path="/usr/bin/chromedriver")
        else:
            logger.info("Local environment detected. Using webdriver-manager.")
            log_path = os.devnull
            service = Service(ChromeDriverManager().install(), log_output=log_path)

        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Selenium driver initialized successfully.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Selenium driver: {e}", exc_info=True)
        return None


def verify_page_structure(page_source: str) -> None:
    logger.info("Verifying page structure for essential text markers...")
    for marker in C.ESSENTIAL_TEXT_MARKERS:
        if marker not in page_source:
            error_msg = (
                f"Page structure verification failed! Marker '{marker}' not found."
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
    logger.info("Page structure verification successful. All markers found.")


def parse_cbe_html(page_source: str) -> Optional[pd.DataFrame]:
    logger.info("Starting to parse HTML content using the robust logic.")
    soup = BeautifulSoup(page_source, "lxml")
    try:
        results_headers = soup.find_all(
            lambda tag: tag.name == "h2" and "النتائج" in tag.get_text()
        )
        if not results_headers:
            return None
        all_dataframes = []
        for header in results_headers:
            dates_table = header.find_next("table")
            if not dates_table:
                continue
            dates_df = pd.read_html(StringIO(str(dates_table)))[0]
            tenors = (
                pd.to_numeric(dates_df.columns[1:], errors="coerce")
                .dropna()
                .astype(int)
                .tolist()
            )
            session_dates_row = dates_df[dates_df.iloc[:, 0] == "تاريخ الجلسة"]
            if session_dates_row.empty or not tenors:
                continue
            session_dates = session_dates_row.iloc[0, 1 : len(tenors) + 1].tolist()
            dates_tenors_df = pd.DataFrame(
                {C.TENOR_COLUMN_NAME: tenors, C.SESSION_DATE_COLUMN_NAME: session_dates}
            )
            accepted_bids_header = header.find_next(
                lambda tag: tag.name in ["p", "strong"]
                and C.ACCEPTED_BIDS_KEYWORD in tag.get_text()
            )
            if not accepted_bids_header:
                continue
            yields_table = accepted_bids_header.find_next("table")
            if not yields_table:
                continue
            yields_df_raw = pd.read_html(StringIO(str(yields_table)))[0]
            yields_df_raw.columns = ["البيان"] + tenors
            yield_row = yields_df_raw[
                yields_df_raw.iloc[:, 0].str.contains(C.YIELD_ANCHOR_TEXT, na=False)
            ]
            if yield_row.empty:
                continue
            yield_series = yield_row.iloc[0, 1:].astype(float)
            yield_series.name = C.YIELD_COLUMN_NAME
            section_df = dates_tenors_df.join(yield_series, on=C.TENOR_COLUMN_NAME)
            if not section_df[C.YIELD_COLUMN_NAME].isnull().any():
                all_dataframes.append(section_df)
        if not all_dataframes:
            return None
        final_df = pd.concat(all_dataframes, ignore_index=True)
        final_df[C.DATE_COLUMN_NAME] = datetime.now(pytz.utc)
        final_df["session_date_dt"] = pd.to_datetime(
            final_df[C.SESSION_DATE_COLUMN_NAME], format="%d/%m/%Y", errors="coerce"
        )
        final_df = (
            final_df.sort_values("session_date_dt", ascending=False)
            .drop_duplicates(subset=[C.TENOR_COLUMN_NAME])
            .sort_values(by=C.TENOR_COLUMN_NAME)
        )
        return final_df
    except Exception as e:
        logger.error(f"A critical error occurred during parsing: {e}", exc_info=True)
        return None


def fetch_data_from_cbe(
    db_manager: DatabaseManager, status_callback: Optional[Callable[[str], None]] = None
) -> None:
    retries = C.SCRAPER_RETRIES
    delay_seconds = C.SCRAPER_RETRY_DELAY_SECONDS
    for attempt in range(retries):
        driver = None
        logger.info(f"--- Starting FULL scrape attempt {attempt + 1} of {retries} ---")
        try:
            if status_callback:
                status_callback(
                    f"محاولة ({attempt + 1}/{retries}): جاري إعداد المتصفح..."
                )
            driver = setup_driver()
            if not driver:
                raise RuntimeError("فشل إعداد المتصفح. لا يمكن المتابعة.")
            if status_callback:
                status_callback(
                    f"محاولة ({attempt + 1}/{retries}): جاري الاتصال بموقع البنك..."
                )
            driver.get(C.CBE_DATA_URL)
            WebDriverWait(driver, C.SCRAPER_TIMEOUT_SECONDS).until(
                EC.presence_of_element_located((By.TAG_NAME, "h2"))
            )
            if status_callback:
                status_callback(
                    f"محاولة ({attempt + 1}/{retries}): تم الاتصال، جاري تحليل المحتوى..."
                )
            page_source = driver.page_source
            verify_page_structure(page_source)
            final_df = parse_cbe_html(page_source)
            if final_df is not None and not final_df.empty:
                db_session_date_str = db_manager.get_latest_session_date()
                live_latest_date_str = final_df[C.SESSION_DATE_COLUMN_NAME].iloc[0]
                if db_session_date_str and live_latest_date_str == db_session_date_str:
                    if status_callback:
                        status_callback("البيانات محدثة بالفعل. لا حاجة للحفظ.")
                    time.sleep(2)
                    return
                if status_callback:
                    status_callback(
                        f"محاولة ({attempt + 1}/{retries}): تم العثور على بيانات جديدة، جاري الحفظ..."
                    )
                db_manager.save_data(final_df)
                if status_callback:
                    status_callback("اكتمل تحديث البيانات بنجاح!")
                return
        except Exception as e:  # هذا السطر يعالج كل الأخطاء بما فيها TimeoutException
            logger.error(
                f"An unexpected error occurred during full scrape attempt {attempt + 1}: {e}",
                exc_info=True,
            )
            if status_callback:
                status_callback(f"فشلت المحاولة {attempt + 1}: {e}")
        finally:
            if driver:
                driver.quit()
        if attempt < retries - 1:
            if status_callback:
                status_callback(f"ستتم إعادة المحاولة بعد {delay_seconds} ثانية...")
            time.sleep(delay_seconds)
    raise RuntimeError(
        f"فشلت جميع المحاولات ({retries}) لجلب البيانات من البنك المركزي."
    )
