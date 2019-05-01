


def safe_float(value, default=-1.0):
    try:
        return float(value)
    except ValueError:
        return default
