import datetime
import sys
import threading

import os
import sqlalchemy
from haversine import haversine
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from autopial_lib.thread_worker import AutopialWorker

Base = declarative_base()

class GPSLocation(Base):
    __tablename__ = 'gpslocation'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    session_id = Column(String(32), ForeignKey('session.id'), nullable=False)
    #session = relationship("Session", back_populates="gps_locations")
    latitude = Column(Float(), nullable=False, default=-1)
    longitude = Column(Float(), nullable=False, default=-1)
    altitude = Column(Float(), nullable=False, default=-1)
    fix = Column(Boolean(), nullable=False, default=0)
    timestamp = Column(Float(), nullable=False)

    def to_dict(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "fix": self.fix,
            "timestamp": self.timestamp
        }

SESSION_STATUS = [
    "NOTSTARTED",
    "ONGOING",
    "PAUSED",
    "TERMINATED"
]

class Session(Base):
    __tablename__ = 'session'
    id = Column(String(32), primary_key=True)
    origin = Column(String(150), nullable=False)
    status = Column(String(32), nullable=False)

    start_date = Column(DateTime(), nullable=False)
    start_point_lat = Column(Float())
    start_point_lon = Column(Float())

    end_point_lat = Column(Float())
    end_point_lon = Column(Float())
    end_date = Column(DateTime())

    max_speed = Column(Float())

    last_comm = Column(DateTime(), nullable=False)
    duration = Column(Float())
    distance = Column(Float())

    #gps_locations = relationship("GPSLocation",
    #                             order_by=GPSLocation.timestamp,
    #                             back_populates="session")


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
            if not self.dbengine.dialect.has_table(self.dbengine, "session"):
                self.create_table()
        except Exception as e:
            logger.error("SQL database error: {}".format(e))

    def create_table(self):
        # Create all tables in the engine. This is equivalent to "Create Table"
        # statements in raw SQL.
        Base.metadata.create_all(self.dbengine)

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

    def update_session(self, session_uid, status=None, duration=None, length=None, last_comm=None, start_date=None):
        autopial_session = self.get_session(session_uid=session_uid)
        if status is not None:
            self.logger.info("[DATABASE] Update Autopial Session id={} status={}".format(session_uid, status))
            autopial_session.status = status
        if duration is not None:
            self.logger.info("[DATABASE] Update Autopial Session id={} duration={}".format(session_uid, duration))
            autopial_session.duration = duration
        if length is not None:
            self.logger.info("[DATABASE] Update Autopial Session id={} length={}".format(session_uid, length))
            autopial_session.length = length
        if last_comm is not None:
            self.logger.info("[DATABASE] Update Autopial Session id={} last_comm={}".format(session_uid, last_comm))
            autopial_session.last_comm = last_comm
        if start_date is not None:
            self.logger.info("[DATABASE] Update Autopial Session id={} start_date={}".format(session_uid, start_date))
            autopial_session.start_date = start_date
        self.dbsession.commit()

    def update_session_metadata(self, session_uid):
        self.logger.info("[DATABASE] Update Autopial Session id={} metadata".format(session_uid))
        autopial_session = self.get_session(session_uid=session_uid)
        nbr_gps_location = self.dbsession.query(GPSLocation).filter_by(session_id=session_uid).count()
        autopial_session.length = nbr_gps_location

        gps_entries = self.dbsession.query(GPSLocation).filter_by(session_id=session_uid).order_by(
            GPSLocation.timestamp)

        first_entry = gps_entries[0]
        autopial_session.start_point_lat = first_entry.latitude
        autopial_session.start_point_lon = first_entry.longitude

        last_entry = gps_entries[-1]
        autopial_session.end_point_lat = last_entry.latitude
        autopial_session.end_point_lon = last_entry.longitude

        autopial_session.duration = last_entry.timestamp
        autopial_session.end_date = autopial_session.start_date + datetime.timedelta(seconds=last_entry.timestamp)

        distance = 0
        prev_pos = (0,0)
        for gps in gps_entries:
            if prev_pos[0] != 0 and prev_pos[1] != 0:
                distance = distance + haversine(prev_pos, (gps.latitude, gps.longitude))
            prev_pos = (gps.latitude, gps.longitude)

        autopial_session.distance = round(distance, 2)
        self.dbsession.commit()

    def print_session(self, session_uid):
        autopial_session = self.get_session(session_uid=session_uid)
        self.logger.info("########################################################")
        self.logger.info("Session '{}' terminated".format(autopial_session.id))
        self.logger.info(" + start date : {}".format(autopial_session.start_date))
        self.logger.info(" + start point: {},{}".format(autopial_session.start_point_lat,autopial_session.start_point_lon))
        self.logger.info(" + end date   : {}".format(autopial_session.end_date))
        self.logger.info(" + end point  : {},{}".format(autopial_session.end_point_lat, autopial_session.end_point_lon))
        self.logger.info(" + origin     : {}".format(autopial_session.origin))
        self.logger.info(" + status     : {}".format(autopial_session.status))
        self.logger.info(" + duration   : {}".format(autopial_session.duration))
        self.logger.info(" + distance   : {}".format(autopial_session.distance))
        self.logger.info("########################################################")

    def delete_session(self, session_uid):
        self.logger.info("[DATABASE] Deleting session: '{}'".format(session_uid))
        self.dbsession.query(GPSLocation).filter_by(session_id=session_uid).delete()
        self.dbsession.query(Session).filter_by(id=session_uid).delete()
        self.dbsession.commit()

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
        gps_entries = self.dbsession.query(GPSLocation).filter_by(session_id=session_uid).order_by(
            GPSLocation.timestamp)
        return [gps.to_dict() for gps in gps_entries]

