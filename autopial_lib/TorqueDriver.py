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
    "févr.": "02",
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
        torque_dt = torque_dt.replace(m, TORQUE_MONTHS[ m ])

    try:
        dt = datetime.datetime.strptime(torque_dt + "000", "%d-%m-%Y %H:%M:%S.%f")
    except ValueError as e:
        logger.warning(e)
        return None
    return dt


def safe_torque_value(value):
    if value == "-":
        return 0.0

    t = safe_value(value)
    if t != value:
        return t

    dt = parse_date(value)
    if dt is not None:
        return dt

    return None


TORQUE_MAPPER = {
    "Acceleration Sensor(Z axis)(g)": "accel_z",
    "GPS Longitude(°)": "longitude",
    " Longitude": "longitude",
    "GPS Altitude(m)": "altitude",
    " Altitude": "altitude",
    " Acceleration Sensor(Total)(g)": "accel_total",
    "Acceleration Sensor(Total)(g)": "accel_total",
    "Speed (GPS)(km/h)": "gps_speed",
    "GPS Speed (Meters/second)": "gps_speed",
    "GPS Satellites": "number_satellites",
    "Speed (OBD)(km/h)": "obd_speed",
    "Acceleration Sensor(Y axis)(g)": "accel_y",
    "GPS Accuracy(m)": "gps_accuracy",
    "Trip Distance(km)": "trip_distance",
    "Device Time": "datetime",
    " Device Time": "datetime",
    "Acceleration Sensor(X axis)(g)": "accel_x",
    " Acceleration Sensor(X axis)(g)": "accel_x",
    "Engine RPM(rpm)": "rpm",
    "GPS Bearing(°)": "direction",
    "Bearing": "direction",
    " Bearing": "direction",
    "GPS Latitude(°)": "latitude",
    " Latitude": "latitude",
    "Engine Coolant Temperature(°C)": "coolant_temp",
    "Engine Oil Temperature(°C)": "oil_temp"
}


class TorqueFileReader():

    def __init__(self, filepath):
        self.isReady = False
        self.__parsing_results = {
            "missing_fields": set(),
            "not_supported_fields": set()
        }
        self.set_file(filepath)

    def parsing_results(self):
        return self.__parsing_results

    def set_file(self, filepath):
        self.start_date = None
        if not os.path.exists(filepath):
            logger.error("Filepath '{}' does not exist !")
            self.isReady = False
            return None

        self.filepath = filepath
        logger.info("Loading Torque file '{}'".format(filepath))
        self.filesize = float(os.path.getsize(filepath))
        logger.info(" + file size: {} MB".format(round(self.filesize / 1024 / 1024, 4)))

        self.num_lines = sum(1 for line in open(filepath))
        with open(self.filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                line = self.parse_row(row)
                if line is None:
                    logger.error("Unable to parse file {}".format(filepath))
                    return

                for k in TORQUE_MAPPER:
                    if TORQUE_MAPPER[k] not in line:
                        self.__parsing_results[ "missing_fields" ].add(TORQUE_MAPPER[k])
                break

        logger.info(" + missing fields: {}".format(self.__parsing_results[ "missing_fields" ]))
        logger.info(" + not supported fields: {}".format(self.__parsing_results[ "not_supported_fields" ]))
        logger.info(" + start date: {}".format(self.start_date))
        self.isReady = True

    def parse_row(self, row):
        line = {}
        for k in row:
            try:
                key = TORQUE_MAPPER[ k ]
            except KeyError as e:
                # logger.debug("Invalid key: '{}'".format(k))
                self.__parsing_results[ "not_supported_fields" ].add(k)
                continue
            v = row[ k ]
            value = safe_torque_value(v)

            if value is None:
                return None

            if key == "datetime":
                if self.start_date is None:
                    self.start_date = value
                    line[ "timestamp" ] = 0
                else:
                    line[ "timestamp" ] = (value - self.start_date).total_seconds()
            line[ key ] = value

        if "latitude" not in line or \
                "longitude" not in line:
            logger.error("Missing mandatory field 'latitude/longitude'")
            return None

        if line[ "longitude" ] == 0 and line[ "longitude" ] == 0:
            line[ "fix" ] = 0
        else:
            line[ "fix" ] = 1

        return line

    def readline(self):
        if self.filepath is None:
            logger.error("Set valid filepath first !")
            return None

        with open(self.filepath, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                line = self.parse_row(row)
                if line is None:
                    logger.error("Invalid data near line {} ".format(reader.line_num))
                    continue

                if (reader.line_num % 500) == 0:
                    logger.debug(" * parsing line {} / {}".format(reader.line_num, self.num_lines))
                yield line
        return None


if __name__ == '__main__':
    csvfile = TorqueFileReader("torque/trackLog-2016-mai-11_20-23-42.csv")
    for line in csvfile.readline():
        print(line)
