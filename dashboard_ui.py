"""Presentation helpers. Engineering calculations live in the existing modules."""

from html import escape
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"


def icon(name, size=20):
    paths = {
        "road": '<path d="M7 3 4 21M17 3l3 18M12 3v4m0 3v4m0 3v4"/>',
        "sliders": '<path d="M4 7h7m4 0h5M4 17h3m4 0h9"/><circle cx="13" cy="7" r="2"/><circle cx="9" cy="17" r="2"/>',
        "pin": '<path d="M20 10c0 6-8 11-8 11S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
        "check": '<path d="m5 12 4 4L19 6"/>',
        "layers": '<path d="m12 3 10 5-10 5L2 8l10-5Zm-10 9 10 5 10-5M2 16l10 5 10-5"/>',
        "refresh": '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M6 6a8 8 0 0 1 13 3M5 15a8 8 0 0 0 13 3"/>',
        "chart": '<path d="M4 4v16h16M8 15v-4m5 4V7m5 8v-6"/>',
        "file": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M8 13h8M8 17h5"/>',
    }
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def render_shell():
    html(f'<style>{(ASSETS / "dashboard.css").read_text(encoding="utf-8")}</style>')
    html('''<div class="pave-intro"><h1>PAVEtrack Intelligent Pavement Monitoring Dashboard</h1>
        <p>Traffic Analysis · ESAL Computation · Pavement Thickness Estimation</p></div>''')


def render_panel_heading():
    html(f'<div class="pave-panel-title">{icon("sliders")}<h2>Input Control Panel</h2></div>')


def render_results_heading(location, ready=False):
    status = (f'<span class="pave-status" role="status">{icon("check", 14)}'
              'Traffic File Processed Successfully</span>') if ready else ""
    location_markup = (f'<div class="pave-location">{icon("pin", 14)}'
                       f'Location: {escape(location or "Not Specified")}</div>') if ready or location else ""
    html(f'''<div class="pave-results-heading"><div><h2>Traffic Analysis Results</h2>
        {location_markup}</div>{status}</div>''')


def render_empty_state(has_file=False):
    if has_file:
        st.warning("Please complete all engineering input parameters before analysis.")
    else:
        html(f'''<div class="pave-empty"><div class="pave-empty-icon">{icon("chart", 44)}</div>
            <p>Upload Consolidated Traffic CSV File</p></div>''')


def render_results(*, merged_df, total_count, num_days, aadt, daily_esal,
                   cumulative_esal, recommended_thickness, pavement_type,
                   pavement_recommendation, cbr, growth_rate_value,
                   design_life_value, thickness_mm, location):
    render_results_heading(location, ready=True)
    metrics = (("AADT", f"{aadt:,.2f}", "veh/day"),
               ("Daily ESAL", f"{daily_esal:,.2f}", ""),
               ("Cumulative ESAL", f"{cumulative_esal:,.2f}", ""))
    html('<div class="pave-metrics">' + ''.join(
        f'<div class="pave-metric"><div class="pave-metric-label">{label}</div>'
        f'<div class="pave-metric-value">{value}</div>'
        + (f'<div class="pave-metric-unit">{unit}</div>' if unit else '') + '</div>'
        for label, value, unit in metrics) + '</div>')
    html(f'''<div class="pave-recommendation"><div><h3>Recommended Pavement Thickness</h3>
        <div class="pave-thickness">{recommended_thickness:,.0f} <span>mm</span></div></div>
        <div class="pave-recommendation-copy"><span class="pave-material">{icon("layers", 17)} {escape(pavement_type)} pavement</span>
        <p>{escape(pavement_recommendation)}</p></div></div>''')
    html('<p class="pave-design-note">Rounded up to the next 10 mm and adjusted to the model’s minimum design thickness.</p>')

    overview, traffic_data, calculations = st.tabs(["Traffic overview", "Uploaded Traffic Data", "Calculation details"])
    with overview:
        render_traffic_chart(merged_df, total_count, num_days)
    with traffic_data:
        st.dataframe(merged_df, width="stretch", hide_index=True,
                     height=min(500, 38 + len(merged_df) * 36), row_height=36,
                     column_config={"TOTAL ESAL": st.column_config.NumberColumn(format="%.4f"),
                                    "ESAL FACTOR": st.column_config.NumberColumn(format="%.4f")})
        st.download_button("Download processed CSV", merged_df.to_csv(index=False).encode("utf-8"),
                           file_name="pavetrack_traffic_analysis.csv", mime="text/csv",
                           icon=":material/download:")
    with calculations:
        details = (("Pavement type", pavement_type), ("Subgrade CBR", str(cbr)),
                   ("Annual growth rate", f"{growth_rate_value:g}%"),
                   ("Design life", f"{design_life_value} years"),
                   ("Monitoring period", f"{num_days} days"),
                   ("Calculated thickness", f"{thickness_mm:,.1f} mm"),
                   ("Minimum design thickness", "150 mm" if pavement_type == "Flexible" else "200 mm"),
                   ("Recommended thickness", f"{recommended_thickness:,.0f} mm"))
        html('<dl class="pave-detail-list">' + ''.join(
            f'<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'
            for label, value in details) + '</dl>')


def render_traffic_chart(df, total_count, num_days):
    rows = []
    maximum = float(df["TOTAL COUNT"].max()) if len(df) else 0
    for _, row in df.iterrows():
        count = float(row["TOTAL COUNT"])
        width = count / maximum * 100 if maximum > 0 else 0
        share = count / total_count * 100 if total_count > 0 else 0
        rows.append(f'''<div class="pave-bar-row"><span class="pave-bar-label">{escape(str(row["VEHICLE CLASS"]))}</span>
            <div class="pave-bar-track" aria-hidden="true"><div class="pave-bar-fill" style="width:{width:.4f}%"></div></div>
            <span class="pave-bar-count">{count:,.0f}</span><span class="pave-bar-share">{share:.1f}%</span></div>''')
    html(f'''<div class="pave-chart"><div class="pave-chart-heading"><h3>Traffic composition</h3>
        <span class="pave-chart-key"><span class="pave-key-dot"></span> Vehicle count</span></div>
        <div>{"".join(rows)}</div></div>''')
