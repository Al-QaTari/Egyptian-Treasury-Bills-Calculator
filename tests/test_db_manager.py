# tests/test_db_manager.py
import sys
import os
import pytest
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db_manager import DatabaseManager
import constants as C

@pytest.fixture
def in_memory_db():
    """إعداد قاعدة بيانات وهمية في الذاكرة لكل اختبار."""
    db_manager = DatabaseManager(db_filename=":memory:")
    return db_manager

def test_save_and_load_latest_data(in_memory_db):
    """🧪 يختبر حفظ وتحميل أحدث البيانات."""
    test_date = datetime.now().strftime("%Y-%m-%d")
    df = pd.DataFrame({
        C.DATE_COLUMN_NAME: [test_date, test_date],
        C.TENOR_COLUMN_NAME: [91, 182],
        C.YIELD_COLUMN_NAME: [25.5, 26.5],
        C.SESSION_DATE_COLUMN_NAME: ["01/01/2025", "01/01/2025"],
    })
    in_memory_db.save_data(df)
    loaded_df, _ = in_memory_db.load_latest_data()
    assert len(loaded_df) == 2
    assert loaded_df[loaded_df[C.TENOR_COLUMN_NAME] == 182][C.YIELD_COLUMN_NAME].iloc[0] == 26.5

def test_get_latest_session_date(in_memory_db):
    """🧪 يختبر جلب آخر تاريخ جلسة."""
    assert in_memory_db.get_latest_session_date() is None, "يجب أن يكون None في البداية"
    df1 = pd.DataFrame({
        C.DATE_COLUMN_NAME: ["2025-01-01"], C.TENOR_COLUMN_NAME: [91],
        C.YIELD_COLUMN_NAME: [25.0], C.SESSION_DATE_COLUMN_NAME: ["01/01/2025"],
    })
    in_memory_db.save_data(df1)
    assert in_memory_db.get_latest_session_date() == "01/01/2025"

    df2 = pd.DataFrame({
        C.DATE_COLUMN_NAME: ["2025-01-02"], C.TENOR_COLUMN_NAME: [91],
        C.YIELD_COLUMN_NAME: [26.0], C.SESSION_DATE_COLUMN_NAME: ["02/01/2025"],
    })
    in_memory_db.save_data(df2)
    assert in_memory_db.get_latest_session_date() == "02/01/2025"

def test_load_all_historical_data(in_memory_db):
    """🧪 يختبر تحميل كل البيانات التاريخية."""
    df1 = pd.DataFrame({C.DATE_COLUMN_NAME: ["2025-01-01"], C.TENOR_COLUMN_NAME: [91], C.YIELD_COLUMN_NAME: [25.0], C.SESSION_DATE_COLUMN_NAME: ["01/01/2025"]})
    df2 = pd.DataFrame({C.DATE_COLUMN_NAME: ["2025-01-02"], C.TENOR_COLUMN_NAME: [182], C.YIELD_COLUMN_NAME: [26.0], C.SESSION_DATE_COLUMN_NAME: ["02/01/2025"]})
    in_memory_db.save_data(df1)
    in_memory_db.save_data(df2)
    historical_df = in_memory_db.load_all_historical_data()
    assert len(historical_df) == 2