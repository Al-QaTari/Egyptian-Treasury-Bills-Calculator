# tests/test_integration.py
import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cbe_scraper import parse_cbe_html
from db_manager import DatabaseManager
from .test_cbe_scraper import MOCK_HTML_CONTENT

@pytest.fixture
def db_for_integration():
    """إعداد قاعدة بيانات وهمية في الذاكرة لاختبار التكامل."""
    return DatabaseManager(db_filename=":memory:")

def test_parse_save_load_flow(db_for_integration: DatabaseManager):
    """
    🧪 يختبر التدفق المباشر: تحليل -> حفظ -> تحميل.
    """
    # 1. الخطوة الأولى: تحليل المحتوى الوهمي للحصول على DataFrame
    parsed_df = parse_cbe_html(MOCK_HTML_CONTENT)
    assert parsed_df is not None
    assert len(parsed_df) == 4

    # 2. الخطوة الثانية: حفظ الـ DataFrame الناتج في قاعدة البيانات
    db_for_integration.save_data(parsed_df)

    # 3. الخطوة الثالثة: تحميل أحدث البيانات والتحقق منها
    latest_data, _ = db_for_integration.load_latest_data()
    assert latest_data is not None
    assert len(latest_data) == 4

    # التحقق من قيمة محددة للتأكد من صحة البيانات
    latest_data["tenor"] = pd.to_numeric(latest_data["tenor"])
    yield_val = latest_data[latest_data["tenor"] == 91]["yield"].iloc[0]
    assert yield_val == 27.558
