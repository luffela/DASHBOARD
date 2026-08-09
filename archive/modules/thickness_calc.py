def compute_pavement_thickness(cumulative_esal, cbr, pavement_type):

    # FLEXIBLE PAVEMENT (CBR-based calibrated model)
    if pavement_type == "Flexible":

        k = 3.92
        n = 3.21

        thickness_mm = k * ((cumulative_esal / cbr) ** (1 / n))

    # RIGID PAVEMENT (slab-based ESAL model)
    elif pavement_type == "Rigid":

        k_r = 5.0
        thickness_mm = k_r * (cumulative_esal ** 0.25)

    else:
        raise ValueError("Invalid pavement type selected")

    thickness_m = thickness_mm / 1000

    return round(thickness_m, 3), round(thickness_mm, 1)


