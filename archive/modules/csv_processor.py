import pandas as pd

def process_uploaded_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)

    total_count = df["Total Count"].sum()
    total_esal = df["Total ESAL"].sum()

    return df, total_count, total_esal