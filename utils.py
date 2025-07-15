import streamlit as st
import os
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def prepare_arabic_text(text: str) -> str:
    """
    This function now does nothing because the system handles Arabic correctly.
    It just returns the text as it is.
    """
    try:
        return str(text)
    except Exception:
        logger.error(f"Could not convert text to string: {text}", exc_info=True)
        return ""


def load_css(file_path: str) -> None:
    """
    Loads an external CSS file into the Streamlit app for custom styling.
    """
    if os.path.exists(file_path):
        logger.debug(f"Loading CSS from {file_path}")
        with open(file_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        logger.warning(f"CSS file not found at path: {file_path}")


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configures the root logger for consistent formatting across all modules.
    Should be called once when the application starts.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[logging.StreamHandler()],
        )
        logger.info("Logging configured successfully.")


def format_currency(value: Optional[float], currency_symbol: str = "جنيه") -> str:
    """
    Formats a numeric value into a standardized currency string.

    Args:
        value (Optional[float]): The number to format.
        currency_symbol (str): The currency symbol or text to append.

    Returns:
        A formatted currency string (e.g., "12,345.68 جنيه").
    """
    if value is None:
        logger.debug("Formatting a None value to default currency string.")
        return f"- {prepare_arabic_text(currency_symbol)}"
    try:
        sign = "-" if value < 0 else ""
        return f"{sign}{abs(value):,.2f} {prepare_arabic_text(currency_symbol)}"
    except (ValueError, TypeError):
        logger.error(f"Could not format value '{value}' as currency.", exc_info=True)
        return str(value)
