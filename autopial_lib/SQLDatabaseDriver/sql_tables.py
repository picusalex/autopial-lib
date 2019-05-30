import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from opencage.geocoder import OpenCageGeocode

key = '17d3fa34ccb04d42b9292c191ae4d0b8'
geocoder = OpenCageGeocode(key)

Base = declarative_base()

class CarData(Base):
    __tablename__ = 'cardata'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)

    session_id = Column(String(32), ForeignKey('session.id'), nullable=False)
    timestamp = Column(Float(), nullable=False)
    distance = Column(Float(), default=0.0)

    fix = Column(Boolean(), nullable=False, default=0)
    latitude = Column(Float(), nullable=False, default=0.0)
    longitude = Column(Float(), nullable=False, default=0.0)
    altitude = Column(Float(), default=-1)

    gps_speed = Column(Float(), default=-1)
    direction = Column(Float(), default=-1)

    rpm = Column(Float(), default=-1)
    obd_speed = Column(Float(), default=-1)
    coolant_temp = Column(Float(), nullable=False, default=-1)
    oil_temp = Column(Float(), nullable=False, default=-1)

    accel_x = Column(Float(), nullable=False, default=-1)
    accel_y = Column(Float(), nullable=False, default=-1)
    accel_z = Column(Float(), nullable=False, default=-1)

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "distance": self.distance,

            "fix": self.fix,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,

            "gps_speed": self.gps_speed,
            "direction": self.direction,

            "rpm": self.rpm,
            "obd_speed": self.obd_speed,
            "coolant_temp": self.coolant_temp,
            "oil_temp": self.oil_temp,

            "accel_x": self.accel_x,
            "accel_y": self.accel_y,
            "accel_z": self.accel_z,
        }

class Session(Base):
    __tablename__ = 'session'

    id = Column(String(32), primary_key=True)
    origin = Column(String(150), nullable=False)
    status = Column(String(32), nullable=False)

    start_date = Column(DateTime(), nullable=False)
    start_point_lat = Column(Float())
    start_point_lon = Column(Float())

    end_date = Column(DateTime())
    end_point_lat = Column(Float())
    end_point_lon = Column(Float())

    first_address = Column(String(250))
    last_address = Column(String(250))

    max_speed = Column(Float())

    last_comm = Column(DateTime(), nullable=False)

    duration = Column(Float())
    distance = Column(Float())

    def update_metadata(self):
        self.logger.info("[DATABASE] Update Autopial Session id={} metadata".format(self.id))
        autopial_session = self.get_session(session_uid=self.id)

        gps_entries = self.dbsession.query(CarData).filter_by(session_id=self.id).order_by(
            CarData.timestamp)

        autopial_session.length = gps_entries.count()

        first_entry = gps_entries[0]
        autopial_session.start_point_lat = first_entry.latitude
        autopial_session.start_point_lon = first_entry.longitude
        results = geocoder.reverse_geocode(first_entry.latitude, first_entry.longitude, language='fr')
        autopial_session.start_address = "{}, {}".format(results[0])

        first_pos = (0,0)
        last_pos = (0, 0)
        for gps_entry in gps_entries:
            if first_pos[0] == 0 and first_pos[1] == 0 and gps_entry.latitude !=0 and gps_entry.longitude !=0:
                pass


        last_entry = gps_entries[-1]
        autopial_session.end_point_lat = last_entry.latitude
        autopial_session.end_point_lon = last_entry.longitude

        autopial_session.duration = last_entry.timestamp
        autopial_session.distance = round(last_entry.distance, 2)

        autopial_session.end_date = autopial_session.start_date + datetime.timedelta(seconds=last_entry.timestamp)

        self.db.commit()
        return True