from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTextEdit, QPushButton, QSpinBox
from PyQt5.QtCore import QTimer
import traceback
import sys
import zmq

HOST = 'tcp://127.0.0.1:28125'  # 服务器的ip和端口
RECV_INTERVAL = 0.1  # 多长时间接收一次程序


def run_with_exc(f):
    """游戏运行出现错误时，用messagebox把错误信息显示出来"""

    def call(window, **kwargs):
        try:
            return f(window, **kwargs)
        except Exception:
            exc_info = traceback.format_exc()
            QMessageBox.about(window, '错误信息', exc_info)
    return call


class Comm:

    def __init__(self):
        context = zmq.Context()
        self.sock = context.socket(zmq.SUB)  # 使用subscribe模式接受数据
        self.sock.connect(HOST)  # 连接服务器
        self.old_room_id = -1

    def get_msg(self):
        try:
            recv_msg = self.sock.recv(zmq.NOBLOCK)  # 以非阻塞模式接收数据
            return recv_msg.decode('utf_8')
        except zmq.error.Again:  # 没有数据的情况
            return str()

    def select_room(self, room_id):
        """新加的选择直播间功能"""
        if self.old_room_id != -1:
            old_filter_bytes = ('%d:' % self.old_room_id).encode('utf_8')
            self.sock.setsockopt(zmq.UNSUBSCRIBE, old_filter_bytes)  # 取消对前一个直播间数据的订阅
        # 订阅新的直播间数据
        filter_text = '%d:' % room_id  # 直播间编号
        filter_bytes = filter_text.encode('utf_8')
        self.sock.setsockopt(zmq.SUBSCRIBE, filter_bytes)  # 订阅新的直播间数据
        self.old_room_id = room_id


class Client(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.comm_obj = Comm()  # 初始化通信工具
        self.room_selected = False  # 是否已经选定了一个直播间

    # noinspection PyAttributeOutsideInit
    def init_ui(self):
        # 1.确定界面的标题，大小
        self.setObjectName('MainWindow')
        self.setWindowTitle('直播客户端')
        self.setFixedSize(400, 400)

        # 2.初始化界面内容：显示直播内容（TextEdit），进入哪一个直播间的SpinBox，以及确认的按钮
        self.recv_content = QTextEdit(self)  # 已发送内容的记录位置
        self.recv_content.setReadOnly(True)
        self.recv_content.setFixedSize(360, 300)
        self.recv_content.move(20, 80)
        self.room_select = QSpinBox(self)
        self.room_select.setFixedSize(80, 40)
        self.room_select.move(110, 20)
        self.room_select.setMinimum(0)
        self.room_select.setMaximum(99)
        self.confirm_button = QPushButton(self)
        self.confirm_button.setFixedSize(80, 40)
        self.confirm_button.move(210, 20)
        self.confirm_button.setText('进入直播间')
        self.confirm_button.clicked.connect(self.select_room)

        # 3.设置定时器，定时接收直播内容
        self.recv_timer = QTimer(self)
        self.recv_timer.timeout.connect(self.get_msg)
        self.recv_timer.start(RECV_INTERVAL * 1000)

        # 4.显示界面
        self.show()

    @run_with_exc
    def get_msg(self):
        if not self.room_selected:
            return  # 在没有选定直播间的时候，不从服务器获取任何数据
        while True:
            recv_msg = self.comm_obj.get_msg()
            if recv_msg:
                self.recv_content.append(recv_msg + '\n')
            else:
                break

    @run_with_exc
    def select_room(self):
        """选择一个特定的直播间"""
        self.recv_content.clear()  # 首先清空旧直播间中的内容
        room_id = self.room_select.value()
        self.comm_obj.select_room(room_id)  # 然后让底层协议选择性接收
        self.room_selected = True  # 最后打开标志位，允许接收该直播间的内容


def main():
    app = QApplication(sys.argv)
    live_client = Client()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
