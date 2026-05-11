import math
import streamlit as st

from modules.csv_in import process_uploaded_csv
from modules.aadt_calc import compute_aadt
from modules.esal_calc import compute_cumulative_esal
from modules.pavement_engine import compute_pavement_thickness

# ================= PAGE CONFIG =================

st.set_page_config(
    page_title="PAVEtrack Dashboard",
    layout="wide"
)

# ================= CUSTOM CSS =================

st.markdown("""
<style>

/* App background */
.stApp {
    background-color: #eef2f7;
}

/* Main page spacing */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* Header card */
.header-card {
    background-color: #dfe5ec;
    padding: 25px;
    border-radius: 16px;
    border: 1px solid #c8d0d9;
    text-align: center;
    margin-bottom: 20px;
}

/* Metric cards */
[data-testid="metric-container"] {
    background-color: #f8fafc;
    border: 1px solid #d9e1ea;
    padding: 10px;
    border-radius: 12px;
}

/* Section titles */
.section-title {
    font-size: 22px;
    font-weight: bold;
    color: #2f3e4e;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# ================= HEADER =================

st.markdown("""
<div style='padding:20px; background:#dfe5ec; border-radius:12px; text-align:center;'>
    <h1>PAVEtrack Intelligent Pavement Monitoring Dashboard</h1>
    <p>Traffic Analysis • ESAL Computation • Pavement Thickness Estimation</p>
</div>
""", unsafe_allow_html=True)

# ================= MAIN COLUMNS =================

left, right = st.columns([1, 2], gap="large")

# ================= LEFT PANEL =================

with left:

    with st.container(border=True):

        st.markdown(
            "<div class='section-title'>Input Control Panel</div>",
            unsafe_allow_html=True
        )

        st.markdown("---")

        uploaded_file = st.file_uploader(
            "Upload Consolidated Traffic CSV File",
            type=["csv"]
        )

        pavement_type = st.selectbox(
            "Pavement Type",
            ["Flexible", "Rigid"],
            index=None,
            placeholder="Select Pavement Type"
        )

        # =====================================================
        # CBR INPUT
        # =====================================================

        cbr = st.selectbox(
            "Subgrade CBR",
            [3, 5, 8, 10, 12],
            index=None,
            placeholder="Select CBR Value"
        )

        growth_rate_percent = st.text_input(
            "Annual Growth Rate (%)",
            placeholder="Enter Annual Growth Rate"
        )

        design_life = st.text_input(
            "Design Life (Years)",
            placeholder="Enter Design Life"
        )

        location = st.text_input(
            "Project Location"
        )

# ================= RIGHT PANEL =================

with right:

    with st.container(border=True):

        st.markdown(
            "<div class='section-title'>Traffic Analysis Results</div>",
            unsafe_allow_html=True
        )

        st.markdown("---")

        # =====================================================
        # INPUT VALIDATION
        # =====================================================

        if uploaded_file and (
            pavement_type is None or
            cbr is None or
            growth_rate_percent == "" or
            design_life == ""
        ):

            st.warning(
                "Please complete all engineering input parameters before analysis."
            )

        elif uploaded_file:

            try:

                # =====================================================
                # INPUT CONVERSION
                # =====================================================

                growth_rate_value = float(growth_rate_percent)
                design_life_value = int(design_life)

                # =====================================================
                # CSV PROCESSING
                # =====================================================

                merged_df, total_count, total_esal, num_days = process_uploaded_csv(
                    uploaded_file
                )

                # =====================================================
                # AADT COMPUTATION
                # =====================================================

                aadt = compute_aadt(
                    total_count,
                    num_days
                )

                # =====================================================
                # ESAL COMPUTATION
                # =====================================================

                cumulative_esal, daily_esal = compute_cumulative_esal(
                    total_esal,
                    growth_rate_value / 100,
                    design_life_value
                )

                # =====================================================
                # PAVEMENT THICKNESS
                # =====================================================

                thickness_m, thickness_mm = compute_pavement_thickness(
                    cumulative_esal,
                    cbr,
                    pavement_type
                )

                # =====================================================
                # ROUND TO NEXT 10 mm
                # =====================================================

                recommended_thickness = math.ceil(thickness_mm / 10) * 10

                # =====================================================
                # ENGINEERING RECOMMENDATION
                # =====================================================

                if pavement_type == "Flexible":

                    if recommended_thickness < 150:
                        recommended_thickness = 150

                    if recommended_thickness <= 200:

                        pavement_recommendation = (
                            "Suitable for light-volume flexible pavement roads."
                        )

                    elif recommended_thickness <= 350:

                        pavement_recommendation = (
                            "Recommended for medium-volume arterial roads."
                        )

                    elif recommended_thickness <= 500:

                        pavement_recommendation = (
                            "Recommended for heavily trafficked national roads."
                        )

                    elif recommended_thickness <= 700:

                        pavement_recommendation = (
                            "Suitable for high ESAL freight and highway corridors."
                        )

                    else:

                        pavement_recommendation = (
                            "Suitable for very heavy-duty pavement applications."
                        )

                else:

                    if recommended_thickness < 200:
                        recommended_thickness = 200

                    if recommended_thickness <= 250:

                        pavement_recommendation = (
                            "Suitable for light to medium rigid pavement applications."
                        )

                    elif recommended_thickness <= 350:

                        pavement_recommendation = (
                            "Recommended for major concrete roadway facilities."
                        )

                    else:

                        pavement_recommendation = (
                            "Recommended for high-load rigid pavement structures."
                        )

                # =====================================================
                # SUCCESS MESSAGE
                # =====================================================

                st.success(
                    "Traffic File Processed Successfully"
                )

                # =====================================================
                # METRICS
                # =====================================================

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Location",
                        location if location else "Not Specified"
                    )

                with col2:

                    st.metric(
                        "AADT",
                        f"{aadt:,.2f} veh/day"
                    )

                with col3:

                    st.metric(
                        "Recommended Pavement Thickness",
                        f"{recommended_thickness} mm"
                    )

                # =====================================================
                # ENGINEERING NOTES
                # =====================================================

                st.info(pavement_recommendation)

                st.caption(
                    """
                    Final pavement thickness output is presented as the
                    recommended practical design thickness after rounding
                    to the nearest standard construction value and applying
                    minimum pavement design considerations.
                    """
                )

                st.caption(
                    f"""
                    Daily ESAL: {daily_esal:,.2f} |
                    Cumulative ESAL: {cumulative_esal:,.2f}
                    """
                )

                # =====================================================
                # TRAFFIC DATA TABLE ONLY
                # =====================================================

                st.markdown("### Uploaded Traffic Data")

                st.dataframe(
                    merged_df,
                    use_container_width=True,
                    height=500
                )

            except ValueError:

                st.error(
                    "Annual Growth Rate and Design Life must contain valid numeric values only."
                )

            except FileNotFoundError:

                st.error(
                    "Required processing file not found."
                )