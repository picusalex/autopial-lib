
import datetime
import hashlib
import logging

from haversine import haversine
from opencage.geocoder import OpenCageGeocode, RateLimitExceededError

key = '17d3fa34ccb04d42b9292c191ae4d0b8'
geocoder = OpenCageGeocode(key)

class CarController:
    def __init__(self, db_driver, logger=None):
        if logger is None:
            self.__logger = logging.getLogger(__name__)
        else:
            self.__logger = logger
        self.__db_driver = db_driver

    def __uid_from_origin(self, origin):
        return hashlib.md5(origin.encode('utf-8')).hexdigest()

    def create(self, origin):
        session_uid = self.__uid_from_origin(origin)
        self.__logger.info("Creating session {} from {}".format(session_uid, origin))
        self.__db_driver.create_session(session_uid, origin)
        return self.get(session_uid)

    def recreate(self, origin):
        session_uid = self.__uid_from_origin(origin)
        self.__logger.info("Re-creating session {} from {}".format(session_uid, origin))
        self.__db_driver.delete_session(session_uid)
        return self.create(origin)

    def get(self, session_uid):
        mongo_dict = self.__db_driver.get_session(session_uid)
        if mongo_dict is None:
            raise Exception("Session {} does not exist".format(session_uid))

        session = CarSession(session_uid, db_driver=self.__db_driver, logger=self.__logger)
        session.fromDict(**mongo_dict)

        return session

    def get_all(self):
        mongo_dicts = self.__db_driver.get_all_sessions()
        sessions = []

        for mongo_dict in mongo_dicts:
            session = CarSession(mongo_dict["uid"], db_driver=self.__db_driver, logger=self.__logger)
            session.fromDict(**mongo_dict)
            sessions.append(session)

        return sessions

    def get_car_data(self, uid, offset=0, limit=None):
        car_datas = self.__db_driver.get_car_data(uid, offset, limit)
        return car_datas

