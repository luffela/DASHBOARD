def compute_aadt(total_traffic_count):
    fh = 1.33
    fd = 3
    fw = 1.4

    aadt = total_traffic_count * fh * fd * fw

    return aadt


