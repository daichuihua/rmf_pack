from multiprocessing import Event
from pickle import TRUE
import random
import time
from time import ctime
import os as _os
import sys as _sys
import threading
import eventlet

from paho.mqtt import client as mqtt_client
     
class RobotMqtt:
    def __init__(self,broker,port):
        self.broker = broker
        self.port = port
        self.client  = None
        self.client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.event = Event()

    def connect_mqtt(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)
        self.client = mqtt_client.Client(self.client_id)
        self.client.on_connect = on_connect
        self.client.connect(self.broker, self.port)
        return self.client

    def publish(self,topic,msg):
        result = self.client.publish(topic, msg)
        status = result[0]
        if status == 0:
            # print(f"22222222发送： Send `{msg}` to topic `{topic}`\n",'时间:',ctime())
            pass
        else:
            print(f"Failed to send message to topic {topic}")

    def subscribe(self,callback,topic):
        self.client.subscribe(topic)
        self.client.on_message = callback

    def loop_start(self):
        self.client.loop_start()
