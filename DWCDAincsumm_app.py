import pandas as pd
import streamlit as st

st.set_page_config(page_title="Divine Wisdom CDA - Income Summary", page_icon="🏘️", layout="wide")

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

# ---------------------------------------------------------------------------
# Source sheets — paste each form's response-sheet CSV export link here.
# (Share -> Anyone with the link -> Viewer, then:
# https://docs.google.com/spreadsheets/d/<SHEET_ID>/export?format=csv&gid=<GID>)
# ---------------------------------------------------------------------------
SOURCES = {
    "Development Fee": {
        "url": "https://docs.google.com/spreadsheets/d/1jQlLFJeimhaKhThr0v6fgvJNdHJkYeonO7zAxI5EfL8/export?format=csv",
        "type": "monthly",
    },
    "Monthly Minutes": {
        "url": "https://docs.google.com/spreadsheets/d/1b3-M1xPw1AChLFFOQZ-0fnNlXie5AwuwLFUauvWrOhw/export?format=csv",
        "type": "monthly",
    },
    "Electricity Connection": {
        "url": "https://docs.google.com/spreadsheets/d/1m_XlYYYo_HlCJUtpHWH6OPdffJq3vEwZWYBrrZn2mdE/export?format=csv",
        "type": "payment",
    },
    "Projects": {
        "url": "https://docs.google.com/spreadsheets/d/1aEucpAJPB6NLWKMmqgmMlmhwGbdy-HIxSnAv-j61aGE/export?format=csv&gid=1442528727",
        "type": "payment",
    },
}


def find_column(columns, keywords):
    for col in columns:
        low = col.lower()
        if any(kw in low for kw in keywords):
            return col
    return None


@st.cache_data(ttl=30)
def load_monthly_sheet(url: str) -> pd.DataFrame:
    """Sheets shaped like: Timestamp | Year | Name | Jan..Dec"""
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]

    keywords = {
        "Timestamp": ["timestamp"],
        "Year": ["year"],
        "Name": ["name"],
        **{m: [m.lower()] for m in MONTHS},
    }
    rename_map = {}
    for standard, kws in keywords.items():
        found = find_column(df.columns, kws)
        if found:
            rename_map[found] = standard
    df = df.rename(columns=rename_map)

    if "Name" not in df.columns:
        return pd.DataFrame(columns=["Timestamp", "Year", "Name"] + MONTHS + ["Total"])

    df = df[df["Name"].notna()].copy()
    df["Name"] = df["Name"].astype(str).str.strip().str.title()

    for m in MONTHS:
        if m not in df.columns:
            df[m] = 0
        df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0)

    if "Year" in df.columns:
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    df["Total"] = df[MONTHS].sum(axis=1)
    keep = [c for c in ["Timestamp", "Year", "Name"] + MONTHS + ["Total"] if c in df.columns]
    return df[keep]


@st.cache_data(ttl=30)
def load_payment_sheet(url: str) -> pd.DataFrame:
    """Sheets shaped like: Timestamp | Name | Payments Paid | Balance"""
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]

    keywords = {
        "Timestamp": ["timestamp"],
        "Name": ["name"],
        "Paid": ["payments paid", "paid"],
        "Balance": ["balance"],
    }
    rename_map = {}
    for standard, kws in keywords.items():
        found = find_column(df.columns, kws)
        if found:
            rename_map[found] = standard
    df = df.rename(columns=rename_map)

    if "Name" not in df.columns:
        return pd.DataFrame(columns=["Timestamp", "Name", "Paid", "Balance"])

    df = df[df["Name"].notna()].copy()
    df["Name"] = df["Name"].astype(str).str.strip().str.title()
    df["Paid"] = pd.to_numeric(df.get("Paid", 0), errors="coerce").fillna(0)
    df["Balance"] = pd.to_numeric(df.get("Balance", 0), errors="coerce").fillna(0)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")

    keep = [c for c in ["Timestamp", "Name", "Paid", "Balance"] if c in df.columns]
    return df[keep]


def load_all():
    data = {}
    for label, cfg in SOURCES.items():
        loader = load_monthly_sheet if cfg["type"] == "monthly" else load_payment_sheet
        try:
            data[label] = loader(cfg["url"])
        except Exception as e:
            st.error(f"Couldn't load '{label}': {e}")
            data[label] = pd.DataFrame()
    return data


st.title("🏘️ Divine Wisdom CDA — Income Summary")
st.caption("To record a new entry, use the relevant Google Form. This page just shows the totals, pulled live from each response sheet.")

data = load_all()

