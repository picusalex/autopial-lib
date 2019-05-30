import datetime

from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from .sql_tables import Base, Session, CarData

class DatabaseDriver():
    def __init__(self, database, logger):
        # Create an engine that stores data in the local directory's
        # sqlalchemy_example.db file.
        self.logger = logger
        self._database = database
        self.dbengine = create_engine(self._database)
        DBSession = sessionmaker(bind=self.dbengine)
        self.dbsession = DBSession()

        try:
            if not self.dbengine.dialect.has_table(self.dbengine, "session") or \
                not self.dbengine.dialect.has_table(self.dbengine, "cardata") :
                Base.metadata.create_all(self.dbengine)
        except Exception as e:
            logger.error("SQL database error: {}".format(e))

    def create_session(self, session_uid, origin, start_date=datetime.datetime.now()):
        autopial_session = self.get_session(session_uid)

        if autopial_session is None:
            self.logger.info("[DATABASE] Creating Autopial Session in DB. id={}".format(session_uid))
            autopial_session = Session(id=session_uid,
                                       origin=origin,
                                       start_date=start_date,
                                       last_comm=datetime.datetime.now(),
                                       status="NOTSTARTED")
            self.dbsession.add(autopial_session)
            self.dbsession.commit()
        else:
            self.logger.info("[DATABASE] Autopial Session id={} already exist".format(session_uid))
        return autopial_session

    def get_session(self, session_uid):
        autopial_session = self.dbsession.query(Session).filter_by(id=session_uid).first()
        return autopial_session

    def get_all_sessions(self):
        autopial_sessions = self.dbsession.query(Session).all()
        return autopial_sessions

    def update_session(self, session_uid, **kwargs):
        if "id" in kwargs:
            del kwargs["id"]

        autopial_session = self.get_session(session_uid=session_uid)
        if autopial_session is None:
            return False

        for field in kwargs:
            if hasattr(autopial_session, field):
                self.logger.info("[DATABASE] Update Autopial Session id={} {}={}".format(session_uid, field, kwargs[field]))
                setattr(autopial_session, field, kwargs[field])

        self.dbsession.commit()





    def delete_session(self, session_uid):
        self.logger.info("[DATABASE] Deleting session: '{}'".format(session_uid))
        self.dbsession.query(CarData).filter_by(session_id=session_uid).delete()
        self.dbsession.query(Session).filter_by(id=session_uid).delete()
        self.dbsession.commit()
        return True

    def add_gps_location(self, session_uid, fix, longitude, latitude, altitude, timestamp):
        autopial_session = self.get_session(session_uid=session_uid)
        if autopial_session.status != "ONGOING" and autopial_session.status != "PAUSED":
            self.logger.info("[DATABASE] Session {} has invalid state to add data. status={}".format(session_uid, autopial_session.status))
            return False

        #self.logger.debug("[DATABASE] Add GPS location to session: '{}'".format(session_uid))
        gps_location = GPSLocation( latitude=latitude,
                                    longitude=longitude,
                                    altitude=altitude,
                                    fix=fix,
                                    timestamp=timestamp,
                                    session_id=session_uid)
        self.dbsession.add(gps_location)
        #autopial_session.gps_locations.append(gps_location)
        self.dbsession.commit()
        return True

    def get_gps_locations(self, session_uid):
        gps_entries = self.dbsession.query(CarData).filter_by(session_id=session_uid).order_by(
            GPSLocation.timestamp)
        return [gps.to_dict() for gps in gps_entries]

    def add_car_data(self, session_uid, timestamp, distance,
                     fix, latitude, longitude, altitude,
                     gps_speed, direction,
                     obd_speed, rpm, coolant_temp, oil_temp,
                     accel_x, accel_y, accel_z):
        autopial_session = self.get_session(session_uid=session_uid)
        if autopial_session.status != "ONGOING" and autopial_session.status != "PAUSED":
            self.logger.info("[DATABASE] Session {} has invalid state to add data. status={}".format(session_uid, autopial_session.status))
            return False

        #self.logger.debug("[DATABASE] Add GPS movement to session: '{}'".format(session_uid))
        car_data = CarData( session_id=session_uid, timestamp=timestamp, distance=distance,
                                fix=fix, latitude=latitude, longitude=longitude, altitude=altitude,
                                gps_speed=gps_speed, direction=direction,
                                obd_speed=obd_speed, rpm=rpm,coolant_temp=coolant_temp, oil_temp=oil_temp,
                                accel_x=accel_x, accel_y=accel_y, accel_z=accel_z)

        self.dbsession.add(car_data)
        self.dbsession.commit()
        return True

    def get_cardata(self, session_uid):
        all_entries = self.dbsession.query(CarData).filter_by(session_id=session_uid).order_by(
            CarData.timestamp)
        return [data.to_dict() for data in all_entries]


