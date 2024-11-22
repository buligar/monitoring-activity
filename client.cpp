#include <iostream>
#include <boost/asio.hpp>
#include <ctime>
#include <windows.h>

using namespace boost::asio;
using ip::tcp;

int main() {
    system("chcp 65001");
    io_service io;
    tcp::socket socket(io);

    try {
        // Подключение к серверу
        tcp::resolver resolver(io);
        tcp::resolver::query query("172.21.48.1", "45454");
        tcp::resolver::iterator endpoint_iterator = resolver.resolve(query);

        connect(socket, endpoint_iterator);

        std::cout << "Подключен к серверу." << std::endl;

        while (true) {
            char computerName[MAX_COMPUTERNAME_LENGTH + 1];
            DWORD computerNameSize = sizeof(computerName);
            GetComputerNameA(computerName, &computerNameSize);

            char userName[MAX_PATH];
            DWORD userNameSize = sizeof(userName);
            GetUserNameA(userName, &userNameSize);

            std::time_t currentTime = std::time(nullptr);
            std::string timeStr = std::ctime(&currentTime);

            // Формируем строку с информацией
            std::string info = std::string(computerName) + "|" + std::string(userName) + "|" + timeStr;

            // Отправляем информацию на сервер
            socket.write_some(boost::asio::buffer(info));

            Sleep(10000);
        }
    } catch (std::exception& e) {
        std::cerr << "Ошибка: " << e.what() << std::endl;
    }

    // Отключение от сервера (недостижимый код, так как есть бесконечный цикл выше)
    socket.close();
    std::cout << "Отключен от сервера." << std::endl;

    return 0;
}
