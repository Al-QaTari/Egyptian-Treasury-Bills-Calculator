# --- START: كل جمل الاستيراد مجمعة هنا ---
# 1. مكتبات بايثون القياسية
import logging
import sys
import os

# 2. المكتبات الخارجية
import sentry_sdk
from dotenv import load_dotenv

# 3. تعديل المسار (يجب أن يكون قبل استيراد ملفات المشروع)
sys.path.append(".")

# 4. استيراد ملفات المشروع
from db_manager import get_db_manager
from cbe_scraper import fetch_data_from_cbe
from utils import setup_logging
# --- END: كل جمل الاستيراد مجمعة هنا ---

# 5. استدعاء الدالة بعد الانتهاء من كل عمليات الاستيراد
load_dotenv()


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

    # إعداد نظام التسجيل (Logging) باستخدام الدالة المركزية
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Starting scheduled data update process...")

    try:
        # الحصول على مدير قاعدة البيانات عبر الدالة التي تدعم الكاش
        db_manager = get_db_manager()

        # استدعاء دالة الجلب مع تمرير None للكول باك الخاص بالواجهة
        fetch_data_from_cbe(db_manager, status_callback=None)

        logger.info("Data update process completed successfully.")
        logger.info("=" * 50)

    except Exception as e:
        logger.critical(f"Scheduled data update FAILED: {e}", exc_info=True)
        logger.info("=" * 50)
        # الخروج برمز خطأ لإعلام GitHub Actions بفشل المهمة
        sys.exit(1)


if __name__ == "__main__":
    run_update()
