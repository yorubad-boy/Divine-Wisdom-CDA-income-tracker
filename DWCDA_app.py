import pandas as pd
import streamlit as st

st.set_page_config(page_title="Divine Wisdom CDA Income Tracker", page_icon="💰", layout="wide")

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Paste the "Publish to web" CSV link from your Google Sheet here (Step 2 in SETUP.md)
CSV_URL = "https://docs.google.com/spreadsheets/d/1E-BWXVd5AzYHnNHEAZZkbq2t8aeA1op7WclV6EScWUw/export?format=csv&gid=1146799343"


# Keywords used to find each column regardless of the exact wording of your
# Google Form questions (e.g. "Amount Paid" or "Amount (Naira)" both match "Amount").
COLUMN_KEYWORDS = {
    "Year": ["year"],
    "Name": ["name"],
    "Month": ["month"],
    "Amount Paid": ["amount", "paid"],
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
        else:
            missing.append(standard_name)

    if missing:
        st.error(
            f"Couldn't find a column for: {', '.join(missing)}.\n\n"
            f"Columns found in your sheet: {list(df.columns)}\n\n"
            "Check that your Google Form questions include these words, or "
            "rename the columns in the sheet to match."
        )
        st.stop()

    df = df.rename(columns=rename_map)[list(COLUMN_KEYWORDS.keys())]
    df["Year"] = df["Year"].astype(str).str.strip()
    df["Name"] = df["Name"].astype(str).str.strip().str.title()
    df["Month"] = df["Month"].astype(str).str.strip().str.title()
    df["Amount Paid"] = pd.to_numeric(df["Amount Paid"], errors="coerce").fillna(0)
    return df


def build_pivot(df: pd.DataFrame, year: str) -> pd.DataFrame:
    year_df = df[df["Year"] == year]
    pivot = year_df.pivot_table(
        index="Name", columns="Month", values="Amount Paid", aggfunc="sum", fill_value=0
    )
    for m in MONTHS:
        if m not in pivot.columns:
            pivot[m] = 0
    pivot = pivot[MONTHS]
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.reset_index()

    grand_total = pivot[MONTHS + ["Total"]].sum(numeric_only=True)
    grand_row = pd.DataFrame([["Grand Total"] + grand_total.tolist()], columns=pivot.columns)
    return pd.concat([pivot, grand_row], ignore_index=True)


st.title("💰 Divine Wisdom CDA Income Tracker")
st.caption("To record a payment, use the Google Form link — this page just shows the totals.")

if CSV_URL == "PASTE_YOUR_PUBLISHED_CSV_LINK_HERE":
    st.warning("Add your published Google Sheet CSV link to `CSV_URL` in app.py — see SETUP.md.")
    st.stop()

df = load_data()

if df.empty:
    st.info("No payments recorded yet.")
    st.stop()

years = sorted(df["Year"].unique(), reverse=True)
selected_year = st.selectbox("Year", years)

pivot = build_pivot(df, selected_year)
st.dataframe(pivot, use_container_width=True, hide_index=True)

year_df = df[df["Year"] == selected_year]
col1, col2 = st.columns(2)

with col1:
    st.caption("Total by Member")
    by_member = year_df.groupby("Name")["Amount Paid"].sum().sort_values(ascending=False)
    st.bar_chart(by_member)

with col2:
    st.caption("Total by Month")
    by_month = year_df.groupby("Month")["Amount Paid"].sum().reindex(MONTHS).fillna(0)
    st.bar_chart(by_month)

grand_total = year_df["Amount Paid"].sum()
st.metric(f"Grand Total ({selected_year})", f"₦{grand_total:,.2f}")

if st.button("Refresh data"):
    load_data.clear()
    st.rerun()
