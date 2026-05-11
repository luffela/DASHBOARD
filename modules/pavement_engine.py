def compute_pavement_thickness(cumulative_esal, cbr, pavement_type):
    if pavement_type == "Flexible":
        k = 10
        n = 4
    else:
        k = 12
        n = 5

    thickness_mm = k * ((cumulative_esal / cbr) ** (1 / n))

    thickness_m = thickness_mm / 1000

    return round(thickness_m, 3), round(thickness_mm, 1)




