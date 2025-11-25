import socket
from time import sleep

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

raspi_ip = "172.20.10.2"#set as your raspi ip
s.settimeout(0.01)
s.bind((raspi_ip, 8003)) #raspi ip pand port
print("ip", raspi_ip, "port", 8003)

def socketReceive():
    while True:
        try:
            data, addrR = s.recvfrom(128)
            datastr=data.decode(encoding='UTF-8')
            return datastr
        except:
            return False
if __name__ == '__main__':
    i=1
    while True:
        re = socketReceive()
        if re:
            print('received data:', re)