class CarSession:
    STATUS_NOTSTARTED = "NOT_STARTED"
    STATUS_ONGOING = "ON_GOING"
    STATUS_TERMINATED = "TERMINATED"

    DATA_VALID_FIELDS = dict(timestamp=-1.0, latitude=0.0, longitude=0.0, fix=False, altitude=-1.0, gps_speed=-1.0,
                             direction=-1.0, rpm=-1.0, obd_speed=-1.0, coolant_temp=-1.0, oil_temp=-1.0, accel_x=0.0,
                             accel_y=0.0, accel_z=0.0)

    def __init__(self, session_uid, db_driver, logger=None):
        if logger is None:
            self.__logger = logging.getLogger(__name__)
        else:
            self.__logger = logger
        self.__db_driver = db_driver

        self.uid = session_uid

        self.origin = None
        self.status = self.STATUS_NOTSTARTED

        self.start_date = None
        self.start_point = ( 0,0 )
        self.end_date = None
        self.end_point = ( 0, 0 )

        self.first_address = None
        self.last_address = None

        self.distance = -1.0
        self.duration = -1.0

        self.last_comm = None
        self.car_datas = []

        self.__prev_pos = (0.0, 0.0)

    @property
    def nbr_events(self):
        return len(self.car_datas)

    def fromDict(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            elif key == "uid":
                self.uid = kwargs[key]
            elif key == "_id":
                pass
            else:
                self.__logger.debug("[CarSession::fromDict] Field '{}' does not exist".format(key))

    def start(self, start_date=datetime.datetime.now()):
        self.__logger.info("Starting session {} at {}".format(self.uid, start_date))
        self.start_date = start_date

        self.status = self.STATUS_ONGOING
        kwargs = {
            "start_date": self.start_date,
            "start_point": self.start_point,
            "first_address": self.first_address,
            "end_point": self.end_point,
            "last_address": self.last_address,
            "duration": self.duration,
            "distance": self.distance,
            "end_date": self.end_date,
            "status": self.status
        }
        self.__db_driver.update_session(self.uid, **kwargs)

    def stop(self):
        self.__logger.info("Stopping session {}".format(self.uid))
        self._terminate_session()
        self.print_session()

    def _terminate_session(self):
        car_datas = self.get_car_data()

        first_data = car_datas[ 0 ]
        last_data = car_datas[ -1 ]

        self.start_point = (first_data[ "latitude" ], first_data[ "longitude" ])
        self.end_point = (last_data[ "latitude" ], last_data[ "longitude" ])

        self.duration = last_data[ "timestamp" ]
        self.distance = last_data[ "distance" ]

        self.end_date = self.start_date + datetime.timedelta(seconds=self.duration)

        min_lat = min_lon = 9999
        max_lat = max_lon = -9999
        for t in reversed(car_datas):
            if t[ "latitude" ]:
                if t[ "latitude" ] > max_lat:
                    max_lat = t[ "latitude" ]
                if t[ "latitude" ] < min_lat:
                    min_lat = t[ "latitude" ]

            if t[ "longitude" ]:
                if t[ "longitude" ] > max_lon:
                    max_lon = t[ "longitude" ]
                if t[ "longitude" ] < min_lon:
                    min_lon = t[ "longitude" ]

            if t[ "latitude" ] and t[ "longitude" ] and self.last_address is None:
                self.last_address = self.address(t[ "latitude" ], t[ "longitude" ])

        max_distance = haversine((min_lat, min_lon), (max_lat, max_lon))
        if max_distance < 1:
            self.__logger.warning(
                "Deleting session with too small geographical dilution ({} km)".format(round(max_distance, 3)))
            self.__db_driver.delete_session(self.uid)
            return

        self.status = self.STATUS_TERMINATED
        kwargs = {
            "start_point": self.start_point,
            "first_address": self.first_address,
            "end_point": self.end_point,
            "last_address": self.last_address,
            "duration": self.duration,
            "distance": self.distance,
            "end_date": self.end_date,
            "status": self.status
        }

        self.__db_driver.update_session(self.uid, **kwargs)

    def address(self, latitude, longitude):
        try:
            results = geocoder.reverse_geocode(latitude, longitude, language='fr', no_annotation='1')
            if results and len(results):
                return results[ 0 ][ 'formatted' ]
        except RateLimitExceededError as ex:
            self.__logger.warning("OpenCageData rate limit exceeded !")
            return "<Limit reached, try later>"

    def new_car_data(self, latitude, longitude, **kwargs):
        valid_dict = dict()

        for field in self.DATA_VALID_FIELDS:
            if field in kwargs:
                valid_dict[ field ] = kwargs[ field ]
            else:
                valid_dict[ field ] = self.DATA_VALID_FIELDS[ field ]

        valid_dict[ "latitude" ] = latitude
        valid_dict[ "longitude" ] = longitude

        if self.__prev_pos[ 0 ] != 0.0 and self.__prev_pos[ 1 ] != 0.0 and latitude and longitude:
            self.distance += haversine(self.__prev_pos, (latitude, longitude))

        if self.first_address is None and latitude != 0 and longitude != 0:
            self.first_address = self.address(latitude, longitude)

        self.__prev_pos = (latitude, longitude)

        if latitude != 0.0 and longitude != 0.0 and "fix" not in valid_dict:
            valid_dict[ "fix" ] = True
        else:
            valid_dict[ "fix" ] = False

        valid_dict[ "uid" ] = self.uid
        valid_dict[ "distance" ] = self.distance
        # print (valid_dict)
        self.__db_driver.add_car_data(**valid_dict)

    def get_car_data(self):
        car_datas = self.__db_driver.get_car_data(self.uid)
        return car_datas

    def print_session(self):
        autopial_session = self.__db_driver.get_session(session_uid=self.uid)
        if autopial_session is None:
            return

        self.__logger.info("########################################################")
        self.__logger.info("Session '{}' terminated".format(autopial_session["uid"]))
        self.__logger.info(" + start date   : {}".format(autopial_session["start_date"]))
        self.__logger.info(" + start point  : {}".format(autopial_session["start_point"]))
        self.__logger.info(" + first address: {}".format(autopial_session["first_address"]))
        self.__logger.info(" + end date     : {}".format(autopial_session["end_date"]))
        self.__logger.info(" + end point    : {}".format(autopial_session["end_point"]))
        self.__logger.info(" + last address : {}".format(autopial_session["last_address"]))
        self.__logger.info(" + origin       : {}".format(autopial_session["origin"]))
        self.__logger.info(" + status       : {}".format(autopial_session["status"]))
        self.__logger.info(" + duration     : {}".format(autopial_session["duration"]))
        self.__logger.info(" + distance     : {}".format(autopial_session["distance"]))
        self.__logger.info("########################################################")
