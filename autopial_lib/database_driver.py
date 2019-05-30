

"""
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
"""