import PCF8591 as ADC
import RPi.GPIO as GPIO
import socket
import time

# 水位传感器 DO 引脚（根据你的接线，tutorial 7 里是 GPIO 17）
WATER_SENSOR_DO = 17

# 平板的 IP 和接收端口（之前 tutorial 9 里平板监听的是 8888）
TABLET_IP = "10.8.118.18" #Pad's IP
TABLET_PORT = 8888

GPIO.setmode(GPIO.BCM)
GPIO.setup(WATER_SENSOR_DO, GPIO.IN)

def send_to_tablet(message):
    """发送消息给平板"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(message.encode(), (TABLET_IP, TABLET_PORT))
        s.close()
        print(f"已发送: {message}")
    except Exception as e:
        print(f"发送失败: {e}")

def check_water_level():
    """检查水位：1=有水，0=无水"""
    return GPIO.input(WATER_SENSOR_DO)

if __name__ == "__main__":
    print("开始监测水位...")
    try:
        while True:
            water_status = check_water_level()
            
            if water_status == 0:
                message = "WATER:OK"  # 水位正常
            else:
                message = "WATER:LOW"  # 水位低
            
            send_to_tablet(message)
            time.sleep(2)  # 每 2 秒发送一次
            
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\n程序已停止")      
            