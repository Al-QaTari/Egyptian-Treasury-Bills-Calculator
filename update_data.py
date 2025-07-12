# 1. استيراد المكتبات القياسية
import logging
import os
import sys

# 2. استيراد المكتبات الخارجية (Third-party)
from dotenv import load_dotenv
import sentry_sdk

# --- الإعدادات الأولية ---
# تحميل متغيرات البيئة من ملف .env أولاً
load_dotenv()

# تعديل مسار بايثون للسماح باستيراد ملفات المشروع المحلية.
# هذا السطر ضروري ويجب أن يكون قبل استيراد وحدات مشروعك.
sys.path.append(os.getcwd())

# 3. استيراد وحدات المشروع المحلية
from cbe_scraper import fetch_data_from_cbe
from db_manager import get_db_manager
from utils import setup_logging
# --- نهاية كتلة الاستيراد والإعداد ---


def run_update():
    """
    الدالة الرئيسية التي تقوم بتشغيل عملية تحديث البيانات وجلبها.
    """
    # تهيئة Sentry لتتبع الأخطاء
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            environment="production-cron",  # بيئة مختلفة للتمييز
        )

    # إعداد نظام التسجيل (Logging)
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("بدء عملية تحديث البيانات المجدولة...")

    try:
        # الحصول على مدير قاعدة البيانات
        db_manager = get_db_manager()

        # جلب البيانات من البنك المركزي المصري
        fetch_data_from_cbe(db_manager, status_callback=None)

        logger.info("اكتملت عملية تحديث البيانات بنجاح.")

    except Exception as e:
        logger.critical(f"فشل تحديث البيانات المجدول: {e}", exc_info=True)
        # الخروج برمز خطأ (1) لإعلام GitHub Actions بفشل المهمة
        sys.exit(1)
    finally:
        logger.info("=" * 50)


if __name__ == "__main__":
    run_update()
