# tests/test_ui.py
import sys
import os
import pytest
from selenium.webdriver.common.by import By
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- START OF FIX ---
# نستورد الدالة الجاهزة التي تعمل على السيرفرات
from cbe_scraper import setup_driver
# --- END OF FIX ---

# ملاحظة: هذا الاختبار يفترض أن تطبيق ستريم-ليت يعمل بالفعل على الرابط المحلي
STREAMLIT_APP_URL = "http://localhost:8501"

@pytest.mark.ui
def test_app_main_title():
    """🧪 يختبر أن عنوان التطبيق الرئيسي يظهر بشكل صحيح."""
    # نستخدم دالة الإعداد الصحيحة بدلاً من التشغيل المباشر
    driver = setup_driver()
    assert driver is not None, "فشل إعداد المتصفح للاختبار"
    try:
        driver.get(STREAMLIT_APP_URL)
        time.sleep(5) # نزيد الوقت قليلاً لضمان تحميل كل شيء
        
        title_element = driver.find_element(By.TAG_NAME, "h1")
        assert "حاسبة أذون الخزانة" in title_element.text
    finally:
        driver.quit()

@pytest.mark.ui
def test_update_data_button_exists():
    """🧪 يختبر أن زر تحديث البيانات موجود."""
    # نستخدم دالة الإعداد الصحيحة بدلاً من التشغيل المباشر
    driver = setup_driver()
    assert driver is not None, "فشل إعداد المتصفح للاختبار"
    try:
        driver.get(STREAMLIT_APP_URL)
        time.sleep(5)
        
        button_elements = driver.find_elements(By.XPATH, "//button")
        update_button = None
        for btn in button_elements:
            if "تحديث البيانات" in btn.text:
                update_button = btn
                break
        
        assert update_button is not None
        assert update_button.is_displayed()
    finally:
        driver.quit()
