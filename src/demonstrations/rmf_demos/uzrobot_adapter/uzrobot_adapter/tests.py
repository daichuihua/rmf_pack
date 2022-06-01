from singleton import instance

from robot_mqtt import RobotMqtt

import threading

import random
import time

def task():
    broker = '192.168.110.200'
    port = 9002
    topic = "/python/mqtt"

    rq = RobotMqtt(broker,port)
    rq.connect_mq()
    rq.subscribe('aaaa')
    while True:
        time.sleep(1)
if __name__ == '__main__':
    task()
