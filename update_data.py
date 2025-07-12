import logging
import sys
import os
import sentry_sdk
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env (للبيئة المحلية)
load_dotenv()

# هذا السطر يضمن أن السكربت يمكنه العثور على باقي ملفات المشروع
# عند تشغيله من GitHub Actions
sys.path.append(".")

# نستورد الدوال المحسنة من ملفات مشروعنا
from db_manager import get_db_manager
from cbe_scraper import fetch_data_from_cbe
from utils import setup_logging


def run_update():
    """
    الدالة الرئيسية التي تقوم بتشغيل عملية تحديث البيانات.
    """
    # --- START: Sentry Initialization ---
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0,
            environment="production-cron", # بيئة مختلفة للتمييز
        )
    # --- END: Sentry Initialization ---

    # 1. إعداد نظام التسجيل (Logging) باستخدام الدالة المركزية
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Starting scheduled data update process...")

    try:
        # 2. الحصول على مدير قاعدة البيانات عبر الدالة التي تدعم الكاش
        db_manager = get_db_manager()

        # 3. استدعاء دالة الجلب مع تمرير None للكول باك الخاص بالواجهة
        fetch_data_from_cbe(db_manager, status_callback=None)

        logger.info("Data update process completed successfully.")
        logger.info("=" * 50)

    except Exception as e:
        logger.critical(f"Scheduled data update FAILED: {e}", exc_info=True)
        logger.info("=" * 50)
        # 4. الخروج برمز خطأ لإعلام GitHub Actions بفشل المهمة
        sys.exit(1)


if __name__ == "__main__":
    run_update()
