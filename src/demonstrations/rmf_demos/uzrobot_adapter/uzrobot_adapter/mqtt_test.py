from robot_mqtt import RobotMqtt
import threading
import time
from RobotClientAPI import RobotAPI
# Initialize robot API for this fleet
api = RobotAPI("","","")

        # Test connectivity
         # 运行添加机器人线程
#mqtt = threading.Thread(target=api.mqtt_thread)
#mqtt.start()
robotlist = api.getrobotlist()
for robot in robotlist:
    api.addrobot('CIOT',robot)


#print(robotlist)
pos = [0,0,0]

pos[0] = 1.59
pos[1]= -0.85
pos[2] = 33
count = 0
while True:
    print(time.time())
    time.sleep(1)
    count+=1

    api.position("YHME1252C013C0SZGM2021001997")
    api.battery_soc("YHME1252C013C0SZGM2021001997")
    api.transforms_test()
    
    #print(pos)
    #if count == 10:
    api.navigate("YHME1252C013C0SZGM2021001997",pos,"")

    
'''
YHME1252C015C0SZGM522100075X
YHME1252C015C0SZGM522100074X
YHME1252C013C0SZGM2021001997
'''