def compute_cumulative_esal(total_esal, growth_rate, design_life):
    fh = 1.33
    fd = 10
    fw = 1.0

    daily_esal = total_esal * fh * fd * fw

    cumulative_esal = daily_esal * 365 * (((1 + growth_rate) ** design_life) - 1) / growth_rate

    return cumulative_esal, daily_esal