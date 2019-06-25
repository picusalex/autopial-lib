#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import logging

import pymongo
from pymongo import MongoClient

class CarDriver():
    COLLECTION_SESSION = "car_session"
    COLLECTION_DATA = "car_data"

    def __init__(self, db_path, db_name="autopial-cardb", logger=None):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.connect(db_path, db_name)

    def connect(self, db_path, db_name):
        self._db_path = db_path
        self._db_name = db_name
        client = MongoClient(db_path)
        self.database = client[db_name]


    def create_session(self, session_uid, origin, start_date=datetime.datetime.now()):
        autopial_session = self.get_session(session_uid)

        if autopial_session is None:
            self.logger.info("[DATABASE] Creating Autopial Session in DB. uid={}".format(session_uid))
            t = dict(uid=session_uid,
                     origin=origin,
                     start_date=start_date,
                     last_comm=datetime.datetime.now(),
                     status="NOTSTARTED",
                     car_datas=[])
            autopial_session = self.database[self.COLLECTION_SESSION].insert_one(t)
        else:
            self.logger.info("[DATABASE] Autopial Session uid={} already exist".format(session_uid))
        return autopial_session

    def update_session(self, session_uid, **kwargs):
        if "_id" in kwargs:
            del kwargs["_id"]

        autopial_session = self.get_session(session_uid=session_uid)
        if autopial_session is None:
            return False

        for field in kwargs:
            #if field in autopial_session:
            self.logger.info("[DATABASE] Update Autopial Session uid={} {}={}".format(session_uid, field, kwargs[field]))
            autopial_session[field] = kwargs[field]

        autopial_session["last_comm"] = datetime.datetime.now()
        result = self.database[ self.COLLECTION_SESSION ].update_one({"uid": session_uid}, {'$set': autopial_session})
        return result.modified_count

    def get_session(self, session_uid):
        autopial_session = self.database[ self.COLLECTION_SESSION ].find_one({"uid": session_uid})
        return autopial_session

    def get_all_sessions(self):
        autopial_sessions = list(self.database[ self.COLLECTION_SESSION ].find())
        return autopial_sessions

    def delete_session(self, session_uid):
        self.logger.info("[DATABASE] Deleting session: '{}'".format(session_uid))
        result = self.database[ self.COLLECTION_SESSION ].delete_many({"uid": session_uid})
        return result.deleted_count

    def add_car_data(self, uid, timestamp, distance,
                     fix, latitude, longitude, altitude,
                     gps_speed, direction,
                     obd_speed, rpm, coolant_temp, oil_temp,
                     accel_x, accel_y, accel_z):

        #self.logger.debug("[DATABASE] Add GPS movement to session: '{}'".format(session_uid))
        car_data = dict( session_uid=uid,
                         timestamp=timestamp,
                         distance=distance,
                         fix=fix, latitude=latitude, longitude=longitude, altitude=altitude,
                         gps_speed=gps_speed, direction=direction,
                         obd_speed=obd_speed, rpm=rpm,coolant_temp=coolant_temp, oil_temp=oil_temp,
                         accel_x=accel_x, accel_y=accel_y, accel_z=accel_z)
        mongo_object = self.database[ self.COLLECTION_DATA ].insert_one(car_data)

        result = self.database[ self.COLLECTION_SESSION ].update_one(
            {
                "uid": uid
            },
            {
                '$push': {
                    "car_datas": mongo_object.inserted_id
                }
            }
        )
        return True

    def get_car_data(self, uid, offset=None, limit=None):
        mongo_objects = self.database[ self.COLLECTION_DATA ]\
            .find({"session_uid": uid}, {'_id': False}) \
            .sort("timestamp", 1)

        if offset is not None:
            mongo_objects.skip(offset)
        if limit is not None:
            mongo_objects.limit(limit)

        return list(mongo_objects)