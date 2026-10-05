# YouTube Analytics Toolkit

Two ways to answer "what content actually works" — pick the one that fits.

## The two tools

### `no-install/` — instant answers, zero setup
A single self-contained HTML file. Double-click it, import your YouTube Studio CSVs, and get reach / retention / engagement / subscriber-source analysis with promoted-vs-organic separation. No Python, no packages, no terminal.

### `streamlit/` — the power version
Full Streamlit app: drag-and-drop CSV imports, auto-detects report types, content intelligence (what to repeat, high-reach/low-conversion flags, title/thumbnail opportunities), side-by-side video compare, enriched CSV export.

```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

## Why two versions
The Streamlit app came first. The single-file version is the same analysis with the setup removed — it covers ~90% of the value with 0% of the friction. Both ship with sample channel data so they run immediately; point them at your own Studio exports for real answers.

## Stack
Vanilla JS (no-install) · Python, Streamlit, pandas, plotly (power version)

Built by [Misael Payan](https://github.com/hyperwumpus) as part of the HyperWumpus creator toolkit.
