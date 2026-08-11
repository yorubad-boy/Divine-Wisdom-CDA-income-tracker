import pandas as pd
import streamlit as st

st.set_page_config(page_title="Divine Wisdom CDA Income Tracker", page_icon="💰", layout="wide")

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Your published Google Sheet CSV export link
CSV_URL = "https://docs.google.com/spreadsheets/d/1jQlLFJeimhaKhThr0v6fgvJNdHJkYeonO7zAxI5EfL8/export?format=csv&gid=494362929"

# Your form has one column per month (Year, Name, January, February, ..., December)
# rather than a single "Month" dropdown — this matches column headers by keyword.
COLUMN_KEYWORDS = {
    "Year": ["year"],
    "Name": ["name"],
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

    # Match each month name to its column (e.g. "January" question -> "January" column)
    month_col_map = {}
    missing_months = []
    for month in MONTHS:
        found = find_column(df.columns, [month.lower()])
        if found:
            month_col_map[found] = month
        else:
            missing_months.append(month)

    if missing or missing_months:
        st.error(
            f"Couldn't find columns for: {', '.join(missing + missing_months)}.\n\n"
            f"Columns found in your sheet: {list(df.columns)}\n\n"
            "Check that your Google Form questions include these words, or "
            "rename the columns in the sheet to match."
        )
        st.stop()

    df = df.rename(columns={**rename_map, **month_col_map})
    df = df[["Year", "Name"] + MONTHS]

    df["Year"] = df["Year"].astype(str).str.strip()
    df["Name"] = df["Name"].astype(str).str.strip().str.title()
    for month in MONTHS:
        df[month] = pd.to_numeric(df[month], errors="coerce").fillna(0)

    return df


def build_pivot(df: pd.DataFrame, year: str) -> pd.DataFrame:
    year_df = df[df["Year"] == year]
    # Sum in case the same person submitted more than once for the same year
    pivot = year_df.groupby("Name", as_index=False)[MONTHS].sum()
    pivot["Total"] = pivot[MONTHS].sum(axis=1)

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

year_df = df[df["Year"] == selected_year].copy()
year_df["Total"] = year_df[MONTHS].sum(axis=1)

col1, col2 = st.columns(2)

with col1:
    st.caption("Total by Member")
    by_member = year_df.groupby("Name")["Total"].sum().sort_values(ascending=False)
    st.bar_chart(by_member)

with col2:
    st.caption("Total by Month")
    by_month = year_df[MONTHS].sum()
    st.bar_chart(by_month)

grand_total = year_df["Total"].sum()
st.metric(f"Grand Total ({selected_year})", f"₦{grand_total:,.2f}")

if st.button("Refresh data"):
    load_data.clear()
    st.rerun()