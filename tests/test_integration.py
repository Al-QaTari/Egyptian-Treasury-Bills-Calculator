# tests/test_integration.py
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cbe_scraper import fetch_data_from_cbe
from db_manager import DatabaseManager
from test_cbe_scraper import MOCK_HTML_CONTENT # نستورد المحتوى الوهمي

@pytest.fixture
def in_memory_db_integration():
    """قاعدة بيانات وهمية لاختبار التكامل."""
    return DatabaseManager(db_filename=":memory:")

def test_full_flow(mocker, in_memory_db_integration):
    """🧪 يختبر التدفق الكامل: الجلب -> الحفظ -> التحميل."""
    # 1. محاكاة طلب الويب الناجح
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.text = MOCK_HTML_CONTENT
    mock_response.content = MOCK_HTML_CONTENT.encode('utf-8')
    mocker.patch('requests.get', return_value=mock_response)
    
    # 2. تشغيل دالة الجلب الرئيسية
    fetch_data_from_cbe(in_memory_db_integration)
    
    # 3. التحقق من أن البيانات حُفظت في قاعدة البيانات الوهمية
    latest_data, _ = in_memory_db_integration.load_latest_data()
    assert latest_data is not None
    assert len(latest_data) == 4
    yield_91 = latest_data[latest_data["tenor"] == 91]["yield"].iloc[0]
    assert yield_91 == 27.558