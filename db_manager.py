import sqlite3
import pandas as pd
import os
import logging
from datetime import datetime
from typing import Tuple, Optional
import streamlit as st
import pytz

import constants as C

logger = logging.getLogger(__name__)


@st.cache_resource
def get_db_manager(db_filename: str = C.DB_FILENAME) -> "DatabaseManager":
    return DatabaseManager(db_filename)


class DatabaseManager:
    def __init__(self, db_filename: str = C.DB_FILENAME):
        self.db_filename = os.path.abspath(db_filename)
        self._init_db()

    def _init_db(self) -> None:
        try:
            with sqlite3.connect(self.db_filename) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"""
                CREATE TABLE IF NOT EXISTS "{C.TABLE_NAME}" (
                    "{C.TENOR_COLUMN_NAME}" INTEGER NOT NULL,
                    "{C.YIELD_COLUMN_NAME}" REAL NOT NULL,
                    "{C.SESSION_DATE_COLUMN_NAME}" TEXT NOT NULL,
                    "{C.DATE_COLUMN_NAME}" DATETIME NOT NULL,
                    PRIMARY KEY ("{C.TENOR_COLUMN_NAME}", "{C.SESSION_DATE_COLUMN_NAME}")
                )
                """
                )
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise

    def save_data(self, df: pd.DataFrame) -> None:
        # --- بداية الإصلاح: تنظيف البيانات قبل الحفظ ---
        df_to_save = df.copy()
        if "session_date_dt" in df_to_save.columns:
            df_to_save = df_to_save.drop(columns=["session_date_dt"])
        # --- نهاية الإصلاح ---

        try:
            with sqlite3.connect(self.db_filename) as conn:
                df_to_save.to_sql(
                    C.TABLE_NAME,
                    conn,
                    if_exists="append",
                    index=False,
                    method=self._upsert,
                )
            logger.info("Data saved successfully.")
        except sqlite3.Error as e:
            logger.error(f"Failed to save data to database: {e}", exc_info=True)

    def _upsert(self, table, conn, keys, data_iter):
        cursor = conn
        for data in data_iter:
            placeholders = ", ".join("?" * len(data))
            sql = f"INSERT OR REPLACE INTO {table.name} ({', '.join(keys)}) VALUES ({placeholders})"
            cursor.execute(sql, data)

    def load_latest_data(
        self,
    ) -> Tuple[pd.DataFrame, Tuple[Optional[str], Optional[str]]]:
        # --- بداية الإصلاح: إعادة الاستعلام الصحيح والأقوى ---
        try:
            with sqlite3.connect(self.db_filename) as conn:
                query = f"""
                WITH RankedData AS (
                    SELECT *,
                           ROW_NUMBER() OVER(PARTITION BY "{C.TENOR_COLUMN_NAME}" ORDER BY "{C.DATE_COLUMN_NAME}" DESC) as rn,
                           MAX("{C.DATE_COLUMN_NAME}") OVER () as max_scrape_date
                    FROM "{C.TABLE_NAME}"
                )
                SELECT "{C.TENOR_COLUMN_NAME}", "{C.YIELD_COLUMN_NAME}", "{C.SESSION_DATE_COLUMN_NAME}", max_scrape_date
                FROM RankedData
                WHERE rn = 1;
                """
                df = pd.read_sql_query(query, conn)

                if not df.empty:
                    last_update_dt_utc = pd.to_datetime(df["max_scrape_date"].iloc[0])
                    cairo_tz = pytz.timezone(C.TIMEZONE)

                    if last_update_dt_utc.tzinfo is None:
                        last_update_dt_cairo = last_update_dt_utc.tz_localize(
                            "UTC"
                        ).tz_convert(cairo_tz)
                    else:
                        last_update_dt_cairo = last_update_dt_utc.tz_convert(cairo_tz)

                    last_update_date = last_update_dt_cairo.strftime("%Y-%m-%d")
                    last_update_time = last_update_dt_cairo.strftime("%I:%M %p")

                    df = df.drop(columns=["max_scrape_date"])
                    return df, (last_update_date, last_update_time)

                return pd.DataFrame(), ("البيانات الأولية", None)
        except Exception as e:
            logger.warning(f"Could not load latest data (table might be empty): {e}")
            return pd.DataFrame(), ("البيانات الأولية", None)

    # --- نهاية الإصلاح ---

    def load_all_historical_data(self) -> pd.DataFrame:
        try:
            with sqlite3.connect(self.db_filename) as conn:
                query = f'SELECT * FROM "{C.TABLE_NAME}"'
                df = pd.read_sql_query(query, conn)
                return df.sort_values(by=C.DATE_COLUMN_NAME, ascending=False)
        except Exception:
            return pd.DataFrame()

    def get_latest_session_date(self) -> Optional[str]:
        try:
            with sqlite3.connect(self.db_filename) as conn:
                query = f"""
                SELECT "{C.SESSION_DATE_COLUMN_NAME}" 
                FROM "{C.TABLE_NAME}"
                ORDER BY 
                    SUBSTR("{C.SESSION_DATE_COLUMN_NAME}", 7, 4) DESC,
                    SUBSTR("{C.SESSION_DATE_COLUMN_NAME}", 4, 2) DESC,
                    SUBSTR("{C.SESSION_DATE_COLUMN_NAME}", 1, 2) DESC
                LIMIT 1;
                """
                result = conn.cursor().execute(query).fetchone()
                return result[0] if result else None
        except sqlite3.Error:
            return None
