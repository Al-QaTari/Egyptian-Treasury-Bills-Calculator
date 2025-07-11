# tests/test_db_manager.py
import sys
import os
import pytest
import pandas as pd
from datetime import datetime

# لا حاجة لـ streamlit cache clear بعد الآن لأن كل اختبار معزول تمامًا
# import streamlit as st 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import DatabaseManager
import constants as C

# --- START OF FINAL FIX ---
@pytest.fixture
def db(tmp_path):
    """
    إعداد قاعدة بيانات حقيقية ولكن في ملف مؤقت ومنعزل لكل اختبار.
    يتم حذف الملف تلقائيًا بواسطة pytest بعد انتهاء الاختبار.
    """
    # tmp_path هو مسار مؤقت يوفره pytest
    temp_db_file = tmp_path / "test.db"
    db_manager = DatabaseManager(db_filename=temp_db_file)
    yield db_manager
# --- END OF FINAL FIX ---

def test_initial_state(db: DatabaseManager):
    """🧪 يختبر الحالة الأولية لقاعدة البيانات الفارغة."""
    assert db.get_latest_session_date() is None, "يجب أن تكون قاعدة البيانات فارغة في البداية"
    df, msg = db.load_latest_data()
    assert "البيانات الأولية" in msg, "يجب أن تُرجع رسالة البيانات الأولية"
    assert len(db.load_all_historical_data()) == 0, "يجب ألا تحتوي البيانات التاريخية على أي صفوف"

def test_save_and_load_flow(db: DatabaseManager):
    """🧪 يختبر دورة الحياة الكاملة للحفظ والتحميل بشكل متسلسل."""
    # 1. حفظ الدفعة الأولى من البيانات
    date1 = "2025-01-05"
    session_date1 = "05/01/2025"
    df1 = pd.DataFrame({
        C.DATE_COLUMN_NAME: [date1, date1],
        C.TENOR_COLUMN_NAME: [91, 182],
        C.YIELD_COLUMN_NAME: [25.0, 26.0],
        C.SESSION_DATE_COLUMN_NAME: [session_date1, session_date1],
    })
    db.save_data(df1)

    # 2. التحقق من البيانات بعد الحفظ الأول
    latest_df, _ = db.load_latest_data()
    historical_df = db.load_all_historical_data()
    assert len(latest_df) == 2, "بعد الحفظ الأول، يجب أن تكون أحدث البيانات صفين"
    assert len(historical_df) == 2, "بعد الحفظ الأول، يجب أن تكون البيانات التاريخية صفين"
    assert db.get_latest_session_date() == session_date1

    # 3. حفظ الدفعة الثانية من البيانات بتاريخ أحدث
    date2 = "2025-01-12"
    session_date2 = "12/01/2025"
    df2 = pd.DataFrame({
        C.DATE_COLUMN_NAME: [date2],
        C.TENOR_COLUMN_NAME: [364],
        C.YIELD_COLUMN_NAME: [27.0],
        C.SESSION_DATE_COLUMN_NAME: [session_date2],
    })
    db.save_data(df2)

    # 4. التحقق من البيانات بعد الحفظ الثاني
    latest_df_2, _ = db.load_latest_data()
    historical_df_2 = db.load_all_historical_data()
    assert len(latest_df_2) == 1, "بعد الحفظ الثاني، يجب أن تكون أحدث البيانات صفًا واحدًا فقط"
    assert latest_df_2[C.TENOR_COLUMN_NAME].iloc[0] == 364
    assert len(historical_df_2) == 3, "يجب أن تحتوي البيانات التاريخية الآن على 3 صفوف"
    assert db.get_latest_session_date() == session_date2
