import pandas as pd
import streamlit as st

st.set_page_config(page_title="Divine Wisdom CDA - Electricity Connection", page_icon="⚡", layout="wide")

# Paste the CSV export link for THIS form's response sheet
# (Share -> Anyone with the link -> Viewer, then build:
CSV_URL = "https://docs.google.com/spreadsheets/d/1m_XlYYYo_HlCJUtpHWH6OPdffJq3vEwZWYBrrZn2mdE/export?format=csv&gid=303203247"

COLUMN_KEYWORDS = {
    "Timestamp": ["timestamp"],
    "Name": ["name"],
    "Paid": ["payments paid", "paid"],
    "Balance": ["balance"],
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
    keep = [c for c in ["Timestamp", "Name", "Paid", "Balance"] if c in df.columns]
    df = df[keep]

    df["Name"] = df["Name"].astype(str).str.strip().str.title()
    df["Paid"] = pd.to_numeric(df["Paid"], errors="coerce").fillna(0)
    df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce").fillna(0)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    return df


st.title("⚡ Divine Wisdom CDA — Electricity Connection Tracker")
st.caption("To record a payment, use the Google Form link — this page just shows the totals.")

if CSV_URL == "PASTE_YOUR_ELECTRICITY_SHEET_CSV_LINK_HERE":
    st.warning("Add your published Google Sheet CSV link to `CSV_URL` in app.py.")
    st.stop()

df = load_data()

if df.empty:
    st.info("No entries recorded yet.")
    st.stop()

# Latest submission per member = their current balance
if "Timestamp" in df.columns:
    latest = df.sort_values("Timestamp").groupby("Name", as_index=False).last()
else:
    latest = df.groupby("Name", as_index=False).last()

# Running total paid = sum of every submission (covers installments)
total_paid = df.groupby("Name", as_index=False)["Paid"].sum().rename(columns={"Paid": "Total Paid"})

summary = latest[["Name", "Balance"]].merge(total_paid, on="Name")
summary = summary.sort_values("Balance", ascending=False)

st.dataframe(summary, use_container_width=True, hide_index=True)

col1, col2, col3 = st.columns(3)
col1.metric("Total Paid (all members)", f"₦{summary['Total Paid'].sum():,.2f}")
col2.metric("Total Outstanding Balance", f"₦{summary['Balance'].sum():,.2f}")
col3.metric("Members Fully Paid", int((summary["Balance"] <= 0).sum()))

st.caption("Outstanding Balance by Member")
st.bar_chart(summary.set_index("Name")["Balance"])

if st.button("Refresh data"):
    load_data.clear()
    st.rerun()