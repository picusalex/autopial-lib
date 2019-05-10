


def safe_float(value, default=-1.0):
    try:
        return float(value)
    except ValueError:
        return default

def safe_integer(value, default=0):
    try:
        return int(value)
    except ValueError:
        return default

def safe_value(value):
    try:
        return float(value)
    except ValueError:
        pass

    try:
        return int(value)
    except ValueError:
        pass

    return value