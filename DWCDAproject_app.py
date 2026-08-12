import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Divine Wisdom CDA - Projects", page_icon="👷", layout="wide")

# Spreadsheet ID + worksheet gid for THIS form's response sheet
# (open the sheet, the ID is the long string in the URL between /d/ and /edit,
# and the gid is the number after gid= when you click the relevant tab)
SPREADSHEET_ID = "1aEucpAJPB6NLWKMmqgmMlmhwGbdy-HIxSnAv-j61aGE"
GID = 1442528727

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

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


@st.cache_resource
def get_gspread_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_data(ttl=30)
def load_data() -> pd.DataFrame:
    client = get_gspread_client()
    sh = client.open_by_key(SPREADSHEET_ID)
    ws = sh.get_worksheet_by_id(GID) if GID else sh.get_worksheet(0)
    records = ws.get_all_records()

    df = pd.DataFrame(records)
    if df.empty:
        return df
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


st.title("👷 Divine Wisdom CDA — Projects")
st.caption("To record a project, use the Google Form link — this page just shows the totals.")

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
