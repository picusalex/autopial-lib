import datetime
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class GPSLocation(Base):
    __tablename__ = 'gpslocation'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    session_uid = Column(String(50), nullable=False)
    latitude = Column(Float())
    longitude = Column(Float())
    altitude = Column(Float())
    fix = Column(Boolean())
    timestamp = Column(DateTime())

class DatabaseDriver():
    def __init__(self, database):
        # Create an engine that stores data in the local directory's
        # sqlalchemy_example.db file.
        self._database = database
        self.dbengine = create_engine(self._database)
        DBSession = sessionmaker(bind=self.dbengine)
        self.session = DBSession()

    def create_table(self):
        # Create all tables in the engine. This is equivalent to "Create Table"
        # statements in raw SQL.
        Base.metadata.create_all(self.dbengine)

    def add_gps_location(self, session_uid, lat, lon, alt=0, fix=True, dt=datetime.datetime.now()):
        new_gps_location = GPSLocation(session_uid=session_uid,
                                       latitude=lat,
                                       longitude=lon,
                                       altitude=alt,
                                       fix=fix,
                                       timestamp=dt)
        self.session.add(new_gps_location)
        self.session.commit()



