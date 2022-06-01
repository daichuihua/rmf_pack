# from asyncio.windows_events import NULL
from fcntl import DN_DELETE
from multiprocessing import Event
from pickle import TRUE
import re
from turtle import pos
from matplotlib.pyplot import cla
from .robot_mqtt import RobotMqtt
import threading
import time
import uuid
import json
import array
import nudged
import copy
import math
from time import ctime
lock = threading.Lock()
class RobotInfo:
    def __init__(self) -> None:
        self.sn = ""
        self.x = 0
        self.y = 0
        self.theta = 0
        self.map_alias = "" 
        self.battery_soc = 0
        self.transforms = None
        self.navigate = []
        self.navigation_completed_flag = False
        pass

class RobotAPI:
    # The constructor below accepts parameters typically required to submit
    # http requests. Users should modify the constructor as per the
    # requirements of their robot's API
    def __init__(self, prefix: str, user: str, password: str):
        self.prefix = prefix
        self.user = user
        self.password = password
        self.connected = False
        # 接收机器人列表事件
        self.robotlist_uuid = None
      
        self.robotlist_event = Event()
        self.robotlist = []
        self.robot_info_list = []
        self.rq = None
        self.topic_send = "rmf/to/ubhrpl/api"
        self.topic_recv = "ubhrpl/to/rmf/api"
        self.mqtt_thread()

    def mqtt_thread(self):
        def on_recv(client, userdata, msg):
            jsondata = json.loads(msg.payload.decode())
            uuid = jsondata['uuid']
            result = jsondata['result']['msg']
            cmd = jsondata['title'] #responseUrmsRobotList
            if cmd == 'responseUrmsRobotList':
                self.robotlist.clear()
                robots = jsondata['data']['robotList']
                for robot in robots:
                    sn = robot['robotsSelfBaseInfo']['theRobot']['sn']
                    self.robotlist.append(sn)
                self.robotlist_event.set()        
            print(f"-------------------------------------------------------------",'\n')
            print(f"Received from :`{msg.topic}` topic\n")
            print(msg.payload.decode())            
            print(f"-------------------------------------------------------------",'\n')
            return 
        broker = '10.10.17.35'
        port = 1883
        self.rq = RobotMqtt(broker,port)
        self.rq.connect_mqtt()
        self.rq.event.clear()
        self.rq.subscribe(on_recv,self.topic_recv)
        self.rq.loop_start()

    def check_connection(self):
        ''' Return True if connection to the robot API server is successful'''
        # 连接 URMS MQTT 服务
        return True

    def transforms(self):
        return None

    def transforms_test(self):     
        tuuid = uuid.uuid1()
        playload = json.dumps(
            {
                "content":{
                    "srcMapInfo":{
                        "alias":"智园C1栋",
                        "format":"pointCloundMap",
                        "serverDomainName":"www.mapServer.com",
                        "serverIpAdress":"192.168.1.100",
                        "url":"/home/map/2d/floor_8/",
                        "mapFile":"map.png",
                        "mapConfig":"map.yaml"
                    },
                    "dstMapInfo":{
                        "alias":"8楼_zwy",
                        "format":"cadMap",
                        "serverDomainName":"www.mapServer.com",
                        "serverIpAdress":"192.168.1.100",
                        "url":"/home/map/2d/floor_8/",
                        "mapFile":"floor_8.cad",
                        "mapConfig":""
                    }
                },
                "timestamp":1646978181926,
                "title":"requestUrmsMapTransform",
                "uuid":tuuid.hex
            }
        )
        self.rq.publish(self.topic_send,playload)
        return None
    
    def addrobot(self,vendor,sn):
        #添加mqtt 订阅回调
        def on_message_recv(client, userdata, msg):
            # print("\n")
            # print(f"-------------------------------------------------------------")
            # print(f"Received from :`{msg.topic}` topic\n")
            # print(msg.payload.decode())            
            # print(f"-------------------------------------------------------------")
            # print("\n")
            jsondata = json.loads(msg.payload.decode())
            uuid = jsondata['uuid']
            cmd = jsondata['title'] #responseUrmsRobotList
            # 位置信息
            if cmd == 'reportRobotPosition':
                sn = jsondata['theRobot']['sn']
                robot_info = self.get_robot_info(sn)
                print(robot_info)
                loc = jsondata['data']['robotLocation']['location']
                robot_info.x =loc['x']
                robot_info.y = loc['y']
                robot_info.theta = loc['yaw']
                robot_info.map_alias = jsondata['data']['robotLocation']['mapAlias']
                print(f"message pos:{sn}")
            # 设备信息
            elif cmd == 'reportRobotDeviceStatus':
                sn = jsondata['theRobot']['sn']
                robot_info = self.get_robot_info(sn)
                print(robot_info)
                soc = jsondata['data']['robotDeviceStatus']['battery']['data']['level']
                robot_info.battery_soc = soc
                print(f"message soc:{sn}")
            elif cmd == 'responseUrmsMapTransform':
                print(f"responseUrmsMapTransform")
            elif cmd == 'reportRobotTaskStatus':
                sn = jsondata['theRobot']['sn']
                robot_info = self.get_robot_info(sn)
                if jsondata['data']['robotTaskStatus']['status']=="finished":
                    robot_info.navigation_completed_flag = True                
                print("reportRobotTaskStatus")
            return
        robot_info  = RobotInfo()
        robot_info.sn = sn        
        self.robot_info_list.append(copy.copy(robot_info))
   
        topic = self.topic_recv+'/'+vendor + '/'+sn
        self.rq.subscribe(on_message_recv,topic)
        return True

    def conf_transform(self,sn,rmf_coordinates,robot_coordinates):
        robot_info = self.get_robot_info(sn)
        robot_info.transforms = {'rmf_to_robot': nudged.estimate(rmf_coordinates, robot_coordinates),
            'robot_to_rmf': nudged.estimate(robot_coordinates, rmf_coordinates)}
        robot_info.transforms['orientation_offset'] = robot_info.transforms['rmf_to_robot'].get_rotation()
        mse = nudged.estimate_error(robot_info.transforms['rmf_to_robot'],rmf_coordinates,robot_coordinates)
        print(f"Coordinate transformation error: {mse}")       

    def transform_get(self,sn):
        robot_info = self.get_robot_info(sn)
        return  robot_info.transforms
    
    def transform_rmf_to_robot(self,sn,position):
        robot_info = self.get_robot_info(sn)
        x, y = robot_info.transforms['rmf_to_robot'].transform(
                [position[0], position[1]])
        theta = math.degrees(position[2]) + robot_info.transforms['orientation_offset']
        # print(f"rmf to robot   x:{x},y:{y},theta:{theta}")
        return [x,y,theta]

    def transform_robot_to_rmf(self,sn,position):
        robot_info = self.get_robot_info(sn)
        x, y = robot_info.transforms['robot_to_rmf'].transform(
                [position[0], position[1]])
        theta = math.radians(position[2]) - robot_info.transforms['orientation_offset']
        # print(f"robot to rmf   x:{x},y:{y},theta:{theta}")
        return [x,y,theta] 

    def getrobotlist(self):
        self.robotlist_event.clear()
        self.robotlist_uuid = uuid.uuid1()
        playload = json.dumps(
            {
            "content":{
            "theNodeAddress":{
            "alias": "nodeAlias",
            "buildingAddress":{
            "building": "nodeBuilding",
            "floor": "nodeFloor",
            "room": "nodeRoom"
            }
            } },
            "timestamp":1646978181926,
            "title":"requestUrmsRobotList",
            "uuid":self.robotlist_uuid.hex
            }
        )
        self.rq.publish(self.topic_send,playload)
        self.robotlist_event.wait(5)
        # print("\n")
        # print(f"-------------------------------------------------------------")
        # print(f"RobotClient RobotList :")
        for robot in self.robotlist:
            print(robot)
        # print(f"-------------------------------------------------------------")
        return self.robotlist

    def get_robot_info(self,sn):
        for info in self.robot_info_list:
            if info.sn == sn:
                return info
        return None

    # 获取机器人当前位置
    def position(self, robot_name: str):
        ''' Return [x, y, theta] expressed in the robot's coordinate frame or
            None if any errors are encountered'''
        # x = 0
        # y = 0
        # theta = 0
        robot_info = self.get_robot_info(robot_name)
        if robot_info is None:
            print(f"RobotClient name {robot_name} position: None")
            return None
        x = robot_info.x
        y = robot_info.y
        theta = robot_info.theta
        # print(f"33333333接收位置：--------------RobotClient position:Name:{robot_name}  X:{x} Y:{y} Theta: {theta}",'时间：',ctime() )
        # if x == 0 and y == 0 and theta ==0:
        #     return None
        return [x,y,theta]

    # 设置机器人移动到导航点位置
    def navigate(self, robot_name: str, pos, map_name: str):
        ''' Request the robot to navigate to pose:[x,y,theta] where x, y and
            and theta are in the robot's coordinate convention. This function
            should return True if the robot has accepted the request,
            else False'''
        robot_info = self.get_robot_info(robot_name)
        # if robot_info.navigation_completed_flag == False:
        #     return False
        # robot_info.navigation_completed_flag = False
        robot_info.navigate = pos
        print("navigate pos"+"{robot_info.navigate}")

        x = pos[0]
        y = pos[1]
        theta = pos[2]

        if theta > 360:
            theta = theta - 360
        if theta <0:
            theta = theta + 360

        vendor = "CIOT"
        tuuid = uuid.uuid1()
        playload = json.dumps(
            {
                "theRobot":{
                    "alias":"CIOT_1",
                    "ip":"39.101.132.114",
                    "model":"CIOT_1",
                    "sn":robot_name,
                    "vendor":"CIOT"
                },
                "content":{
                    "type":"pointClound",
                    "point":{
                        "id":"pointId",
                        "alias":"pointAlias",
                        "mapAlias":"pointMapAlias",
                        "type":"passthrough",
                        "buildingAddress":{
                            "building":"pointBuilding",
                            "floor":"pointFloor",
                            "room":"pointRoom"
                        },
                        "location":{
                            "x":x,
                            "y":y,
                            "z":8,
                            "longitude":0,
                            "latitude":0,
                            "yaw":theta,
                            "elevation":0
                        }
                    }
                },
                "timestamp":1646978181926,
                "title":"requestMoveToPoint",
                "uuid":tuuid.hex
            }
        )
        topic = self.topic_send
        self.rq.publish(topic,playload)
        
        print(f"注意注意注意注意！！！！！！！！！！ :Name:{robot_name}  Position X:{x} Y:{y} Theta: {theta}" )
        return True

    # 开始执行一个任务
    def start_process(self, robot_name: str, process: str, map_name: str):
        ''' Request the robot to begin a process. This is specific to the robot
            and the use case. For example, load/unload a cart for Deliverybot
            or begin cleaning a zone for a cleaning robot.
            Return True if the robot has accepted the request, else False'''
        return False

    def stop(self, robot_name: str):
        vendor = "CIOT"
        tuuid = uuid.uuid1()
        playload = json.dumps(
            {
                "theRobot":{
                    "alias":"CIOT_1",
                    "ip":"39.101.132.114",
                    "model":"CIOT_1",
                    "sn":robot_name,
                    "vendor":"CIOT"
                },
                "cmd":"stop",
                "timestamp":1646978181926,
                "title":"requestRobtoControl",
                "uuid":tuuid.hex
            }
        )
        topic = self.topic_recv+'/'+vendor + '/'+robot_name
        self.rq.publish(topic,playload)
        ''' Command the robot to stop.
            Return True if robot has successfully stopped. Else False'''
        # print(f"RobotClientAPI stop :Name:{robot_name}")
        return True

    # 计算机器人到达目标导航点的剩余时间，单位：秒
    def navigation_remaining_duration(self, robot_name: str):
        ''' Return the number of seconds remaining for the robot to reach its
            destination'''
        print("navigation_remaining_duration")
        return 0.0

    # 导航完成
    def navigation_completed(self, robot_name: str):
        ''' Return True if the robot has successfully completed its previous
            navigation request. Else False.'''
        robot_info = self.get_robot_info(robot_name)
        # print(f"navigation_completed :curr:{robot_name}  Position X:{robot_info.x} Y:{robot_info.y} Theta: {robot_info.theta}" )
        # print(f"navigation_completed :navi:{robot_name}  Position X:{robot_info.navigate[0]} Y:{robot_info.navigate[1]} Theta: {robot_info.navigate[2]}" )
        
        # if(robot_info.navigation_completed_flag == True):
        if(abs(robot_info.x-robot_info.navigate[0])<0.5 and abs(robot_info.x-robot_info.navigate[0])<0.5):
            return True
        # print("navigation not completed")
        return False

    # 任务执行完成
    def process_completed(self, robot_name: str):
        ''' Return True if the robot has successfully completed its previous
            process request. Else False.'''
        return False

    # 获取机器人当前电量，值范围 0.0-1.0,失败返回 None
    def battery_soc(self, robot_name: str):
        ''' Return the state of charge of the robot as a value between 0.0
            and 1.0. Else return None if any errors are encountered'''
        robot_info = self.get_robot_info(robot_name)
        soc = 0
        if robot_info is not None:
            soc = robot_info.battery_soc/100.0
            print(f"RobotClient battery_soc:Name:{robot_name}  Battery_Soc X:{soc} " )
        if soc >1:
            soc =1
        return soc

