# cbe_scraper.py (النسخة النهائية الكاملة والموثوقة)
import pandas as pd
from io import StringIO
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging
import time
from typing import Optional, List, Callable
import platform

import constants as C
from db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def setup_driver() -> Optional[webdriver.Chrome]:
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={C.USER_AGENT}")
    try:
        if platform.system() == "Windows" or platform.system() == "Darwin":
            logger.info(
                "Local environment (Windows/Mac) detected. Using automatic Selenium manager."
            )
            driver = webdriver.Chrome(options=options)
        else:
            logger.info("Linux environment detected. Using fixed driver path.")
            service = Service(executable_path="/usr/bin/chromedriver")
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
            error_msg = f"Page structure verification failed! Marker '{marker}' not found. Site design may have changed."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
    logger.info("Page structure verification successful. All markers found.")


def parse_cbe_html(page_source: str) -> Optional[pd.DataFrame]:
    logger.info("Starting to parse HTML content using the robust logic.")
    soup = BeautifulSoup(page_source, "lxml")

    try:
        results_header = soup.find(
            lambda tag: tag.name == "h2" and "النتائج" in tag.get_text()
        )
        if not results_header:
            logger.error(
                "Parse Error: Could not find the main 'النتائج' (Results) header."
            )
            return None

        dates_table = results_header.find_next("table")
        if not dates_table:
            logger.error("Could not find the session dates table.")
            return None

        dates_df = pd.read_html(StringIO(str(dates_table)))[0]
        tenors = (
            pd.to_numeric(dates_df.columns[1:], errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )
        session_dates_row = dates_df[dates_df.iloc[:, 0] == "تاريخ الجلسة"]
        if session_dates_row.empty:
            logger.error("Could not find 'تاريخ الجلسة' row in the dates table.")
            return None
        session_dates = session_dates_row.iloc[0, 1 : len(tenors) + 1].tolist()

        dates_tenors_df = pd.DataFrame(
            {C.TENOR_COLUMN_NAME: tenors, C.SESSION_DATE_COLUMN_NAME: session_dates}
        )

        accepted_bids_header = soup.find(
            lambda tag: tag.name in ["p", "strong"]
            and C.ACCEPTED_BIDS_KEYWORD in tag.get_text()
        )
        if not accepted_bids_header:
            logger.error("Could not find the 'العروض المقبولة' header.")
            return None

        yields_table = accepted_bids_header.find_next("table")
        if not yields_table:
            logger.error(
                "Could not find the yields table after the accepted bids header."
            )
            return None

        yields_df_raw = pd.read_html(StringIO(str(yields_table)))[0]
        yields_df_raw.columns = ["البيان"] + tenors

        yield_row = yields_df_raw[
            yields_df_raw.iloc[:, 0].str.contains(C.YIELD_ANCHOR_TEXT, na=False)
        ]
        if yield_row.empty:
            logger.error(
                "Could not find 'متوسط العائد المرجح' row in the yields table."
            )
            return None

        yield_series = yield_row.iloc[0, 1:].astype(float)
        yield_series.name = C.YIELD_COLUMN_NAME

        final_df = dates_tenors_df.join(yield_series, on=C.TENOR_COLUMN_NAME)

        if final_df[C.YIELD_COLUMN_NAME].isnull().any():
            logger.error("Data merge failed, resulting in NaN values for yields.")
            return None

        final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
        final_df["session_date_dt"] = pd.to_datetime(
            final_df[C.SESSION_DATE_COLUMN_NAME], format="%d/%m/%Y", errors="coerce"
        )

        logger.info(f"Successfully parsed and merged data for {len(final_df)} tenors.")
        return final_df

    except Exception as e:
        logger.error(
            f"A critical error occurred during parsing logic: {e}", exc_info=True
        )
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
                live_latest_date = final_df["session_date_dt"].max()
                live_latest_date_str = live_latest_date.strftime("%d/%m/%Y")

                logger.info(f"Latest date found on page: {live_latest_date_str}")
                logger.info(f"Latest date in DB: {db_session_date_str}")

                if db_session_date_str and live_latest_date_str == db_session_date_str:
                    logger.info(
                        "No new data found after full scrape. Data is up-to-date."
                    )
                    if status_callback:
                        status_callback("البيانات محدثة بالفعل. لا حاجة للحفظ.")
                    time.sleep(2)
                    return

                if status_callback:
                    status_callback(
                        f"محاولة ({attempt + 1}/{retries}): تم العثور على بيانات جديدة، جاري الحفظ..."
                    )

                final_df = final_df.drop(columns=["session_date_dt"])

                db_manager.save_data(final_df)
                logger.info("Data successfully scraped and saved.")
                if status_callback:
                    status_callback("اكتمل تحديث البيانات بنجاح!")
                return
            else:
                logger.error("Full parsing failed. No data was saved for this attempt.")

        except TimeoutException:
            logger.warning(
                f"Page load timed out on attempt {attempt + 1}.", exc_info=True
            )
            if status_callback:
                status_callback(
                    f"فشلت المحاولة {attempt + 1}: استغرق تحميل الصفحة وقتاً طويلاً."
                )
        except Exception as e:
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
            logger.info(f"Waiting for {delay_seconds} seconds before next attempt...")
            if status_callback:
                status_callback(f"ستتم إعادة المحاولة بعد {delay_seconds} ثانية...")
            time.sleep(delay_seconds)

    logger.critical(f"All {retries} attempts to fetch data from CBE failed.")
    raise RuntimeError(
        f"فشلت جميع المحاولات ({retries}) لجلب البيانات من البنك المركزي."
    )
