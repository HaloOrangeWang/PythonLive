from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLineEdit, QPushButton, QTextEdit
from PyQt5.QtGui import QFont
import traceback
import argparse
import sys
import pika


def run_with_exc(f):
    """游戏运行出现错误时，用messagebox把错误信息显示出来"""

    def call(window, **kwargs):
        try:
            return f(window, **kwargs)
        except Exception:
            exc_info = traceback.format_exc()
            QMessageBox.about(window, '错误信息', exc_info)
    return call


USERNAME = 'admin'  # AMQP的用户名和密码
PASSWORD = 'admin'
AMQP_HOST = 'localhost'  # AMQP的服务器地址
EXCHANGE_NAME = 'Stream1'  # 讲消息发送到哪个队列中


class Comm:

    def __init__(self):
        user_pwd = pika.PlainCredentials(USERNAME, PASSWORD)
        # 连接AMQP并登入
        s_conn = pika.BlockingConnection(pika.ConnectionParameters(AMQP_HOST, credentials=user_pwd))
        self.channel = s_conn.channel()

    def send_msg(self, stream_id, stream_msg):
        send_msg = '%d:%s' % (stream_id, stream_msg)  # 发送的消息内容应该包含直播间id和消息正文
        self.channel.basic_publish(exchange=EXCHANGE_NAME, routing_key='', body=send_msg)


class Streamer(QMainWindow):

    def __init__(self, stream_id):
        super().__init__()
        self.init_ui()
        self.comm_obj = Comm()  # 初始化通信工具
        self.stream_id = stream_id

    # noinspection PyAttributeOutsideInit
    def init_ui(self):
        # 1.确定界面的标题，大小
        self.setObjectName('MainWindow')
        self.setWindowTitle('直播服务器')
        self.setFixedSize(500, 400)

        # 2.初始化界面内容：LineEdit, 按钮和已发送内容
        self.send_content = QLineEdit(self)  # 要发送的内容输入框
        self.send_content.setFixedSize(360, 60)
        self.send_content.setFont(QFont("宋体", 18, QFont.Bold))
        self.send_content.move(20, 320)

        self.send_button = QPushButton(self)  # 发送按钮
        self.send_button.setFixedSize(80, 60)
        self.send_button.setText("发送")
        self.send_button.move(400, 320)
        self.send_button.clicked.connect(self.send_msg)

        self.send_hist = QTextEdit(self)  # 已发送内容的记录位置
        self.send_hist.setReadOnly(True)
        self.send_hist.setFixedSize(460, 280)
        self.send_hist.move(20, 20)

        # 3.显示界面
        self.show()

    @run_with_exc
    def send_msg(self):
        """将直播数据发送出去"""
        send_msg = self.send_content.text()
        if send_msg:
            self.comm_obj.send_msg(self.stream_id, send_msg)
            self.send_hist.append(send_msg)
        else:
            QMessageBox.about(self, '提示', '发送内容不能为空')


def main():
    parser2 = argparse.ArgumentParser()
    parser2.add_argument('stream_id', type=int)
    args = parser2.parse_args()

    app = QApplication(sys.argv)
    streamer = Streamer(args.stream_id)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
