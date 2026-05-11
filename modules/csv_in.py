import pandas as pd

def process_uploaded_csv(uploaded_file):

    df = pd.read_csv(uploaded_file)

    # Detect all DAY columns automatically
    day_columns = [col for col in df.columns if "DAY" in col.upper()]

    # Number of monitoring days
    num_days = len(day_columns)

    # Total traffic count across all days
    total_count = df[day_columns].sum().sum()

    # Compute total count per vehicle class
    df["TOTAL COUNT"] = df[day_columns].sum(axis=1)

    # Compute total ESAL per vehicle class
    df["TOTAL ESAL"] = (
        df["TOTAL COUNT"] * df["ESAL FACTOR"]
    )

    # Total ESAL across all vehicle classes
    total_esal = df["TOTAL ESAL"].sum()

    return df, total_count, total_esal, num_days


