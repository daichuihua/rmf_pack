# Copyright 2021 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


'''
    The RobotAPI class is a wrapper for API calls to the robot. Here users
    are expected to fill up the implementations of functions which will be used
    by the RobotCommandHandle. For example, if your robot has a REST API, you
    will need to make http request calls to the appropriate endpoints within
    these functions.
'''

import sys
import json
import hashlib
import time  # 引入time模块
import uuid
import logging
import yaml
#import rclpy
#import rclpy.node
import requests
from urllib.error import HTTPError

class RobotAPI:
    # The constructor below accepts parameters typically required to submit
    # http requests. Users should modify the constructor as per the
    # requirements of their robot's API
    def __init__(self, prefix: str = '', user: str = '', password: str = ''):
        # read config.yml
        with open("/home/dch/aimbot.yaml", "r") as f:
             config_yaml = yaml.safe_load(f)

        self.token = ""
        self.prefix = prefix
        self.server_yml = config_yaml['aimbot']['server']
        self.robot_yml = config_yaml['aimbot']['robots']['robot_list']

        #conv list to dict
        self.robot_list ={}
        for v in self.robot_yml:
            self.robot_list[v[0]] = v[1]

        #conv url_list to dict
        self.url_list = {}
        t_url = self.server_yml['url_list']
        for v in t_url:
            self.url_list[v[0]] = v[1]

        self.map_list={}
        self.battery={}

        #config 
        self.user = self.server_yml['user']
        self.pwd = self.server_yml['password']
        self.timeout = 5.0
        self.debug = False
        self.offset_x = self.server_yml['map_offset_x']
        self.offset_y = self.server_yml['map_offset_y']

        #url
        self.url_base = "http://" + self.server_yml['ip'] + ":" + str(self.server_yml['port'])

        #print
        print(f'serverurl_base_yml:{self.url_base}')            
        print(f'robots_yml:'+self.robot_list.get('tinyRobot1',""))

        #get token
        self.get_token()
        #self.get_bettary_info('tinyRobot1')
        #self.battery_soc('tinyRobot1')

    def get_robot_info(self,robot_name = None):
        robot_sn = self.robot_list.get(robot_name,"")        
        if robot_sn not in self.map_list:
            url = self.get_url('getinfo')
            
            # logging.warning(f'UBH: get poistion {url},    robot:{robot_name}, sn:{robot_sn}')
            headers={'Content-Type':'application/json'}
            #robot_str = '"' + robot_sn} + '"'
            payload=json.dumps(
                                    {
                                                "content":  robot_sn,
                                                "sn": robot_sn,
                                                "timestamp": 0,
                                                "title": "request_robot_query_info_timer",
                                                "uuid": "E4162BC1D93B4D7EA2EC7BD28CC9119D"
                                    }
            )
            #print(f'Response: {payload}')               
            response=requests.request("POST",url,headers=headers,data=payload)
            #print(f'Response: {response.json()}')
            response.raise_for_status()
            
            data = response.json()
            map = self.map_list[robot_sn] = data['data']['content']['robot_info']['current_map']
            # logging.warning(f'UBH: get map {map}')

        return self.map_list.get(robot_sn)

    def get_bettary_info(self,robot_name = None):
        robot_sn = self.robot_list.get(robot_name,"")  
        url = self.get_url('getinfo')
        headers={'Content-Type':'application/json'}
        payload=json.dumps(
                                    {
                                                "content":  robot_sn,
                                                "sn": robot_sn,
                                                "timestamp": 0,
                                                "title": "request_robot_query_info_timer",
                                                "uuid": "E4162BC1D93B4D7EA2EC7BD28CC9119D"
                                    }
                                                

            )
            #print(f'Response: {payload}')               
        response=requests.request("POST",url,headers=headers,data=payload)
            #print(f'Response: {response.json()}')
        response.raise_for_status()
            
        data = response.json()
        battery = self.battery[robot_sn] = data['data']['content']['battery_info']['level']  
        # print(f'battery: {battery}')

    def get_token(self, robot_name=None): 

        url =self.get_url('token')
        print(f'token_url:{url}')

        headers={'Content-Type':'application/json'}
        pwdsh1= hashlib.sha1()
        pwdsh1.update(self.pwd.encode("utf-8"))        
        payload=json.dumps({"content":{
                "password":pwdsh1.hexdigest(),
                "username":self.user},
                "timestamp":0,
                "title":"","uuid":""})

        response=requests.request("POST",url,headers=headers,data=payload)
        # print(response.text)
        js = json.loads(response.text)
        self.token =js['data']['token']
        self.uuid = js['uuid']

        print(f'token:{self.token}')
        print(f'uuid: {self.uuid}')

    def get_url(self,cmdtype:str):
        url = self.url_base + self.url_list.get(cmdtype) + "?token=" + self.token
        return url


    def check_connection(self):
        ''' Return True if connection to the robot API server is successful'''
        if self.data() is None:
            return False
        return True

    def position(self, robot_name: str):
        ''' Return [x, y, theta] expressed in the robot's coordinate frame or
            None if any errors are encountered'''
        if robot_name is not None:
            url = self.prefix +\
                f'/open-rmf/rmf_demos_fm/status/?robot_name={robot_name}'
        else:
            url = self.prefix + f'/open-rmf/rmf_demos_fm/status'
        try:

            url = self.get_url('robotcmd')
            robot_sn = self.robot_list.get(robot_name,"")

            # logging.warning(f'UBH: get poistion {url},    robot:{robot_name}, sn:{robot_sn}')
            headers={'Content-Type':'application/json'}
            payload=json.dumps(
                                    {
                                        "content": {
                                            "data": {
                                                "content": {
                                                    "cameraEnable": "0",
                                                    "id": "E4162BC1D93B4D7EA2EC7BD28CC9119D",
                                                    "timestamp": 0,
                                                    "uuid": "E4162BC1D93B4D7EA2EC7BD28CC9119D"
                                                },
                                                "locked": 0,
                                                "title": "request_patrol_info"
                                            },
                                            "domain": "ROBOT_CONTROLLER",
                                            "sn": robot_sn,
                                            "type": "update_syn"
                                        },
                                        "timestamp": 0,
                                        "title": "request_deploy_coord",
                                        "uuid": "E4162BC1D93B4D7EA2EC7BD28CC9119D"
                                    }

                                )
            response=requests.request("POST",url,headers=headers,data=payload)
            # logging.warning(f'Response: {response.json()}')
            # print(f'Response: {response.json()}')
            response.raise_for_status()
            # logging.warning(f"after get poistion")
            data = response.json()

            x = data['data']['content']['position']['x']
            y = data['data']['content']['position']['y']
            angle = data['data']['content']['position']['theta']

            return [x, y, angle]
        except HTTPError as http_err:
            print(f'HTTP error: {http_err}')
        except Exception as err:
            print(f'Other error: {err}')
        return None
    
    def navigate(self, robot_name: str, pose, map_name: str):
        ''' Request the robot to navigate to pose:[x,y,theta] where x, y and
            and theta are in the robot's coordinate convention. This function
            should return True if the robot has accepted the request,
            else False'''
        assert(len(pose) > 2)
        url = self.prefix +\
            f'/open-rmf/rmf_demos_fm/navigate/?robot_name={robot_name}'
        data = {}  # data fields: task, map_name, destination{}, data{}
        data['map_name'] = map_name
        data['destination'] = {'x': pose[0], 'y': pose[1], 'yaw': pose[2]}
        try:
            url = self.get_url('robotcmd')
            robot_sn = self.robot_list.get(robot_name,"")
            robot_map = self.get_robot_info(robot_name)

            logging.warning(f'Attention:.........ubh aimbot api for navigation {url},    robot:{robot_name},sn:{robot_sn}  x: {pose[0]},  y: {pose[1]},  yaw: {pose[2]}')

            headers={'Content-Type':'application/json'}
            payload=json.dumps(
                                    {
                                        "content": {
                                            "data": {
                                                "content": {
                                                    "action": "photo",
                                                    "camera": {
                                                        "aperture": 1900,
                                                        "brightness": 50,
                                                        "cameraEnable": 0,
                                                        "continuousPhotograph": 0,
                                                        "contrast": 50,
                                                        "exposureMode": 1,
                                                        "fillLight": "false",
                                                        "focus": 33103,
                                                        "focusMode": 1,
                                                        "periodInMs": 200,
                                                        "photoNumber": 1,
                                                        "pitch": -10.550000190734863,
                                                        "shutter": 17,
                                                        "yaw": 343.6499938964844,
                                                        "zoom": 2
                                                    },
                                                    "command": "start",
                                                    "elevator": {
                                                        "height": 0
                                                    },
                                                    "id": "A6225179697443718586F3B89A273C8A",
                                                    "position": {
                                                        "map": robot_map,
                                                        # "orientW": 0.712127,
                                                        # "orientZ": -0.70205,
                                                        "theta": pose[2],
                                                        "x": pose[0],
                                                        "y": pose[1]
                                                    },
                                                    "timestamp": 0
                                                },
                                                "locked": 0,
                                                "title": "request_patrol_navigate_to"
                                            },
                                            "domain": "ROBOT_CONTROLLER",
                                            "sn": robot_sn,
                                            "type": "update",
                                            "waitTime": 10
                                        },
                                        "timestamp": 1640601417453,
                                        "title": "request_remote_start_navigation",
                                        "uuid": "A6225179697443718586F3B89A273C8A"
                                    }

                                )
            response=requests.request("POST",url,headers=headers,data=payload)
            response.raise_for_status()
            # logging.warning(f"trybeforedebug")
            # logging.warning(f"Response: {response.json()}    navigation result: {response.json()['data']['content']['result']}")
            if(response.json()['data']['content']['result'] == 'success'):
                return True
            else:
                return False
        except HTTPError as http_err:
            print(f'HTTP error: {http_err}')
        except Exception as err:
            print(f'Other error: {err}')
        return False

    def start_process(self, robot_name: str, process: str, map_name: str):
        ''' Request the robot to begin a process. This is specific to the robot
            and the use case. For example, load/unload a cart for Deliverybot
            or begin cleaning a zone for a cleaning robot.
            Return True if the robot has accepted the request, else False'''
        url = self.prefix +\
            f"/open-rmf/rmf_demos_fm/start_task?robot_name={robot_name}"
        # data fields: task, map_name, destination{}, data{}
        data = {'task': process, 'map_name': map_name}
        try:
            response = requests.post(url, timeout=self.timeout, json=data)
            response.raise_for_status()
            # if self.debug:
            #     print(f'Response: {response.json()}')
            return response.json()['success']
        except HTTPError as http_err:
            print(f'HTTP error: {http_err}')
        except Exception as err:
            print(f'Other error: {err}')
        return False

    def stop(self, robot_name: str):
        ''' Command the robot to stop.
            Return True if robot has successfully stopped. Else False'''
        url = self.prefix +\
            f'/open-rmf/rmf_demos_fm/stop_robot?robot_name={robot_name}'
        try:
            '''
            response = requests.get(url, self.timeout)
            response.raise_for_status()
            if self.debug:
                print(f'Response: {response.json()}')
            return response.json()['success']
            '''
          
            url = self.get_url('robotcmd')
            robot_sn = self.robot_list.get(robot_name,"")

            # logging.warning(f'..UBH stop command: {url},    robot:{robot_name} sn:{robot_sn},  stop')
            headers={'Content-Type':'application/json'}
            payload=json.dumps(
                                    {
                                        "content": {
                                            "data": {
                                                "content": {
                                                    "action": "empty",
                                                    "command": "stop",
                                                    "id": "F2D8C6DDBD1D4E49B85E2D87CA7319D2",
                                                    "timestamp": 0
                                                },
                                                "locked": 0,
                                                "title": "request_patrol_navigate_to"
                                            },
                                            "domain": "ROBOT_CONTROLLER",
                                            "sn": robot_sn,
                                            "type": "update",
                                            "waitTime": 10
                                        },
                                        "timestamp": 0,
                                        "title": "request_remote_stop_navigation",
                                        "uuid": "F2D8C6DDBD1D4E49B85E2D87CA7319D2"
                                    }

                                )
            response=requests.request("POST",url,headers=headers,data=payload)
            # print(f'Response: {response.json()}')
            response.raise_for_status()

            if(response.json()['data']['content']['result'] == 'success'):
                return True
            else:
                return False
        except HTTPError as http_err:
            print(f'HTTP error: {http_err}')
        except Exception as err:
            print(f'Other error: {err}')
        return False

    def navigation_remaining_duration(self, robot_name: str):
        ''' Return the number of seconds remaining for the robot to reach its
            destination'''
        response = self.data(robot_name)
        if response is not None:
            return response['data']['destination_arrival_duration']
        else:
            return 0.0

    def navigation_completed(self, robot_name: str):
        ''' Return True if the robot has successfully completed its previous
            navigation request. Else False.'''
        '''
        response = self.data(robot_name)
        if response is not None and response.get('data') is not None:
            return response['data']['completed_request']
        else:
            return False
        '''
        
        url = self.get_url('robotcmd')
        robot_sn = self.robot_list.get(robot_name,"")
        # logging.warning(f'........ {url},    robot:{robot_name} sn:{robot_sn},  get the status for navigation completed')

        headers={'Content-Type':'application/json'}
        payload=json.dumps(
                                {
                                    "content": {
                                        "data": {
                                            "content": {
                                                "id": "83958F9C0C334366A668F9705F648243",
                                                "timestamp": 1640601012434
                                            },
                                            "locked": 0,
                                            "title": "request_patrol_status"
                                        },
                                        "sn": robot_sn
                                    },
                                    "sn": robot_sn,
                                    "timestamp": 1640601012434,
                                    "title": "request_patrol_status",
                                    "uuid": "83958F9C0C334366A668F9705F648243"
                                }


                            )
        response=requests.request("POST",url,headers=headers,data=payload)
        # print(f'Response: {response.json()}')


        if(response.json()['data']['content']['result'] == 'success' and response.json()['data']['content']['status'] == 'idle'):
            return True
        else:
            return False
        
    def process_completed(self, robot_name: str):
        ''' Return True if the robot has successfully completed its previous
            process request. Else False.'''
        return self.navigation_completed(robot_name)

    def battery_soc(self, robot_name: str):
        ''' Return the state of charge of the robot as a value between 0.0
            and 1.0. Else return None if any errors are encountered'''
        #response = self.data(robot_name)
        robot_sn = self.robot_list.get(robot_name,"")
        self.get_bettary_info(robot_name)
        battery_val = float(self.battery.get(robot_sn,""))
        '''
        if response is not None:
            return response['data']['battery']/100.0
        else:
            return None
        '''
        battery_per = battery_val / 100.0
        # print(f'aimbot battery: {str(battery_per)}')

        return battery_per

    def data(self, robot_name=None):
        if robot_name is None:
            url = self.prefix + f'/open-rmf/rmf_demos_fm/status/'
        else:
            url = self.prefix +\
                f'/open-rmf/rmf_demos_fm/status?robot_name={robot_name}'
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            # if self.debug:
            #     print(f'Response: {response.json()}')
            return response.json()
        except HTTPError as http_err:
            print(f'HTTP error: {http_err}')
        except Exception as err:
            # print(f'Other error: {err}')
            # print(f'注意数据')
            pass
        return None
'''
def main(argv=sys.argv):
    robot = RobotAPI()

if __name__ == '__main__':
    main(sys.argv)
'''
