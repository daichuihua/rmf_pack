import random
import time

from paho.mqtt import client as mqtt_client


topic = 'python_mqtt' # 发布的主题，订阅时需要使用这个主题才能订阅此消息
# 随机生成一个客户端id
client_id = 'python-mqtt-{}'.format(random.randint(0, 1000))


def connect_mqtt():
    #连接mqtt服务器
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    # broker = 'broker.emqx.io'
    # port = 1883
    # client.connect(broker, port)
    client.connect(host='127.0.0.1', port=1883)
    return client


def publish(client):
    # 发布消息
    msg_count = 0
    while True:
        time.sleep(1)
        msg = '这是客户端发送的第{}条消息'.format(msg_count)
        result = client.publish(topic, msg)
        status = result[0]
        if status == 0:
            print('第{}条消息发送成功'.format(msg_count))
        else:
            print('第{}条消息发送失败'.format(msg_count))
        msg_count += 1


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)


if __name__ == '__main__':
    run()