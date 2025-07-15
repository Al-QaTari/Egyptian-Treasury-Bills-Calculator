import logging
import os
import sys
import sentry_sdk

# --- بداية الإصلاح ---
# إضافة المسار الحالي للسماح بالاستيراد المحلي
sys.path.append(os.getcwd())

# استيراد وحدات المشروع بعد تعديل المسار
# تم حذف `load_dotenv` لأنها غير مستخدمة هنا
from cbe_scraper import fetch_data_from_cbe  # noqa: E402
from db_manager import get_db_manager  # noqa: E402
from utils import setup_logging  # noqa: E402

# --- نهاية الإصلاح ---


def run_update():
    """
    الدالة الرئيسية التي تقوم بتشغيل عملية تحديث البيانات، بما في ذلك
    الجلب، والمقارنة، والحفظ.
    """
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
        db_manager = get_db_manager()

        logger.info("Fetching latest data from the Central Bank of Egypt website...")

        # We pass the db_manager to the scraper to handle the comparison internally
        new_df = fetch_data_from_cbe(db_manager=db_manager, status_callback=None)

        if new_df is None or new_df.empty:
            # The scraper now handles the logging for "already up-to-date" cases
            # This block will be reached if scraping fails or returns nothing.
            logger.warning("Scraping did not return any new data.")
            return

        logger.info(
            f"Successfully fetched {len(new_df)} new records. Saving to database..."
        )
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
