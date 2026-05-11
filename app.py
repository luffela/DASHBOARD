import streamlit as st

from modules.csv_processor import process_uploaded_csv
from modules.aadt_calculator import compute_aadt
from modules.esal_calculator import compute_cumulative_esal
from modules.pavement_engine import compute_pavement_thickness

st.set_page_config(page_title="PAVEtrack Dashboard", layout="wide")

st.title("PAVEtrack Dashboard")

left, right = st.columns([1, 2])

with left:
    st.header("Input Panel")

    uploaded_file = st.file_uploader(
        "Upload Consolidated 7-Day CSV File",
        type=["csv"]
    )

    pavement_type = st.selectbox("Pavement Type", ["Flexible", "Rigid"])

    cbr = st.selectbox("Subgrade CBR", [3, 5, 8, 10, 12])

    growth_rate_percent = st.number_input("Annual Growth Rate (%)", min_value=1.0, value=5.0)

    design_life = st.number_input("Design Life (Years)", min_value=1, value=20)

    location = st.text_input("Project Location")

with right:
    st.header("Results")

    if uploaded_file:
        merged_df, total_count, total_esal = process_uploaded_csv(uploaded_file)

        aadt = compute_aadt(total_count)

        cumulative_esal, daily_esal = compute_cumulative_esal(
            total_esal,
            growth_rate_percent / 100,
            design_life
        )

        thickness_m, thickness_mm = compute_pavement_thickness(cumulative_esal, cbr, pavement_type)

        st.success("Traffic File Processed Successfully")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Location", location if location else "Not Specified")

        with col2:
            st.metric("AADT", f"{aadt:,.2f} veh/day")

        with col3:
            st.metric("Pavement Thickness", f"{thickness_mm} mm")

        st.subheader("Uploaded Traffic Data")
        st.dataframe(merged_df)