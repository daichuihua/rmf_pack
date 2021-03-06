#!/usr/bin/env python3

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

import sys
import math
import yaml
import argparse
import requests
import json
import time
import logging

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_system_default

from rclpy.qos import QoSProfile
from rclpy.qos import QoSHistoryPolicy as History
from rclpy.qos import QoSDurabilityPolicy as Durability
from rclpy.qos import QoSReliabilityPolicy as Reliability

from rmf_fleet_msgs.msg import RobotState, Location, PathRequest, \
    DockSummary, ModeRequest, ModeParameter

import rmf_adapter as adpt
import rmf_adapter.vehicletraits as traits
import rmf_adapter.geometry as geometry

import numpy as np

from fastapi import FastAPI
import uvicorn
from typing import Optional
from pydantic import BaseModel

import threading
app = FastAPI()


class Request(BaseModel):
    map_name: str
    task: Optional[str] = None
    destination: Optional[dict] = None
    data: Optional[dict] = None


# ------------------------------------------------------------------------------
# Fleet Manager
# ------------------------------------------------------------------------------
class State:
    def __init__(self, state: RobotState = None, destination: Location = None):
        self.state = state
        self.destination = destination


class FleetManager(Node):
    def __init__(self, config, nav_path):
        self.config = config
        self.fleet_name = self.config["rmf_fleet"]["name"]

        super().__init__(f'{self.fleet_name}_fleet_manager')

        self.robots = {}  # Map robot name to state
        self.docks = {}  # Map dock name to waypoints

        for robot_name, robot_config in self.config["robots"].items():
            self.robots[robot_name] = State()
        assert(len(self.robots) > 0)

        profile = traits.Profile(geometry.make_final_convex_circle(
            self.config['rmf_fleet']['profile']['footprint']),
            geometry.make_final_convex_circle(
                self.config['rmf_fleet']['profile']['vicinity']))
        self.vehicle_traits = traits.VehicleTraits(
            linear=traits.Limits(
                *self.config['rmf_fleet']['limits']['linear']),
            angular=traits.Limits(
                *self.config['rmf_fleet']['limits']['angular']),
            profile=profile)
        self.vehicle_traits.differential.reversible =\
            self.config['rmf_fleet']['reversible']

        self.create_subscription(
            RobotState,
            'robot_state',
            self.robot_state_cb,
            100)

        transient_qos = QoSProfile(
            history=History.RMW_QOS_POLICY_HISTORY_KEEP_LAST,
            depth=1,
            reliability=Reliability.RMW_QOS_POLICY_RELIABILITY_RELIABLE,
            durability=Durability.RMW_QOS_POLICY_DURABILITY_TRANSIENT_LOCAL)

        self.create_subscription(
            DockSummary,
            'dock_summary',
            self.dock_summary_cb,
            qos_profile=transient_qos)

        self.path_pub = self.create_publisher(
            PathRequest,
            'robot_path_requests',
            qos_profile=qos_profile_system_default)

        self.mode_pub = self.create_publisher(
            ModeRequest,
            'robot_mode_requests',
            qos_profile=qos_profile_system_default)

        self.task_id = -1

        @app.get('/open-rmf/rmf_demos_fm/status/')
        async def position(robot_name: Optional[str] = None):
            data = {'data': {},
                    'success': False,
                    'msg': ''}
            if robot_name is None:
                data['data']['all_robots'] = []
                for robot_name in self.robots:
                    state = self.robots.get(robot_name)
                    if state is None or state.state is None:
                        return data
                    data['data']['all_robots'].append(
                        self.get_robot_state(state, robot_name))
            else:
                state = self.robots.get(robot_name)
                if state is None or state.state is None:
                    return data
                data['data'] = self.get_robot_state(state, robot_name)
            data['success'] = True
            return data

        @app.post('/open-rmf/rmf_demos_fm/navigate/')
        async def navigate(robot_name: str, dest: Request):
            data = {'success': False, 'msg': ''}
            if (robot_name not in self.robots or len(dest.destination) < 1):
                return data

            target_x = dest.destination['x']
            target_y = dest.destination['y']
            target_yaw = dest.destination['yaw']
            target_map = dest.map_name

            t = self.get_clock().now().to_msg()

            path_request = PathRequest()
            state = self.robots[robot_name]
            cur_x = state.state.location.x
            cur_y = state.state.location.y
            cur_yaw = state.state.location.yaw
            cur_loc = state.state.location
            path_request.path.append(cur_loc)

            disp = self.disp([target_x, target_y], [cur_x, cur_y])
            duration = int(disp/self.vehicle_traits.linear.nominal_velocity) +\
                int(abs(abs(cur_yaw) - abs(target_yaw)) /
                    self.vehicle_traits.rotational.nominal_velocity)
            t.sec = t.sec + duration
            target_loc = Location()
            target_loc.t = t
            target_loc.x = target_x
            target_loc.y = target_y
            target_loc.yaw = target_yaw
            target_loc.level_name = target_map

            path_request.fleet_name = self.fleet_name
            path_request.robot_name = robot_name
            path_request.path.append(target_loc)
            self.task_id = self.task_id + 1
            path_request.task_id = str(self.task_id)
            self.path_pub.publish(path_request)

            self.robots[robot_name].destination = target_loc

            data['success'] = True
            print(f'sssssssssssmanagerthe robot is navigating')
            
            logging.warning(f'loggingubhmanager')
            '''
            if "tinyRobot2"== path_request.robot_name.strip():
                if 16.70<target_x<16.90:
                    logging.warning(f"ubh...........start control mbot moving...... {path_request.robot_name},{target_x},{target_y},{target_yaw},{disp},{duration}")
                    url="http://10.21.88.186:8092//aimbot-api/robotManage/robotNavigate?token=026158c605237abb44c2231c7315110e"
                    headers={'Content-Type':'application/json'}
                    payload=json.dumps({"content":{
                    "mapName": "victor-1204",
		            "sn": "Aimbot.01.b0416f03a85a",
		            "theta": 2.23,
		            "x": 0.26,
		            "y": -0.64
	                },
	                "timestamp": 0,
	                "title": "",
	                "uuid": ""})
                    response=requests.request("POST",url,headers=headers,data=payload)
                else:
                    print(f"False")    
            else:
                print(f"False")
            '''

            """
            if(target_x == 10.433053704916215) :
                return data
            else:
                url="http://10.21.88.186:8092//aimbot-api/robotManage/robotMove?token=026158c605237abb44c2231c7315110e"
                headers={'Content-Type':'application/json'}
                payload=json.dumps({"content":{
                    "sn": "Aimbot.01.b0416f03a85a",
		            "speed": 0.5,
		            "theta": 0.2,
		            "x": 0.5,
		            "y": 0
	                },
	                "timestamp": 0,
	                "title": "",
	                "uuid": ""})
                response=requests.request("POST",url,headers=headers,data=payload)
            """
            """
            url="http://10.21.88.186:8092//aimbot-api/robotManage/liftingMove?token=026158c605237abb44c2231c7315110e"
            headers={'Content-Type':'application/json'}

            payload=json.dumps({"content":{
                "action":"move",
                "position":100,
                "sn":"Aimbot.01.b0416f03a85a",
                "speed":100},
                "timestamp":0,
                "title":"","uuid":""})
            response=requests.request("POST",url,headers=headers,data=payload)
            """
            
            return data

        @app.get('/open-rmf/rmf_demos_fm/stop_robot/')
        async def stop(robot_name: str):
            data = {'success': False, 'msg': ''}
            if robot_name not in self.robots:
                return data
            path_request = PathRequest()
            path_request.fleet_name = self.fleet_name
            path_request.robot_name = robot_name
            path_request.path = []
            self.task_id = self.task_id + 1
            path_request.task_id = str(self.task_id)
            self.path_pub.publish(path_request)
            data['success'] = True
            return data

        @app.post('/open-rmf/rmf_demos_fm/start_task/')
        async def start_process(robot_name: str, task: Request):
            data = {'success': False, 'msg': ''}
            if (robot_name not in self.robots or
                    len(task.task) < 1 or
                    task.task not in self.docks):
                return data

            t = self.get_clock().now().to_msg()

            mode_request = ModeRequest()
            mode_request.fleet_name = self.fleet_name
            mode_request.robot_name = robot_name
            self.task_id = self.task_id + 1
            mode_request.task_id = str(self.task_id)
            mode_request.mode.mode = mode_request.mode.MODE_DOCKING
            dock = ModeParameter()
            dock.name = 'docking'
            dock.value = task.task
            mode_request.parameters = [dock]
            self.mode_pub.publish(mode_request)

            path_request = PathRequest()
            state = self.robots[robot_name]
            cur_x = state.state.location.x
            cur_y = state.state.location.y
            cur_yaw = state.state.location.yaw
            cur_loc = state.state.location
            path_request.path.append(cur_loc)

            for wp in self.docks[task.task]:

                target_x = wp.x
                target_y = wp.y
                target_yaw = wp.yaw

                disp = self.disp([target_x, target_y], [cur_x, cur_y])
                duration = int(disp /
                               self.vehicle_traits.linear.nominal_velocity) +\
                    int(abs(abs(cur_yaw) - abs(target_yaw)) /
                        self.vehicle_traits.rotational.nominal_velocity)
                t.sec = t.sec + duration
                target_loc = Location()
                target_loc.t = t
                target_loc.x = target_x
                target_loc.y = target_y
                target_loc.yaw = target_yaw
                target_loc.level_name = wp.level_name

                path_request.path.append(target_loc)

            path_request.fleet_name = self.fleet_name
            path_request.robot_name = robot_name
            self.task_id = self.task_id + 1
            path_request.task_id = str(self.task_id)
            self.path_pub.publish(path_request)

            self.robots[robot_name].destination = target_loc

            data['success'] = True
            return data

    def robot_state_cb(self, msg):
        if (msg.name in self.robots):
            self.robots[msg.name].state = msg
            # Check if robot has reached destination
            state = self.robots[msg.name]
            if state.destination is None:
                return
            destination = state.destination
            if ((msg.mode.mode == 0 or msg.mode.mode == 1) and
                    len(msg.path) == 0):
                self.robots[msg.name].destination = None

    def dock_summary_cb(self, msg):
        for fleet in msg.docks:
            if(fleet.fleet_name == self.fleet_name):
                for dock in fleet.params:
                    self.docks[dock.start] = dock.path

    def get_robot_state(self, state, robot_name):
        data = {}
        position = [state.state.location.x, state.state.location.y]
        angle = state.state.location.yaw
        data['robot_name'] = robot_name
        data['map_name'] = state.state.location.level_name
        data['position'] =\
            {'x': position[0], 'y': position[1], 'yaw': angle}
        data['battery'] = state.state.battery_percent
        data['completed_request'] = False
        if state.destination is not None:
            destination = state.destination
            # calculate arrival estimate
            dist_to_target =\
                self.disp(position, [destination.x, destination.y])
            ori_delta = abs(abs(angle) - abs(destination.yaw))
            if ori_delta > np.pi:
                ori_delta = ori_delta - (2 * np.pi)
            if ori_delta < -np.pi:
                ori_delta = (2 * np.pi) + ori_delta
            duration = (dist_to_target /
                        self.vehicle_traits.linear.nominal_velocity +
                        ori_delta /
                        self.vehicle_traits.rotational.nominal_velocity)
            data['destination_arrival_duration'] = duration
        else:
            data['destination_arrival_duration'] = 0.0
            data['completed_request'] = True
        return data

    def disp(self, A, B):
        return math.sqrt((A[0]-B[0])**2 + (A[1]-B[1])**2)


# ------------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------------
def main(argv=sys.argv):
    # Init rclpy and adapter
    rclpy.init(args=argv)
    adpt.init_rclcpp()
    args_without_ros = rclpy.utilities.remove_ros_args(argv)

    parser = argparse.ArgumentParser(
        prog="fleet_adapter",
        description="Configure and spin up the fleet adapter")
    parser.add_argument("-c", "--config_file", type=str, required=True,
                        help="Path to the config.yaml file")
    parser.add_argument("-n", "--nav_graph", type=str, required=True,
                        help="Path to the nav_graph for this fleet adapter")
    args = parser.parse_args(args_without_ros[1:])
    print(f"Starting fleet manager...")

    with open(args.config_file, "r") as f:
        config = yaml.safe_load(f)

    fleet_manager = FleetManager(config, args.nav_graph)

    spin_thread = threading.Thread(target=rclpy.spin, args=(fleet_manager,))
    spin_thread.start()

    uvicorn.run(app,
                host=config['rmf_fleet']['fleet_manager']['ip'],
                port=config['rmf_fleet']['fleet_manager']['port'],
                log_level='warning')


if __name__ == '__main__':
    main(sys.argv)
