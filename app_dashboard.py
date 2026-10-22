import math

import streamlit as st

from modules.csv_in import process_uploaded_csv
from modules.aadt_calc import compute_aadt
from modules.esal_calc import compute_cumulative_esal
from modules.pavement_engine import compute_pavement_thickness
from dashboard_ui import (
    ASSETS, render_empty_state, render_panel_heading,
    render_results, render_results_heading, render_shell,
)


st.set_page_config(page_title="PAVEtrack Dashboard", layout="wide")
render_shell()

with st.container(key="workspace"):
    left, right = st.columns([1, 2.65], gap="large")

    with left:
        with st.container(key="project_setup"):
            render_panel_heading()
            uploaded_file = st.file_uploader(
                "Upload Consolidated Traffic CSV File", type=["csv"],
            )
            with st.expander("Sample CSV"):
                st.download_button(
                    "Download sample CSV", (ASSETS / "sample_traffic.csv").read_bytes(),
                    file_name="sample_traffic.csv", mime="text/csv",
                    icon=":material/download:",
                )

            pavement_type = st.selectbox(
                "Pavement Type", ["Flexible", "Rigid"], index=None,
                placeholder="Select Pavement Type",
            )
            cbr = st.selectbox(
                "Subgrade CBR", [3, 5, 8, 10, 12], index=None,
                placeholder="Select CBR Value",
            )
            growth_rate_percent = st.text_input(
                "Annual Growth Rate (%)", placeholder="Enter Annual Growth Rate",
            )
            design_life = st.text_input("Design Life (Years)", placeholder="Enter Design Life")
            location = st.text_input("Project Location")

    with right:
        incomplete = (
            pavement_type is None or cbr is None
            or growth_rate_percent == "" or design_life == ""
        )
        if not uploaded_file or incomplete:
            render_results_heading(location)
            render_empty_state(has_file=bool(uploaded_file))
        else:
            try:
                # Validate user input in the UI; the calculation modules are unchanged.
                try:
                    growth_rate_value = float(growth_rate_percent)
                    design_life_value = int(design_life)
                except ValueError:
                    raise ValueError(
                        "Enter a numeric annual growth rate and a whole number of design years."
                    ) from None
                if not math.isfinite(growth_rate_value) or growth_rate_value <= 0:
                    raise ValueError("Annual Growth Rate must be greater than 0% for this model.")
                if design_life_value <= 0:
                    raise ValueError("Design Life must be at least 1 year.")

                # Existing processing and engineering pipeline.
                merged_df, total_count, total_esal, num_days = process_uploaded_csv(uploaded_file)
                if num_days == 0:
                    raise ValueError("Add at least one daily count column to your CSV, such as DAY1.")
                if "VEHICLE CLASS" not in merged_df.columns:
                    raise ValueError("Your CSV needs a VEHICLE CLASS column. Use the sample CSV as a guide.")
                if merged_df.empty:
                    raise ValueError("Your CSV has no traffic rows. Add vehicle classes and their daily counts.")

                aadt = compute_aadt(total_count, num_days)
                cumulative_esal, daily_esal = compute_cumulative_esal(
                    total_esal, growth_rate_value / 100, design_life_value
                )
                thickness_m, thickness_mm = compute_pavement_thickness(
                    cumulative_esal, cbr, pavement_type
                )

                # Preserve the original rounding, minimums, and recommendations.
                recommended_thickness = math.ceil(thickness_mm / 10) * 10
                if pavement_type == "Flexible":
                    if recommended_thickness < 150:
                        recommended_thickness = 150
                    if recommended_thickness <= 200:
                        pavement_recommendation = "Suitable for light-volume flexible pavement roads."
                    elif recommended_thickness <= 350:
                        pavement_recommendation = "Recommended for medium-volume arterial roads."
                    elif recommended_thickness <= 500:
                        pavement_recommendation = "Recommended for heavily trafficked national roads."
                    elif recommended_thickness <= 700:
                        pavement_recommendation = "Suitable for high ESAL freight and highway corridors."
                    else:
                        pavement_recommendation = "Suitable for very heavy-duty pavement applications."
                else:
                    if recommended_thickness < 200:
                        recommended_thickness = 200
                    if recommended_thickness <= 250:
                        pavement_recommendation = "Suitable for light to medium rigid pavement applications."
                    elif recommended_thickness <= 350:
                        pavement_recommendation = "Recommended for major concrete roadway facilities."
                    else:
                        pavement_recommendation = "Recommended for high-load rigid pavement structures."

                render_results(
                    merged_df=merged_df, total_count=total_count, num_days=num_days,
                    aadt=aadt, daily_esal=daily_esal, cumulative_esal=cumulative_esal,
                    recommended_thickness=recommended_thickness, pavement_type=pavement_type,
                    pavement_recommendation=pavement_recommendation, cbr=cbr,
                    growth_rate_value=growth_rate_value, design_life_value=design_life_value,
                    thickness_mm=thickness_mm, location=location,
                )
            except (ValueError, OverflowError) as error:
                render_results_heading(location)
                st.error(str(error) if isinstance(error, ValueError) else
                         "These inputs exceed the model’s numeric range. Check the growth rate and design life.")
            except KeyError:
                render_results_heading(location)
                st.error("Your CSV is missing a required column. Include VEHICLE CLASS, ESAL FACTOR, and DAY1…DAYn. You can download a sample in Input Control Panel.")
            except (TypeError, ZeroDivisionError):
                render_results_heading(location)
                st.error("Check your CSV: ESAL factors and daily counts must be numeric, with at least one monitoring day.")
            except FileNotFoundError:
                render_results_heading(location)
                st.error("Required processing file not found.")
