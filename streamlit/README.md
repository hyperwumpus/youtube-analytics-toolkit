# HyperWumpus YouTube Analytics

A local Streamlit dashboard tailored to the YouTube Studio exports used in the HyperWumpus channel audit.

## What it does

- Loads the current bundled HyperWumpus snapshot automatically.
- Accepts fresh YouTube Studio CSV exports by drag-and-drop.
- Auto-detects detailed Content, New/Returning Viewers, Subscription Status, Subscription Source, daily Views, and daily Subscribers reports.
- Separates known promoted videos from organic-analysis leaderboards.
- Shows reach, retention, engagement, subscriber conversion, audience quality, subscriber sources, and rolling trends.
- Surfaces content worth repeating, high-reach/low-conversion posts, and title/thumbnail packaging opportunities.
- Lets you compare videos side-by-side and export an enriched analysis CSV.

## Run it

### Windows
1. Install Python 3.10+ from python.org if needed.
2. Double-click `run_windows.bat`.
3. A browser window should open automatically.

### macOS
1. Install Python 3.10+ if needed.
2. In Terminal, `cd` into this folder.
3. Run `bash run_mac.command`.

### Manual

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Updating your data

You do **not** need to rename future YouTube Studio exports. Open the app and drag the CSV files into the uploader in the sidebar. The app identifies report types from their columns.

Useful reports:
- Detailed Content report with Subscribers gained/lost, retention, likes, comments, shares, impressions, CTR, etc.
- New and Returning Viewers
- Subscription Status
- Subscription Source
- Daily Views totals
- Daily Subscribers totals

## Important interpretation note

The current HyperWumpus snapshot shows that YouTube advertising accounts for most historical gross subscriber acquisition. Therefore the app deliberately treats raw subscriber counts on known promoted videos cautiously and excludes known promoted videos from the default **organic opportunity** analysis.

The "Known promoted" tag is based on the promotion history supplied during the audit. It is a useful flag, not a perfect separation of organic and paid views on a video.

## Privacy

This version does not connect to YouTube or send data anywhere. It reads local CSV files in your browser session through Streamlit.
