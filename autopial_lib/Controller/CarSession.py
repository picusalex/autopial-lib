import copy
import datetime
import hashlib
import logging

from haversine import haversine
from opencage.geocoder import OpenCageGeocode, RateLimitExceededError

key = '17d3fa34ccb04d42b9292c191ae4d0b8'
geocoder = OpenCageGeocode(key)

class CarSession:
    VALID_FIELDS = dict(timestamp=-1.0, latitude=0.0, longitude=0.0, fix=False, altitude=-1.0, gps_speed=-1.0,
                        direction=-1.0, rpm=-1.0, obd_speed=-1.0, coolant_temp=-1.0, oil_temp=-1.0, accel_x=0.0,
                        accel_y=0.0, accel_z=0.0)

    def __init__(self, origin, db_driver, logger=None):
        if logger is None:
            self.__logger = logging.getLogger(__name__)
        else:
            self.__logger = logger
        self.__db_driver = db_driver

        self.__origin = origin
        self.__session_uid = hashlib.md5(origin.encode('utf-8')).hexdigest()
        self.create()

        self.__prev_pos = (0.0, 0.0)
        self.__distance = 0.0
        self.__first_address = None
        self.__start_date = None


    def create(self):
        self.__logger.info("Creating session {} from {}".format(self.__session_uid, self.__origin))
        self.__db_driver.create_session(self.__session_uid, self.__origin)

    def recreate(self):
        self.__logger.info("Re-creating session {} from {}".format(self.__session_uid, self.__origin))
        self.__db_driver.delete_session(self.__session_uid)
        self.create()

    def start(self, start_date=datetime.datetime.now()):
        self.__logger.info("Starting session {} at {}".format(self.__session_uid, start_date))
        self.__start_date = start_date
        self.__db_driver.update_session(self.__session_uid, start_date=start_date, status="ONGOING")

    def stop(self):
        self.__logger.info("Stopping session {}".format(self.__session_uid))
        self._terminate_session()
        self.print_session()

    def _terminate_session(self):
        car_datas = self.__db_driver.get_cardata(self.__session_uid)

        start_point_lat = car_datas[0]["latitude"]
        start_point_lon = car_datas[0]["longitude"]
        first_address = self.__first_address

        end_point_lat = car_datas[-1]["latitude"]
        end_point_lon = car_datas[-1]["longitude"]

        duration = car_datas[-1]["timestamp"]
        distance = car_datas[-1]["distance"]

        end_date = self.__start_date + datetime.timedelta(seconds=duration)

        last_address = None
        min_lat = min_lon = 9999
        max_lat = max_lon = -9999
        for t in reversed(car_datas):
            if t[ "latitude" ]:
                if t[ "latitude" ] > max_lat: max_lat = t[ "latitude" ]
                if t[ "latitude" ] < min_lat: min_lat = t[ "latitude" ]

            if t[ "longitude" ]:
                if t[ "longitude" ] > max_lon: max_lon = t[ "longitude" ]
                if t[ "longitude" ] < min_lon: min_lon = t[ "longitude" ]

            if t["latitude"] and t["longitude"] and last_address is None:
                last_address = self.address(t["latitude"], t["longitude"])

        max_distance = haversine((min_lat, min_lon), (max_lat, max_lon))
        if max_distance < 1:
            self.__logger.warning("Deleting session with too small geographical dilution ({} km)".format(round(max_distance,3)))
            self.__db_driver.delete_session(self.__session_uid)
            return

        kwargs = {
            "start_point_lat": start_point_lat,
            "start_point_lon": start_point_lon,
            "first_address": first_address,
            "end_point_lat": end_point_lat,
            "end_point_lon": end_point_lon,
            "last_address": last_address,
            "duration": duration,
            "distance": distance,
            "end_date": end_date,
            "status": "TERMINATED",
        }
        self.__db_driver.update_session(self.__session_uid, **kwargs)

    def address(self, latitude, longitude):
        try:
            results = geocoder.reverse_geocode(latitude, longitude, language='fr', no_annotation='1')
            if results and len(results):
                return results[0]['formatted']
        except RateLimitExceededError as ex:
            self.__logger.warning("OpenCageData rate limit exceeded !")
            return None

    def new_car_data(self, latitude, longitude, **kwargs):
        valid_dict = dict()

        for field in self.VALID_FIELDS:
            if field in kwargs:
                valid_dict[field] = kwargs[field]
            else:
                valid_dict[field] = self.VALID_FIELDS[field]

        valid_dict["latitude"] = latitude
        valid_dict["longitude"] = longitude


        if self.__prev_pos[0] != 0.0 and self.__prev_pos[1] != 0.0 and latitude and longitude:
            self.__distance += haversine(self.__prev_pos, (latitude, longitude))

        if self.__first_address is None and latitude != 0 and longitude != 0:
            self.__first_address = self.address(latitude, longitude)

        self.__prev_pos = (latitude, longitude)

        if latitude != 0.0 and longitude != 0.0 and "fix" not in valid_dict:
            valid_dict["fix"] = True
        else:
            valid_dict["fix"] = False

        valid_dict["session_uid"] = self.__session_uid
        valid_dict["distance"] = self.__distance
        #print (valid_dict)
        self.__db_driver.add_car_data(**valid_dict)

    def print_session(self):
        autopial_session = self.__db_driver.get_session(session_uid=self.__session_uid)
        if autopial_session is None:
            return

        self.__logger.info("########################################################")
        self.__logger.info("Session '{}' terminated".format(autopial_session.id))
        self.__logger.info(" + start date   : {}".format(autopial_session.start_date))
        self.__logger.info(" + start point  : {},{}".format(autopial_session.start_point_lat,autopial_session.start_point_lon))
        self.__logger.info(" + first address: {}".format(autopial_session.first_address))
        self.__logger.info(" + end date     : {}".format(autopial_session.end_date))
        self.__logger.info(" + end point    : {},{}".format(autopial_session.end_point_lat, autopial_session.end_point_lon))
        self.__logger.info(" + last address : {}".format(autopial_session.last_address))
        self.__logger.info(" + origin       : {}".format(autopial_session.origin))
        self.__logger.info(" + status       : {}".format(autopial_session.status))
        self.__logger.info(" + duration     : {}".format(autopial_session.duration))
        self.__logger.info(" + distance     : {}".format(autopial_session.distance))
        self.__logger.info("########################################################")