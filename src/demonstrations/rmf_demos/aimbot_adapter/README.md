r# rmf_demos_fleet_adapter

This is an implementation of the python based [fleet adapter template](https://github.com/open-rmf/fleet_adapter_template) on selected RMF demo worlds: Hotel, Office, Airport Terminal and Clinic. 

The fleet adapter uses FastAPI to:
- Receive robot state information
- Send task and navigation commands to the simulation robot

You can also interact with the endpoints with FastAPI's automatic documentation. First launch a demo world, then visit the base URL with `/docs` appended at the end. Do take note that the port number for ea
ch demo fleet is specified in `rmf_demos/rmf_demos/config/`.

#### Example
Using the Office World as an example, first launch `office.launch.xml`:
```bash
source ~/rmf_ws/install/setup.bash
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release
ros2 launch rmf_demos_gz office.launch.xml
```
Then visit http://127.0.0.1:8001/docs in your browser to interact with the endpoints.

## Request/Response Schemas
Depending on the endpoint, the content may vary (i.e. some items may be removed), but a general structure is followed:
##### Request Body
```json
{
  "map_name": "string",
  "destination": {},
  "data": {}
}
```
##### Response Body
```json
{
  "data": {},
  "success": true,
  "msg": ""
}
```

## API Endpoints

Note: The base URL in this section contains the port number `8001` dedicated to the tinyRobot fleet. The port number varies across different fleets.

### 1. Get Robot Status
The `status` endpoint allows the fleet adapter to access robot state information such as its current position and battery level. This endpoint does not require a Request Body.

There are two ways to request the fleet robot status:

#### a. Get status of all robots in the fleet
Request URL: `http://127.0.0.1:8001/open-rmf/rmf_demos_fm/status/`
##### Response Body:
```json
{
  "data": {
    "all_robots": [
      {
        "robot_name": "tinyRobot1",
        "map_name": "L1",
        "position": {
          "x": 10.0,
          "y": 20.0,
          "yaw": 1.0
        },
        "battery": 100,
        "completed_request": true,
        "destination_arrival_duration": 0
      },
      {
        "robot_name": "tinyRobot2",
        "map_name": "L1",
        "position": {
          "x": 5.0,
          "y": 25.0,
          "yaw": 1.4
        },
        "battery": 100,
        "completed_request": true,
        "destination_arrival_duration": 0
      }
    ]
  },
  "success": true,
  "msg": ""
}
```

#### b. Get status of specified robot in the fleet
Append a `robot_name` query parameter to the end of the URL.

Request URL: `http://127.0.0.1:8001/open-rmf/rmf_demos_fm/status/?robot_name=tinyRobot1`
##### Response Body:
```json
{
  "data": {
    "robot_name": "tinyRobot1",
    "map_name": "L1",
    "position": {
      "x": 10.0,
      "y": 20.0,
      "yaw": 1.0
    },
    "battery": 100,
    "completed_request": true,
    "destination_arrival_duration": 0
  },
  "success": true,
  "msg": ""
}
```

### 2. Send Navigation Request
The `navigate` endpoint allows the fleet adapter to send navigation waypoints to a specified robot. This endpoint requires a Request Body and a `robot_name` query parameter.

Request URL: `http://127.0.0.1:8001/open-rmf/rmf_demos_fm/navigate/?robot_name=tinyRobot1`
##### Request Body:
```json
{
  "map_name": "L1",
  "destination": {
    "x": 7.0,
    "y": 3.5,
    "yaw": 0.5
  }
}
```

##### Response Body:
```json
{
  "success": true,
  "msg": ""
}
```

### 3. Stop Robot
The `stop` endpoint allows the fleet adapter to command a specified robot to stop. This endpoint only requires a `robot_name` query parameter.

Request URL: `http://127.0.0.1:8001/open-rmf/rmf_demos_fm/stop/?robot_name=tinyRobot1`
##### Response Body:
```json
{
  "success": true,
  "msg": ""
}
```

### 4. Send Task Request
The `start_task` endpoint allows the fleet adapter to send task requests to a specified robot. This endpoint requires a Request Body and a `robot_name` query parameter.

Request URL: `http://127.0.0.1:8001/open-rmf/rmf_demos_fm/start_task/?robot_name=tinyRobot1`
##### Request Body:
```json
{
  "map_name": "L1",
  "task": "clean_lobby"
}
```

##### Response Body:
```json
{
  "success": true,
  "msg": ""
}
```
