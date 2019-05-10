import csv
import datetime
import logging

import os

from autopial_lib.utils import safe_value

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
steam_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(asctime)s|%(levelname)08s | %(message)s')
steam_handler.setFormatter(stream_formatter)
logger.addHandler(steam_handler)

TORQUE_MONTHS = {
    "janv.": "01",
    "févr": "02",
    "mars": "03",
    "avr.": "04",
    "mai": "05",
    "juin": "06",
    "juil.": "07",
    "août.": "08",
    "sept.": "09",
    "oct.": "10",
    "nov.": "11",
    "déc.": "12",
}
def parse_date(torque_dt):
    for m in TORQUE_MONTHS:
        torque_dt = torque_dt.replace(m, TORQUE_MONTHS[m])

    dt  = datetime.datetime.strptime(torque_dt+"000", "%d-%m-%Y %H:%M:%S.%f")
    return dt


TORQUE_MAPPER = {
    "Acceleration Sensor(Z axis)(g)": "accel_z",
    "GPS Longitude(°)": "longitude",
    "GPS Altitude(m)": "altitude",
    " Acceleration Sensor(Total)(g)": "accel_total",
    "Speed (GPS)(km/h)": "speed_gps",
    "GPS Satellites": "number_satellites",
    "Speed (OBD)(km/h)": "speed_obd",
    "Acceleration Sensor(Y axis)(g)": "accel_y",
    "GPS Accuracy(m)": "gps_accuracy",
    "Trip Distance(km)": "trip_distance",
    "Device Time": "datetime",
    "Acceleration Sensor(X axis)(g)": "accel_x",
    "Engine RPM(rpm)": "rpm",
    "GPS Bearing(°)": "orientation",
    "GPS Latitude(°)": "latitude",
    "Engine Coolant Temperature(°C)": "coolant_temp",
}

class TorqueFileReader():
    def __init__(self, filepath):
        self.set_file(filepath)

    def set_file(self, filepath):
        if not os.path.exists(filepath):
            logger.error("Filepath '{}' does not exist !")
            return None

        self.filepath = filepath
        self.num_lines = sum(1 for line in open(filepath))

        self.start_date = None

    def readline(self):
        if self.filepath is None:
            logger.error("Set valid filepath first !")
            return None

        _lines = 0
        with open(self.filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                line = {}
                _lines = _lines + 1
                for k in row:
                    try:
                        key = TORQUE_MAPPER[k]
                    except KeyError as e:
                        if _lines == 1 or _lines == self.num_lines-1:
                            logger.warning("No mapping found for key: '{}'".format(k))
                        continue
                    value = row[k]

                    if key == "datetime":
                        if _lines == 1:
                            self.start_date = parse_date(value)
                            line["timestamp"] = 0
                        else:
                            dt = parse_date(value)
                            line["timestamp"] = (dt - self.start_date).total_seconds()
                    else:
                        line[key] = safe_value(value)

                if (_lines%100) == 0:
                    logger.debug(" * parsing line {} / {}".format(_lines, self.num_lines))

                yield line
        return None

if __name__ == '__main__':
    csvfile = TorqueFileReader("torque/trackLog-2016-mai-11_20-23-42.csv")
    for line in csvfile.readline():
        print(line)