import random
from paho.mqtt import client as mqtt_client

topic = "python_mqtt"
client_id = 'python-mqtt-{}'.format(random.randint(0, 100))

def connect_mqtt() -> mqtt_client:
    # 连接MQTT服务器
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

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        data = msg.payload.decode()
        print('订阅【{}】的消息为：{}'.format(msg.topic, data))
    client.subscribe(topic)
    client.on_message = on_message

def run():
    client = connect_mqtt()
    subscribe(client)
    client.loop_forever()

if __name__ == '__main__':
    run()