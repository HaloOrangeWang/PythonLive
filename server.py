import zmq
import pika

CLIENT_HOST = "tcp://*:28125"
USERNAME = 'admin'  # AMQP的用户名和密码
PASSWORD = 'admin'
AMQP_HOST = 'localhost'  # AMQP的服务器地址
QUEUE_NAME = 'StreamQueue1'  # 从哪个队列中接收消息


class CommStreamer:
    """直播服务器和博主的通信"""

    def __init__(self, server_callback_func):
        user_pwd = pika.PlainCredentials(USERNAME, PASSWORD)
        s_conn = pika.BlockingConnection(pika.ConnectionParameters(AMQP_HOST,
                                                                   credentials=user_pwd))
        self.channel = s_conn.channel()
        self.server_callback_func = server_callback_func

    def recv_msg_call(self, ch, method, properties, body):
        """从AMQP处获取到消息之后，这个函数会被自动调用"""
        self.server_callback_func(body)

    def consume_loop(self):
        """主循环"""
        # 设置接收到消息后的操作，自动从队列中删除，且调用前面的函数
        self.channel.basic_consume(queue=QUEUE_NAME,
                                   on_message_callback=self.recv_msg_call, auto_ack=True)
        self.channel.start_consuming()  # 开始订阅数据


class CommClient:
    """直播服务器和观众的通信"""

    def __init__(self):
        context = zmq.Context()  # 初始化ZeroMQ
        self.sock = context.socket(zmq.PUB)  # 确定通信模式为Pub/Sub模式
        self.sock.bind(CLIENT_HOST)

    def pub_msg(self, msg_bytes):
        """发送一条消息"""
        self.sock.send(msg_bytes)


class Server:

    def __init__(self):
        # 需要初始化两条连接，分别是和观众的连接，以及和博主的连接
        self.client_comm_obj = CommClient()
        self.streamer_comm_obj = CommStreamer(self.recv_msg_callback_func)

    def main_loop(self):
        """主循环"""
        self.streamer_comm_obj.consume_loop()

    def recv_msg_callback_func(self, msg_bytes):
        """接收到数据后，自动调用"""
        self.client_comm_obj.pub_msg(msg_bytes)


def main():
    server = Server()
    server.main_loop()


if __name__ == '__main__':
    main()
