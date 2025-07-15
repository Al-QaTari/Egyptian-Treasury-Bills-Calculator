import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
import pandas as pd
import sentry_sdk

# --- الإعدادات الأولية ---
load_dotenv()
sys.path.append(os.getcwd())

from cbe_scraper import fetch_data_from_cbe
from db_manager import get_db_manager  # Make sure this is imported
from utils import setup_logging
import constants as C


def run_update():
    """
    الدالة الرئيسية التي تقوم بتشغيل عملية تحديث البيانات، بما في ذلك
    الجلب، والمقارنة، والحفظ.
    """
    # ... (Sentry and logging setup remains the same)
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            environment="production-cron",
        )

    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Starting scheduled data update process...")

    try:
        # --- FIX: Initialize the db_manager first ---
        db_manager = get_db_manager()

        logger.info("Fetching latest data from the Central Bank of Egypt website...")

        # --- FIX: Pass the created db_manager object ---
        new_df = fetch_data_from_cbe(db_manager=db_manager, status_callback=None)

        if new_df is None or new_df.empty:
            logger.warning(
                "No data was found at the source. The page may be unavailable."
            )
            return

        # ... (The rest of the file remains the same) ...

        logger.info(f"Successfully fetched {len(new_df)} records from the source.")

        # The comparison logic is now correctly handled inside the scraper,
        # so we just need to save the result.
        logger.info("New auction data found. Saving to the database...")
        db_manager.save_data(new_df)
        logger.info("Data update process completed successfully.")

    except Exception as e:
        logger.critical(
            f"Scheduled data update failed unexpectedly: {e}", exc_info=True
        )
        if sentry_dsn:
            sentry_sdk.capture_exception(e)
        sys.exit(1)
    finally:
        logger.info("=" * 50)


if __name__ == "__main__":
    run_update()
