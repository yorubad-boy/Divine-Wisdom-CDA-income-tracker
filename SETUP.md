# Divine Wisdom CDA Income Tracker — Simple Setup

No Google Cloud, no API keys, no secrets file. Just a Google Form for collectors
to submit payments, and a small Streamlit page that shows the dashboard.

## Step 1 — Create the Google Form
1. Go to [forms.google.com](https://forms.google.com) → new form, e.g.
   "CDA Payment Form".
2. Add 4 questions:
   - **Year** — Short answer (e.g. "2026")
   - **Name** — Short answer
   - **Month** — Dropdown, with January–December as options
   - **Amount Paid** — Short answer, set validation to "Number"
3. Click **Responses** tab → the green Sheets icon → **Create Spreadsheet**.
   This makes a Google Sheet that auto-fills every time someone submits the form.

That's it for data entry. Send the Form link to your collectors — Google Forms
already works great on any phone, no app needed.

## Step 2 — Publish the response sheet so the dashboard can read it
1. Open the Google Sheet created in Step 1.
2. **File → Share → Publish to web**.
3. Under "Link", choose the response tab (usually "Form Responses 1") and
   select **Comma-separated values (.csv)** as the format.
4. Click **Publish** → copy the link it gives you.

This makes the data readable (not editable) by anyone with the link — no
sign-in required, which is why the dashboard needs zero credentials.

## Step 3 — Point the app at your data
Open `app.py` and replace this line near the top:
```python
CSV_URL = "PASTE_YOUR_PUBLISHED_CSV_LINK_HERE"
```
with the link you copied in Step 2.

## Step 4 — Run it
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Step 5 — Deploy (optional, so collectors/exco can view from anywhere)
Push this folder to GitHub, then deploy on
[share.streamlit.io](https://share.streamlit.io) pointing at `app.py` — same as
your other Streamlit apps. No secrets to configure this time.

## How it works day-to-day
- Collectors submit payments via the **Google Form link** on their phones.
- Anyone who wants to see totals opens the **Streamlit dashboard link**.
- If two names get typed slightly differently (e.g. "john doe" vs "John Doe"),
  the app automatically title-cases names before totaling, so minor
  capitalization differences won't split one person into two rows. Big
  misspellings still won't match — worth a quick glance at the Name column in
  the Google Sheet now and then.
