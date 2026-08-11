import pandas as pd
import streamlit as st

st.set_page_config(page_title="Divine Wisdom CDA - Expenditures", page_icon="📒", layout="wide")

# Paste the CSV export link for THIS form's response sheet
# (Open the linked response Google Sheet -> Share -> Anyone with the link -> Viewer, then build:
# https://docs.google.com/spreadsheets/d/<SHEET_ID>/export?format=csv&gid=<GID>)
CSV_URL = "https://docs.google.com/spreadsheets/d/10kY8WzW8TmS2vHzsv03Il5zIJCKPAxV0nzEzH_1nta0/export?format=csv&gid=1042344473"

COLUMN_KEYWORDS = {
    "Timestamp": ["timestamp"],
    "Items": ["items"],
    "Description": ["description"],
    "Amount": ["amount"],
}


def find_column(columns, keywords):
    for col in columns:
        low = col.lower()
        if any(kw in low for kw in keywords):
            return col
    return None


@st.cache_data(ttl=30)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip() for c in df.columns]

    rename_map = {}
    missing = []
    for standard_name, keywords in COLUMN_KEYWORDS.items():
        found = find_column(df.columns, keywords)
        if found:
            rename_map[found] = standard_name
        elif standard_name != "Timestamp":  # Timestamp is auto-added by Forms; not required
            missing.append(standard_name)

    if missing:
        st.error(
            f"Couldn't find a column for: {', '.join(missing)}.\n\n"
            f"Columns found in your sheet: {list(df.columns)}\n\n"
            "Check that your Google Form questions include these words, or "
            "rename the columns in the sheet to match."
        )
        st.stop()

    df = df.rename(columns=rename_map)
    keep = [c for c in ["Timestamp", "Items", "Description", "Amount"] if c in df.columns]
    df = df[keep]

    df["Items"] = df["Items"].astype(str).str.strip()
    df["Description"] = df["Description"].astype(str).str.strip()
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    return df


st.title("📒 Divine Wisdom CDA — Expenditures")
st.caption("To record an expenditure, use the Google Form link — this page just shows the totals.")

if CSV_URL == "PASTE_YOUR_EXPENDITURES_SHEET_CSV_LINK_HERE":
    st.warning("Add your published Google Sheet CSV link to `CSV_URL` in app.py.")
    st.stop()

df = load_data()

if df.empty:
    st.info("No entries recorded yet.")
    st.stop()

if "Timestamp" in df.columns:
    df = df.sort_values("Timestamp", ascending=False)

st.dataframe(df, use_container_width=True, hide_index=True)

col1, col2, col3 = st.columns(3)
col1.metric("Total Expenditure", f"₦{df['Amount'].sum():,.2f}")
col2.metric("Number of Entries", len(df))
col3.metric("Average Amount", f"₦{df['Amount'].mean():,.2f}")

st.caption("Total Amount by Item")
by_item = df.groupby("Items", as_index=True)["Amount"].sum().sort_values(ascending=False)
st.bar_chart(by_item)

if st.button("Refresh data"):
    load_data.clear()
    st.rerun()