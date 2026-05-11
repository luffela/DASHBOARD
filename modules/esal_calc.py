def compute_cumulative_esal(total_esal, growth_rate, design_life):

    daily_esal = total_esal

    cumulative_esal = (
        daily_esal
        * 365
        * (((1 + growth_rate) ** design_life) - 1)
        / growth_rate
    )

    return round(cumulative_esal, 2), round(daily_esal, 2)



