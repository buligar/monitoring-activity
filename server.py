import sys
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
import datetime
import time


class ServerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client_table = None
        self.client_sockets = []
        self.client_activity = {}
        self.initUI()

    def initUI(self):
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('Сервер')

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        self.client_table = QTableWidget(self)
        self.client_table.setColumnCount(6)
        self.client_table.setHorizontalHeaderLabels(['IP адрес', 'Порт', 'Машина', 'Имя', 'Время последней активности', 'Статус'])
        layout.addWidget(self.client_table)
        central_widget.setLayout(layout)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_last_activity_times)
        self.update_timer.start(1000)

    def start_server(self):
        host = "172.21.48.1"
        port = 45454

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)

        print(f"Сервер запущен на {host}:{port}")

        while True:
            client_socket, addr = server_socket.accept()
            print(f"Подключено клиент: {addr[0]}:{addr[1]}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_handler.start()
            self.add_client_to_table(addr)
            self.client_sockets.append((client_socket, addr))
            self.update_activity_status(addr, "Активен")

    def add_client_to_table(self, addr):
        # Проверяем, есть ли уже запись с таким адресом
        for row in range(self.client_table.rowCount()):
            item = self.client_table.item(row, 0)
            if item and item.text() == addr[0]:
                # Если запись существует, обновляем только активность
                self.client_table.setItem(row, 5, QTableWidgetItem("Активен"))
                self.client_activity[addr] = True
                return

        # Если запись не найдена, добавляем новую
        row_position = self.client_table.rowCount()
        self.client_table.insertRow(row_position)
        self.client_table.setItem(row_position, 0, QTableWidgetItem(addr[0]))
        self.client_table.setItem(row_position, 1, QTableWidgetItem(str(addr[1])))
        self.client_table.setItem(row_position, 5, QTableWidgetItem("Активен"))
        self.client_activity[addr] = True

    def handle_client(self, client_socket, addr):
        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                print(f"Активность сотрудника ({addr[0]}:{addr[1]}): {data}")

                # Разделяем сообщение по разделителю "|"
                parts = data.split('|')
                if len(parts) == 3:
                    machine, user, lasttime = parts
                    self.update_client_info(addr, machine, user, lasttime)

                # Отправляем ответ клиенту
                response = "Received"
                client_socket.send(response.encode("utf-8"))

            except ConnectionResetError:
                print(f"Клиент {addr[0]}:{addr[1]} отключился")
                self.update_activity_status(addr, "Отключен")
                self.client_activity[addr] = False
                break

        client_socket.close()
        self.client_sockets.remove((client_socket, addr))

    def update_client_info(self, addr, machine, user, lasttime):
        for row in range(self.client_table.rowCount()):
            item = self.client_table.item(row, 0)
            if item and item.text() == addr[0]:
                self.client_table.setItem(row, 2, QTableWidgetItem(machine))
                self.client_table.setItem(row, 3, QTableWidgetItem(user))
                self.client_table.setItem(row, 4, QTableWidgetItem(lasttime))
                self.client_table.setItem(row, 5, QTableWidgetItem("Активен"))
                break

    def update_activity_status(self, addr, status):
        for row in range(self.client_table.rowCount()):
            item = self.client_table.item(row, 0)
            if item and item.text() == addr[0]:
                self.client_table.setItem(row, 5, QTableWidgetItem(status))
                break

    def update_last_activity_times(self):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in range(self.client_table.rowCount()):
            item = self.client_table.item(row, 0)
            if item and item.text() != "Отключен" and self.client_activity.get((item.text(), int(self.client_table.item(row, 1).text())), False):
                self.client_table.setItem(row, 4, QTableWidgetItem(current_time))


def monitor_clients():
    while True:
        time.sleep(5)
        for client_socket, addr in server_window.client_sockets:
            try:
                client_socket.send(b"ping")
            except:
                print(f"Клиент {addr[0]}:{addr[1]} не отвечает, отключаем его.")
                server_window.update_activity_status(addr, "Отключен")
                server_window.client_activity[addr] = False
                client_socket.close()
                server_window.client_sockets.remove((client_socket, addr))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    server_window = ServerWindow()
    server_window.show()

    server_thread = threading.Thread(target=server_window.start_server)
    server_thread.daemon = True
    server_thread.start()

    monitor_thread = threading.Thread(target=monitor_clients)
    monitor_thread.daemon = True
    monitor_thread.start()

    sys.exit(app.exec_())
