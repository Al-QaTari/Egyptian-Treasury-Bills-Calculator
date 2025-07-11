# tests/test_calculations.py
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from calculations import calculate_primary_yield, analyze_secondary_sale

def test_primary_yield_logic_is_self_consistent():
    """🧪 يختبر أن منطق حاسبة العائد الأساسي سليم ومترابط."""
    results = calculate_primary_yield(100000.0, 25.0, 364, 20.0)
    assert results.get("error") is None
    assert results["purchase_price"] + results["gross_return"] == pytest.approx(100000.0)
    assert results["gross_return"] - results["tax_amount"] == pytest.approx(results["net_return"])
    assert results["tax_amount"] == pytest.approx(results["gross_return"] * 0.20)
    assert results["total_payout"] == pytest.approx(100000.0)

def test_primary_yield_invalid_input():
    """🧪 يختبر أن الحاسبة تُرجع خطأ عند إدخال قيم غير صالحة."""
    assert "error" in calculate_primary_yield(0, 25.0, 364, 20.0)
    assert "error" in calculate_primary_yield(100000, 0, 364, 20.0)
    assert "error" in calculate_primary_yield(100000, 25.0, 364, 101)
    assert "error" in calculate_primary_yield(100000, 25.0, 0, 20.0)

def test_secondary_sale_logic_with_profit():
    """🧪 يختبر منطق البيع الثانوي في حالة تحقيق ربح."""
    results = analyze_secondary_sale(100000, 25.0, 364, 90, 23.0, 20.0)
    assert results.get("error") is None
    assert results["original_purchase_price"] + results["gross_profit"] == pytest.approx(results["sale_price"])
    assert results["gross_profit"] - results["tax_amount"] == pytest.approx(results["net_profit"])
    assert results["tax_amount"] > 0

def test_secondary_sale_logic_with_loss():
    """🧪 يختبر منطق البيع الثانوي في حالة تحقيق خسارة."""
    results = analyze_secondary_sale(100000, 25.0, 364, 90, 35.0, 20.0)
    assert results.get("error") is None
    assert results["original_purchase_price"] + results["gross_profit"] == pytest.approx(results["sale_price"])
    assert results["gross_profit"] == pytest.approx(results["net_profit"])
    assert results["tax_amount"] == 0

def test_secondary_sale_invalid_days():
    """🧪 يختبر الحالة التي تكون فيها أيام الاحتفاظ غير صالحة."""
    assert "error" in analyze_secondary_sale(100000, 25.0, 91, 91, 28.0, 20.0)
    assert "error" in analyze_secondary_sale(100000, 25.0, 91, 92, 28.0, 20.0)
