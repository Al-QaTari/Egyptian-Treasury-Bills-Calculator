# db_manager.py (النسخة النهائية مع دعم التاريخ والوقت)
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
        logger.info(f"Initializing new DB Manager instance for: {self.db_filename}")
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
                logger.info(
                    f"Database '{self.db_filename}' and table '{C.TABLE_NAME}' are ready."
                )
        except sqlite3.Error as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise

    def save_data(self, df: pd.DataFrame) -> None:
        logger.info(f"Saving {len(df)} rows to the database.")
        try:
            with sqlite3.connect(self.db_filename) as conn:
                df.to_sql(
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
        cursor = conn.cursor()
        for data in data_iter:
            placeholders = ", ".join("?" * len(data))
            sql = f"INSERT OR REPLACE INTO {table.name} ({', '.join(keys)}) VALUES ({placeholders})"
            cursor.execute(sql, data)

    @st.cache_data(ttl=60)
    def load_latest_data(
        _self,
    ) -> Tuple[pd.DataFrame, Tuple[Optional[str], Optional[str]]]:
        logger.info("Loading latest data from the database.")
        try:
            with sqlite3.connect(_self.db_filename) as conn:
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
                    last_update_dt_cairo = last_update_dt_utc.tz_localize(
                        "UTC"
                    ).tz_convert(cairo_tz)

                    # --- MODIFICATION: Return date and time as a tuple ---
                    last_update_date = last_update_dt_cairo.strftime("%Y-%m-%d")
                    last_update_time = last_update_dt_cairo.strftime("%I:%M %p")

                    df = df.drop(columns=["max_scrape_date"])
                    return df, (last_update_date, last_update_time)

                return pd.DataFrame(), ("البيانات الأولية", None)
        except Exception as e:
            logger.warning(f"Could not load latest data (table might be empty): {e}")
            return pd.DataFrame(C.INITIAL_DATA), ("البيانات الأولية", None)

    @st.cache_data(ttl=3600)
    def load_all_historical_data(_self) -> pd.DataFrame:
        logger.info("Loading all historical data from the database.")
        try:
            with sqlite3.connect(_self.db_filename) as conn:
                query = f'SELECT * FROM "{C.TABLE_NAME}"'
                df = pd.read_sql_query(query, conn)
                return df.sort_values(by=C.DATE_COLUMN_NAME, ascending=False)
        except Exception:
            return pd.DataFrame()

    def get_latest_session_date(self) -> Optional[str]:
        logger.info("Fetching latest session date from database.")
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
                if result:
                    return result[0]
                return None
        except sqlite3.Error:
            return None
