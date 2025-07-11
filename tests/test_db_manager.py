# tests/test_db_manager.py
import sys
import os
import pytest
import pandas as pd
from datetime import datetime
import streamlit as st # <-- تم إضافة هذا السطر

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import DatabaseManager
import constants as C

@pytest.fixture
def db():
    """إعداد قاعدة بيانات وهمية مع مسح الكاش قبل كل اختبار."""
    # --- START OF FIX ---
    # مسح الكاش لضمان عدم تسرب البيانات بين الاختبارات
    st.cache_data.clear()
    st.cache_resource.clear()
    # --- END OF FIX ---
    
    db_manager = DatabaseManager(db_filename=":memory:")
    yield db_manager

def test_initial_state(db: DatabaseManager):
    """🧪 يختبر الحالة الأولية لقاعدة البيانات الفارغة."""
    assert db.get_latest_session_date() is None, "يجب أن تكون قاعدة البيانات فارغة في البداية"
    df, msg = db.load_latest_data()
    assert "البيانات الأولية" in msg
    assert len(db.load_all_historical_data()) == 0

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
    assert len(latest_df) == 2
    assert len(historical_df) == 2
    assert db.get_latest_session_date() == session_date1

    # 3. حفظ الدفعة الثانية من البيانات بتاريخ أحدث
    date2 = "2025-01-12"
    session_date2 = "12/01/2025"
    df2 = pd.DataFrame({
        C.DATE_COLUMN_NAME: [date2], C.TENOR_COLUMN_NAME: [364],
        C.YIELD_COLUMN_NAME: [27.0], C.SESSION_DATE_COLUMN_NAME: [session_date2],
    })
    db.save_data(df2)

    # 4. التحقق من البيانات بعد الحفظ الثاني
    latest_df_2, _ = db.load_latest_data()
    historical_df_2 = db.load_all_historical_data()
    assert len(latest_df_2) == 1, "يجب أن تحتوي أحدث البيانات على صف واحد فقط"
    assert latest_df_2[C.TENOR_COLUMN_NAME].iloc[0] == 364
    assert len(historical_df_2) == 3, "يجب أن تحتوي البيانات التاريخية على 3 صفوف"
    assert db.get_latest_session_date() == session_date2
