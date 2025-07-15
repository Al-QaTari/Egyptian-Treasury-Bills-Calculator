# tests/test_db_manager.py (النسخة النهائية والمصححة)
import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import DatabaseManager
import constants as C


@pytest.fixture
def db(tmp_path):
    """
    إعداد قاعدة بيانات حقيقية ولكن في ملف مؤقت ومنعزل لكل اختبار.
    """
    temp_db_file = tmp_path / "test.db"
    db_manager = DatabaseManager(db_filename=temp_db_file)
    yield db_manager


def test_initial_state(db: DatabaseManager):
    """🧪 يختبر الحالة الأولية لقاعدة البيانات الفارغة."""
    assert db.get_latest_session_date() is None
    df, msg = db.load_latest_data()
    assert "البيانات الأولية" in msg
    assert len(db.load_all_historical_data()) == 0


def test_save_and_load_flow(db: DatabaseManager):
    """🧪 يختبر دورة الحياة الكاملة للحفظ والتحميل بشكل متسلسل."""
    # 1. حفظ الدفعة الأولى من البيانات
    date1 = "2025-01-05"
    session_date1 = "05/01/2025"
    df1 = pd.DataFrame(
        {
            C.DATE_COLUMN_NAME: [date1, date1],
            C.TENOR_COLUMN_NAME: [91, 182],
            C.YIELD_COLUMN_NAME: [25.0, 26.0],
            C.SESSION_DATE_COLUMN_NAME: [session_date1, session_date1],
        }
    )
    db.save_data(df1)

    # 2. التحقق من البيانات بعد الحفظ الأول
    latest_df, _ = db.load_latest_data()
    historical_df = db.load_all_historical_data()
    assert len(latest_df) == 2
    assert len(historical_df) == 2
    assert db.get_latest_session_date() == session_date1

    # 3. حفظ الدفعة الثانية من البيانات بتاريخ أحدث
    date2 = "2025-01-12"
    session_date2 = "12/01/2025"
    df2 = pd.DataFrame(
        {
            C.DATE_COLUMN_NAME: [date2],
            C.TENOR_COLUMN_NAME: [364],
            C.YIELD_COLUMN_NAME: [27.0],
            C.SESSION_DATE_COLUMN_NAME: [session_date2],
        }
    )
    db.save_data(df2)

    # 4. التحقق من البيانات بعد الحفظ الثاني
    latest_df_2, _ = db.load_latest_data()
    historical_df_2 = db.load_all_historical_data()

    # --- بداية الإصلاح: تعديل منطق التحقق ليتوافق مع سلوك التطبيق الصحيح ---
    # الدالة يجب أن ترجع أحدث صف لكل أجل، لذا النتيجة ستكون 3 صفوف
    assert len(latest_df_2) == 3, "يجب أن يتم إرجاع أحدث صف لكل أجل من الآجال الثلاثة"
    
    # نتأكد من أن العدد الإجمالي للصفوف التاريخية صحيح
    assert len(historical_df_2) == 3, "يجب أن تحتوي البيانات التاريخية الآن على 3 صفوف"
    
    # نتأكد من أن تاريخ أحدث جلسة هو الصحيح
    assert db.get_latest_session_date() == session_date2
    # --- نهاية الإصلاح ---
