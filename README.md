# PAVE-TRACK Dashboard — canonical structure

**Run this app:** `streamlit run app_dashboard.py`

This is the single, canonical dashboard (also the one deployed at pavetrack.com).
It uses exactly four modules — do not duplicate or rename them:

| Module | Purpose | Key formula |
|---|---|---|
| `modules/csv_in.py` | Reads the grouped 7-day CSV (class rows + `DAY1..DAYn` + `ESAL FACTOR`), sums to `TOTAL COUNT` and `TOTAL ESAL`, returns `num_days` | `TOTAL ESAL = TOTAL COUNT × ESAL FACTOR` |
| `modules/aadt_calc.py` | AADT from total count | `fh=1.33, fd=3, fw=7/num_days` |
| `modules/esal_calc.py` | Cumulative ESAL over design life | growth-series, no extra fh/fd/fw factors |
| `modules/pavement_engine.py` | Pavement thickness | Flexible `k=10,n=4`; Rigid `k=12,n=5` |

`gis_module.py` is a standalone map-generation utility (not imported by the app).

## Input CSV format expected by the app

```
VEHICLE CLASS,ESAL FACTOR,DAY1,DAY2,...,DAY7
Motorcycles,0.0001,300,280,...
Passenger cars,0.0006,220,210,...
```

## /archive — deprecated, kept for reference only

These were removed from the active app on cleanup (July 2026) because they either
crashed or duplicated the modules above with **different** formulas:

- `archive/app.py`, `archive/newapp.py` — old/alternate entry points (newapp.py had a
  4-vs-3 return-value unpack bug).
- `archive/nap.py`, `archive/new.py` — feature variants (nap.py passed an extra
  `num_days` arg to `compute_cumulative_esal` and crashed).
- `archive/modules/csv_processor.py` — reads a pre-summed CSV (different format).
- `archive/modules/aadt_calculator.py` — hardcodes `fw=1.4`.
- `archive/modules/esal_calculator.py` — applies `fh=1.33, fd=10, fw=1.0`.
- `archive/modules/thickness_calc.py` — calibrated constants `k=3.92, n=3.21`.

If you ever need the factored ESAL/thickness formulas, pull them from `archive/`
deliberately — don't leave two versions live at once.

## Note: GIS mapping (thesis objective 4)

`app_dashboard.py` does not currently render the geospatial thickness map. The map
logic lives in `gis_module.py` and the archived `new.py`/`nap.py`. Re-wire it into
`app_dashboard.py` if the map needs to appear in the live dashboard.

## Presentation and local preview

`dashboard_ui.py` renders the shell, empty state, metrics, recommendation, and result tabs. `assets/dashboard.css` controls the responsive layout; `.streamlit/config.toml` sets the native widget theme. [DESIGN.md](DESIGN.md) records the implemented tokens and patterns, with preview specimens in `.impeccable/design.json`. Calculation modules and their existing arguments remain the canonical pipeline above.

From `DASHBOARD`, with Streamlit and pandas installed (verified with Streamlit 1.65):

```powershell
python -m streamlit run app_dashboard.py
```

For the separate review preview at http://127.0.0.1:8502:

```powershell
python -m streamlit run app_dashboard.py --server.address 127.0.0.1 --server.port 8502
```

Upload a consolidated CSV, choose pavement type and CBR, and enter a positive growth percentage and whole-number design life. Results update automatically; project location is optional. The downloadable sample in `assets/sample_traffic.csv` was copied from `videos/compare/sample_thesis_morning.csv` in the workspace. No raster assets are required by the interface.

With the preview running, the browser check requires Playwright and Chromium:

```powershell
python -m pip install playwright
python -m playwright install chromium
python tests/ui_smoke.py
```

The check covers result values, input/error recovery, downloads, and responsive overflow at 390, 768, 1024, 1440, and 1920px. Screenshots and `browser-report.json` are written to `.impeccable/review/`. Recheck native control styles after Streamlit upgrades because the stylesheet targets framework markup.