class SessionWorker(AutopialWorker):
    def __init__(self, mqtt_client, database, logger):
        AutopialWorker.__init__(self, mqtt_client, time_sleep=5, logger=logger)
        self.logger = logger
        self.dbdriver = DatabaseDriver(database, logger)

    def _update_active_session(self):
        active_sessions = self.dbdriver.session.query(Session).filter_by(status="ONGOING")
        pass

    def _ping(self, session_uid):
        if session_uid not in self.active_sessions:
            self.logger.error("Cannot ping session {}, does not exist !".format(session_uid))
        else:
            self.active_sessions[session_uid]["last_comm"] = datetime.datetime.now()
            self.active_sessions[session_uid]

    def create_session(self, session_uid, origin, start_date=datetime.datetime.now()):
        autopial_session = self.dbsession.query(Session).filter_by(id=session_uid).first()
        if autopial_session is not None:
            self.active_sessions[session_uid] = autopial_session
            self._ping(session_uid)
            return
        else:
            autopial_session = Session(id=session_uid,
                                  origin=origin,
                                  start_date=start_date,
                                  status="ONGOING")
            self.dbsession.add(autopial_session)
            self.dbsession.commit()


    def get_session(self, session_uid):
        if session_uid not in self.active_sessions:
            autopial_session = self.dbsession.query(Session).filter_by(id=session_uid).first()
            if autopial_session is None:
                self.logger.error("Trying to get session {} that does not exist in DB !".format(session_uid))
                return None


    def run(self):
        self.logger.info("Session manager thread starts")
        while self.wait():
            self._update_active_session()
            pass

class DatabaseLogger():
    def __init__(self, database, logger):
        self.dbdriver = DatabaseDriver(database, logger)

        self.session_manager = SessionWorker("SessionWorker", logger=logger, dbsession=self.dbsession)
        self.session_manager.start()

    def start_session(self, session_uid, origin, start_date=datetime.datetime.now()):
        self.logger.info("Starting new session: '{}' from '{}' at '{}'".format(session_uid, origin, start_date))


        self.session_manager.get_session(session_uid)
        pass

        try:
            new_session = Session(id=session_uid,
                                  origin=origin,
                                  start_date=start_date,
                                  status="ONGOING")
            self.dbsession.add(new_session)
            self.dbsession.commit()
        except:
            self.dbsession.rollback()
            self.logger.warning("Session {} already exists !".format(session_uid))
            new_session = self.dbsession.query(Session).filter_by(id=session_uid).first()

        new_session.status = "ONGOING"
        self.active_sessions[session_uid] = new_session

        return new_session

    def stop_session(self, session_uid):
        self.logger.info("Stopping session: '{}'".format(session_uid))

        if session_uid not in self.active_sessions:
            self.active_sessions[session_uid] = self.dbsession.query(Session).filter_by(id=session_uid).first()

        current_session = self.active_sessions[session_uid]

        nbr_gps_location = self.dbsession.query(GPSLocation).filter_by(session_id=session_uid).count()
        last_entry = self.dbsession.query(GPSLocation).filter_by(session_id=session_uid).order_by(GPSLocation.timestamp.desc()).first()

        current_session.length = nbr_gps_location
        current_session.duration = last_entry.timestamp
        current_session.status = "TERMINATED"
        self.dbsession.commit()
        del self.active_sessions[session_uid]

        self.logger.info("########################################################")
        self.logger.info("Session '{}' terminated".format(current_session.id))
        self.logger.info(" + start date: {}".format(current_session.start_date))
        self.logger.info(" + origin    : {}".format(current_session.origin))
        self.logger.info(" + status    : {}".format(current_session.status))
        self.logger.info(" + duration  : {}".format(current_session.duration))
        self.logger.info(" + entries   : {}".format(current_session.length))
        self.logger.info("########################################################")

        return True

    def delete_session(self, session_uid):
        self.logger.info("Deleting session: '{}'".format(session_uid))
        current_session = self.dbsession.query(Session).filter_by(id=session_uid).first()
        self.dbsession.query(GPSLocation).filter_by(session_id=session_uid).delete()
        self.dbsession.query(Session).filter_by(id=session_uid).delete()
        self.dbsession.commit()

    def add_gps_location(self, session_uid, latitude, longitude, altitude, fix, timestamp):
        if session_uid not in self.active_sessions:
            self.active_sessions[session_uid] = self.dbsession.query(Session).filter_by(id=session_uid).first()

        if self.active_sessions[session_uid].status != "ONGOING":
            self.logger.error("Session {} not in 'ONGOING' state ! (status={})".format(session_uid, self.active_sessions[session_uid].status))
            return False

        new_gps_location = GPSLocation(latitude=latitude,
                                       longitude=longitude,
                                       altitude=altitude,
                                       fix=fix,
                                       timestamp=timestamp)
        self.dbsession.add(new_gps_location)
        self.active_sessions[session_uid].gps_locations.append(new_gps_location)
        self.dbsession.commit()
        return True