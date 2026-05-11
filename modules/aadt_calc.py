def compute_aadt(total_traffic_count, num_days):

    fh = 1.33
    fd = 3
    fw = 7 / num_days

    aadt = total_traffic_count * fh * fd * fw

    return round(aadt, 2)