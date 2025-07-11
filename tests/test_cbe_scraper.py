# tests/test_cbe_scraper.py
import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cbe_scraper import parse_cbe_html, verify_page_structure
import constants as C

# (نفس المحتوى الوهمي السابق)
MOCK_HTML_CONTENT = """
<html><body>
    <h2>النتائج</h2><table><thead><tr><th>البيان</th><th>182</th><th>364</th></tr></thead><tbody><tr><td>تاريخ الجلسة</td><td>06/07/2025</td><td>06/07/2025</td></tr></tbody></table>
    <p><strong>تفاصيل العروض المقبولة</strong></p><table><tbody><tr><td>متوسط العائد المرجح</td><td>27.192</td><td>25.043</td></tr></tbody></table>
    <h2>النتائج</h2><table><thead><tr><th>البيان</th><th>91</th><th>273</th></tr></thead><tbody><tr><td>تاريخ الجلسة</td><td>07/07/2025</td><td>07/07/2025</td></tr></tbody></table>
    <p><strong>تفاصيل العروض المقبولة</strong></p><table><tbody><tr><td>متوسط العائد المرجح</td><td>27.558</td><td>26.758</td></tr></tbody></table>
</body></html>
"""

def test_html_parser_full_run(Mocker):
    """🧪 يختبر دالة تحليل HTML في وضع الجلب الكامل."""
    parsed_df = parse_cbe_html(MOCK_HTML_CONTENT)
    assert isinstance(parsed_df, pd.DataFrame)
    assert len(parsed_df) == 4
    yield_364 = parsed_df[parsed_df[C.TENOR_COLUMN_NAME] == 364][C.YIELD_COLUMN_NAME].iloc[0]
    assert yield_364 == 25.043

def test_html_parser_quick_check():
    """🧪 يختبر دالة تحليل HTML في وضع التحقق السريع."""
    session_date = parse_cbe_html(MOCK_HTML_CONTENT, is_quick_check=True)
    assert session_date == "06/07/2025"

def test_verify_page_structure_success():
    """🧪 يختبر أن التحقق من هيكل الصفحة ينجح عند وجود كل العلامات."""
    # يجب ألا يطلق أي خطأ
    verify_page_structure(MOCK_HTML_CONTENT)

def test_verify_page_structure_failure():
    """🧪 يختبر أن التحقق من هيكل الصفحة يفشل عند فقدان علامة."""
    invalid_html = MOCK_HTML_CONTENT.replace("متوسط العائد المرجح", "كلمة خاطئة")
    with pytest.raises(RuntimeError) as excinfo:
        verify_page_structure(invalid_html)
    assert "متوسط العائد المرجح" in str(excinfo.value)