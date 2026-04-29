# -*- coding: utf-8 -*-
"""
gsheets_config.py
-----------------
Central Google Sheets connection module.
Replaces all SQLite (sqlite3) logic.

Setup:
  Option A (Streamlit Cloud / secrets.toml):
      [gcp_service_account] block + SPREADSHEET_ID in secrets.toml

  Option B (local dev):
      Place credentials.json in project root and set SPREADSHEET_ID below.
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# ── Change this to your actual Google Spreadsheet ID ──────────────────────────
# You can also set it in .streamlit/secrets.toml as:  SPREADSHEET_ID = "..."
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Sheet (tab) names inside your spreadsheet
SHEET_ADMISSIONS    = "admissions"
SHEET_FEE_PAYMENTS  = "fee_payments"
SHEET_DEPOSITS      = "deposits"
SHEET_BRAVE_STUDENTS = "brave_students"

# Expected header rows for each sheet
HEADERS = {
    SHEET_ADMISSIONS: [
        "id", "admission_date", "nav", "janmatarikh", "ling", "mobile",
        "palak_mobile", "email", "patta", "tayari", "ssc_gun", "hsc_gun",
        "graduation_padvi", "graduation_gun", "post_graduation_padvi",
        "post_graduation_gun", "photo_data", "sign_data"
    ],
    SHEET_FEE_PAYMENTS: [
        "id", "student_id", "student_name", "payment_date", "month", "year",
        "amount_paid", "payment_type", "remarks", "recorded_by", "created_at"
    ],
    SHEET_DEPOSITS: [
        "id", "student_id", "student_name", "deposit_amount", "deposit_date",
        "deposit_required", "remarks", "recorded_by", "created_at"
    ],
    SHEET_BRAVE_STUDENTS: [
        "id", "name", "position", "photo_url", "display_order", "created_at"
    ],
}


# ── Connection (cached so we only authenticate once per session) ───────────────

@st.cache_resource
def get_gspread_client():
    """Return an authenticated gspread client."""
    try:
        # --- Streamlit secrets (preferred) ---
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    except (KeyError, FileNotFoundError):
        # --- Fallback: local credentials.json ---
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

    return gspread.authorize(creds)


def get_spreadsheet():
    """Return the Spreadsheet object."""
    client = get_gspread_client()
    spreadsheet_id = st.secrets.get("SPREADSHEET_ID", SPREADSHEET_ID)
    return client.open_by_key(spreadsheet_id)


def get_sheet(sheet_name: str):
    """
    Return a worksheet by name.
    If it doesn't exist, create it with the correct headers.
    """
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=sheet_name, rows="1000", cols="30")

    # Ensure headers exist
    existing = ws.row_values(1)
    if not existing:
        ws.append_row(HEADERS[sheet_name])

    return ws


# ── Generic helpers ────────────────────────────────────────────────────────────

def sheet_to_df(sheet_name: str) -> pd.DataFrame:
    """Read an entire sheet into a DataFrame (headers from row 1)."""
    ws = get_sheet(sheet_name)
    records = ws.get_all_records()          # list of dicts keyed by header
    return pd.DataFrame(records)


def next_id(sheet_name: str) -> int:
    """Auto-increment: return max(id)+1 or 1 if empty."""
    df = sheet_to_df(sheet_name)
    if df.empty or "id" not in df.columns or df["id"].dropna().empty:
        return 1
    return int(pd.to_numeric(df["id"], errors="coerce").max()) + 1


def append_row(sheet_name: str, row: list):
    """Append one row to a sheet."""
    ws = get_sheet(sheet_name)
    ws.append_row(row, value_input_option="USER_ENTERED")


def delete_row_by_id(sheet_name: str, record_id: int) -> bool:
    """Delete the first row whose 'id' column matches record_id."""
    ws = get_sheet(sheet_name)
    try:
        cell = ws.find(str(record_id), in_column=1)
        if cell:
            ws.delete_rows(cell.row)
            return True
    except Exception as e:
        st.error(f"Delete error: {e}")
    return False


def update_row_by_id(sheet_name: str, record_id: int, col_index: int, value):
    """Update a single cell in the row whose id matches record_id."""
    ws = get_sheet(sheet_name)
    try:
        cell = ws.find(str(record_id), in_column=1)
        if cell:
            ws.update_cell(cell.row, col_index, value)
            return True
    except Exception as e:
        st.error(f"Update error: {e}")
    return False


def update_brave_student_row(record_id: int, name: str, position: str, photo_url: str) -> bool:
    """Update name, position, photo_url for a brave_student row."""
    ws = get_sheet(SHEET_BRAVE_STUDENTS)
    headers = ws.row_values(1)
    try:
        cell = ws.find(str(record_id), in_column=1)
        if not cell:
            return False
        name_col     = headers.index("name")     + 1
        pos_col      = headers.index("position") + 1
        photo_col    = headers.index("photo_url") + 1
        ws.update_cell(cell.row, name_col,  name)
        ws.update_cell(cell.row, pos_col,   position)
        ws.update_cell(cell.row, photo_col, photo_url)
        return True
    except Exception as e:
        st.error(f"Update error: {e}")
        return False