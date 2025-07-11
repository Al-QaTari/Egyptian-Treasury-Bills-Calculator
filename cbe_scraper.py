# cbe_scraper.py
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
import requests

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
                "تم اكتشاف بيئة محلية (ويندوز/ماك). سيتم استخدام مدير سيلينيوم التلقائي."
            )
            driver = webdriver.Chrome(options=options)
        else:
            logger.info("تم اكتشاف بيئة لينكس. سيتم استخدام المسار الثابت للمشغل.")
            service = Service(executable_path="/usr/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
        logger.info("تم تشغيل متصفح سيلينيوم بنجاح.")
        return driver
    except Exception as e:
        logger.error(f"فشل تشغيل متصفح سيلينيوم. الخطأ: {e}", exc_info=True)
        return None


def verify_page_structure(page_source: str) -> None:
    logger.info("Verifying page structure for essential text markers...")
    for marker in C.ESSENTIAL_TEXT_MARKERS:
        if marker not in page_source:
            error_msg = f"فشل التحقق من هيكل الصفحة! العلامة النصية '{marker}' غير موجودة. ربما تم تغيير تصميم الموقع."
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
    logger.info("Page structure verification successful. All markers found.")


def parse_cbe_html(
    page_source: str, is_quick_check: bool = False
) -> Optional[str | pd.DataFrame]:
    logger.info(f"Starting to parse HTML content. Quick check: {is_quick_check}")
    soup = BeautifulSoup(page_source, "lxml")
    if is_quick_check:
        first_header = soup.find("h2", string=lambda t: "النتائج" in t if t else False)
        if first_header:
            results_table = first_header.find_next("table")
            if results_table:
                session_date_row = results_table.find(
                    "td", string=lambda t: "تاريخ الجلسة" in t if t else False
                )
                if session_date_row and session_date_row.find_next_sibling("td"):
                    live_date = session_date_row.find_next_sibling("td").get_text(
                        strip=True
                    )
                    logger.info(f"Quick check found live session date: {live_date}")
                    return live_date
        logger.warning("Quick check could not find a session date.")
        return None

    results_headers = soup.find_all(
        lambda tag: tag.name == "h2" and "النتائج" in tag.get_text()
    )
    if not results_headers:
        logger.error("Parse Error: Could not find any 'النتائج' (Results) headers.")
        return None

    all_dataframes: List[pd.DataFrame] = []
    for header in results_headers:
        results_table = header.find_next("table")
        if not results_table:
            logger.warning(
                "Found a 'Results' header but no subsequent table. Skipping."
            )
            continue
        try:
            results_df = pd.read_html(StringIO(str(results_table)))[0]
            tenors = (
                pd.to_numeric(results_df.columns[1:], errors="coerce")
                .dropna()
                .astype(int)
                .tolist()
            )
            if not tenors:
                continue
            session_date_row = results_df[results_df.iloc[:, 0] == "تاريخ الجلسة"]
            if session_date_row.empty:
                continue
            session_dates = session_date_row.iloc[0, 1 : len(tenors) + 1].tolist()
            accepted_bids_header = header.find_next(
                lambda tag: tag.name in ["p", "strong"]
                and C.ACCEPTED_BIDS_KEYWORD in tag.get_text()
            )
            if not accepted_bids_header:
                continue
            accepted_bids_table = accepted_bids_header.find_next("table")
            if not accepted_bids_table:
                continue
            accepted_df = pd.read_html(StringIO(str(accepted_bids_table)))[0]
            yield_row = accepted_df[
                accepted_df.iloc[:, 0].str.contains(C.YIELD_ANCHOR_TEXT, na=False)
            ]
            if yield_row.empty:
                continue
            yields = (
                pd.to_numeric(yield_row.iloc[0, 1 : len(tenors) + 1], errors="coerce")
                .dropna()
                .astype(float)
                .tolist()
            )
            if len(tenors) == len(yields) == len(session_dates):
                section_df = pd.DataFrame(
                    {
                        C.TENOR_COLUMN_NAME: tenors,
                        C.YIELD_COLUMN_NAME: yields,
                        C.SESSION_DATE_COLUMN_NAME: session_dates,
                    }
                )
                all_dataframes.append(section_df)
        except Exception as e:
            logger.error(f"Error processing a section: {e}", exc_info=True)
            continue
    if not all_dataframes:
        return None
    final_df = pd.concat(all_dataframes, ignore_index=True)
    final_df[C.DATE_COLUMN_NAME] = datetime.now().strftime("%Y-%m-%d")
    final_df = final_df.sort_values(by=C.TENOR_COLUMN_NAME).reset_index(drop=True)
    logger.info(f"Successfully parsed a total of {len(final_df)} tenors from the page.")
    return final_df


def fetch_data_from_cbe(
    db_manager: DatabaseManager, status_callback: Optional[Callable[[str], None]] = None
) -> None:
    try:
        if status_callback:
            status_callback("التحقق من وجود تحديثات جديدة...")

        db_session_date = db_manager.get_latest_session_date()
        headers = {"User-Agent": C.USER_AGENT}
        response = requests.get(C.CBE_DATA_URL, headers=headers, timeout=15)
        response.raise_for_status()
        verify_page_structure(response.text)

        live_session_date = parse_cbe_html(response.content, is_quick_check=True)
        logger.info(f"Live session date from CBE website: {live_session_date}")
        logger.info(f"Most recent session date in database: {db_session_date}")

        if (
            live_session_date
            and db_session_date
            and live_session_date == db_session_date
        ):
            logger.info("No new data found. Skipping full scrape.")
            if status_callback:
                status_callback("البيانات محدثة بالفعل. لا حاجة للجلب.")
            time.sleep(2)
            return

    except requests.RequestException as e:
        logger.warning(
            f"Quick check with 'requests' failed: {e}. Proceeding with full Selenium scrape."
        )
        if status_callback:
            status_callback("فشل التحقق الأولي، سيتم إجراء الجلب الكامل...")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during the quick check: {e}. Proceeding with full scrape.",
            exc_info=True,
        )
        if status_callback:
            status_callback(f"حدث خطأ غير متوقع أثناء الفحص الأولي: {e}")

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
                    f"محاولة ({attempt + 1}/{retries}): تم الاتصال، جاري تحليل المحتوى الكامل..."
                )
            page_source = driver.page_source
            verify_page_structure(page_source)
            final_df = parse_cbe_html(page_source, is_quick_check=False)

            if final_df is not None and not final_df.empty:
                if status_callback:
                    status_callback(
                        f"محاولة ({attempt + 1}/{retries}): تم التحليل، جاري حفظ البيانات..."
                    )
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
