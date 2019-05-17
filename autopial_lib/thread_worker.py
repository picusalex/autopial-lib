import json
import logging
import threading
import uuid
import logging
import time
import datetime

import os
import paho.mqtt.client as mqtt #import the client1
import sys

class AutopialWorker(threading.Thread):
    BROKER_ADDRESS = "localhost"

    def __init__(self, mqtt_client_name, time_sleep=5, logger = None):
        threading.Thread.__init__(self)
        self.daemon = True
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger

        self.logger.info("New AutopialWorker: '{}' publishing every {}secs".format(mqtt_client_name, time_sleep))
        self.time_sleep = time_sleep
        self._stopevent = threading.Event( )
        self._one_time_force = True
        self._last_publish_dates = {}
        self.client_name = mqtt_client_name
        self.mqtt_connect(mqtt_client_name)

    def autopial_metadata(self):
        md = {
            "device_uid" : str(os.environ['AUTOPIAL_UID']),
            "device_name" : str(os.environ['AUTOPIAL_NAME']),
            "process_name": str(os.path.basename(sys.argv[0])),
            "worker_name": str(self.client_name)
        }
        return md


    def mqtt_connect(self, mqtt_client_name):
        #self.client_name = "{}-{}".format(mqtt_client_name, uuid.uuid4().hex)
        self.logger.info("Connection to MQTT broker: '{}' with name '{}'".format(self.BROKER_ADDRESS, self.client_name))
        self.mqtt_client = mqtt.Client(self.client_name)
        try:
            self.mqtt_client.connect(self.BROKER_ADDRESS, port=1883, keepalive=60)
        except ConnectionRefusedError as e:
            self.logger.error("  => MQTT connection failed ! Is broker installed and launched ? (sudo apt install mosquitto")
            sys.exit(1)

        self.logger.info("  => successful !")

    def run(self):
        self.logger.error("Define a run() method from an inherited class of AutopialWorker")

    def publish(self, topic, value, ignore_timer=False):
        if ignore_timer is False:
            if topic not in self._last_publish_dates:
                self._last_publish_dates[topic] = datetime.datetime.now()
            else:
                if self._last_publish_dates[topic] + datetime.timedelta(seconds=self.time_sleep) > datetime.datetime.now():
                    return

        if isinstance(value, dict):
            value["datetime"] = datetime.datetime.now().isoformat(' ')
            value["topic"] = topic
            value["autopial"] = self.autopial_metadata()
        else:
            value = {
                "topic": topic,
                "value": value,
                "datetime" : datetime.datetime.now().isoformat(),
                "autopial" : self.autopial_metadata()
            }

        value = json.dumps(value)
        self.logger.info("MQTT Publish: {} = {}".format(topic, value))
        self.mqtt_client.publish(topic,
                                 payload=value,
                                 qos=0,
                                 retain=True)
        self._last_publish_dates[topic] = datetime.datetime.now()

    def wait(self):
        if self._one_time_force == True:
            self._one_time_force = False
        else:
            self.logger.debug("{} sleeping for {} seconds".format(self.client_name, self.time_sleep))
            first_dt = datetime.datetime.now()
            dt = datetime.datetime.now()
            while (dt - first_dt).total_seconds() < self.time_sleep and not self._stopevent.isSet():
                time.sleep(0.2)
                dt = datetime.datetime.now()
        return not self._stopevent.isSet()

    def next(self):
        return not self._stopevent.isSet()

    def stop(self):
        self._stopevent.set( )