if st.button("🔄 Refresh all data"):
    load_monthly_sheet.clear()
    load_payment_sheet.clear()
    st.rerun()

# ---------------------------------------------------------------------------
# Overview tab — combined totals across all four sheets
# ---------------------------------------------------------------------------
tab_names = ["Overview"] + list(SOURCES.keys())
tabs = st.tabs(tab_names)

with tabs[0]:
    monthly_income = sum(data[label]["Total"].sum() for label in SOURCES if SOURCES[label]["type"] == "monthly" and not data[label].empty)
    payments_paid = sum(data[label]["Paid"].sum() for label in SOURCES if SOURCES[label]["type"] == "payment" and not data[label].empty)
    outstanding_balance = sum(data[label]["Balance"].sum() for label in SOURCES if SOURCES[label]["type"] == "payment" and not data[label].empty)
    grand_total = monthly_income + payments_paid

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Development Fee + Monthly Minutes", f"₦{monthly_income:,.2f}")
    col2.metric("Electricity + Projects Paid", f"₦{payments_paid:,.2f}")
    col3.metric("Outstanding Balance", f"₦{outstanding_balance:,.2f}")
    col4.metric("Grand Total Collected", f"₦{grand_total:,.2f}")

    st.divider()
    st.subheader("Collected by Source")
    by_source = pd.DataFrame({
        "Source": list(SOURCES.keys()),
        "Amount": [
            data[label]["Total"].sum() if SOURCES[label]["type"] == "monthly" and not data[label].empty
            else (data[label]["Paid"].sum() if not data[label].empty else 0)
            for label in SOURCES
        ],
    }).set_index("Source")
    st.bar_chart(by_source)

    st.subheader("Total Contribution by Member (all sources combined)")
    per_member = pd.Series(dtype=float)
    for label, cfg in SOURCES.items():
        df = data[label]
        if df.empty:
            continue
        if cfg["type"] == "monthly":
            s = df.groupby("Name")["Total"].sum()
        else:
            s = df.groupby("Name")["Paid"].sum()
        per_member = per_member.add(s, fill_value=0)
    per_member = per_member.sort_values(ascending=False)
    if not per_member.empty:
        st.bar_chart(per_member)
    else:
        st.info("No entries recorded yet across any sheet.")

# ---------------------------------------------------------------------------
# Individual tabs — one per sheet
# ---------------------------------------------------------------------------
for label, tab in zip(SOURCES.keys(), tabs[1:]):
    with tab:
        df = data[label]
        cfg = SOURCES[label]

        if df.empty:
            st.info("No entries recorded yet.")
            continue

        if cfg["type"] == "monthly":
            years = sorted(df["Year"].dropna().unique().tolist()) if "Year" in df.columns else []
            if years:
                selected_years = st.multiselect("Year", years, default=years, key=f"years_{label}")
                df = df[df["Year"].isin(selected_years)]

            summary = df.groupby("Name", as_index=False)["Total"].sum().rename(columns={"Total": "Total Income"})
            summary = summary.sort_values("Total Income", ascending=False)
            st.dataframe(summary, use_container_width=True, hide_index=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total", f"₦{summary['Total Income'].sum():,.2f}")
            c2.metric("Entries", len(df))
            c3.metric("Members", summary["Name"].nunique())

            st.caption("By Member")
            st.bar_chart(summary.set_index("Name")["Total Income"])

            st.caption("By Month")
            monthly = df[MONTHS].sum()
            monthly.index = pd.CategoricalIndex(monthly.index, categories=MONTHS, ordered=True)
            st.bar_chart(monthly.sort_index())

        else:  # payment type
            if "Timestamp" in df.columns:
                latest = df.sort_values("Timestamp").groupby("Name", as_index=False).last()
            else:
                latest = df.groupby("Name", as_index=False).last()

            total_paid = df.groupby("Name", as_index=False)["Paid"].sum().rename(columns={"Paid": "Total Paid"})
            summary = latest[["Name", "Balance"]].merge(total_paid, on="Name")
            summary = summary.sort_values("Balance", ascending=False)
            st.dataframe(summary, use_container_width=True, hide_index=True)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Paid", f"₦{summary['Total Paid'].sum():,.2f}")
            c2.metric("Outstanding Balance", f"₦{summary['Balance'].sum():,.2f}")
            c3.metric("Members Fully Paid", int((summary["Balance"] <= 0).sum()))

            st.caption("Outstanding Balance by Member")
            st.bar_chart(summary.set_index("Name")["Balance"])

        with st.expander("Raw data"):
            st.dataframe(df, use_container_width=True, hide_index=True)