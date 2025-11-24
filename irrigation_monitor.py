import PCF8591 as ADC
import RPi.GPIO as GPIO
import socket
import time

# ========== 硬件配置 ==========
WATER_SENSOR_DO = 17  # 水位传感器 DO 引脚
PCF8591_ADDRESS = 0x48  # PCF8591 地址
SOIL_MOISTURE_CHANNEL = 0  # 土壤湿度传感器连到 PCF8591 的 AIN0
TEMPERATURE_CHANNEL = 1  # 温度传感器连到 PCF8591 的 AIN1

# ========== 网络配置 ==========
TABLET_IP = "172.20.10.3"  # ← 改成你平板的 IP
TABLET_PORT = 8888

# ========== 自动浇水配置 ==========
AUTO_WATERING = True  # 是否启用自动浇水
TEMP_THRESHOLD = 20   # 温度阈值（摄氏度）
MOISTURE_THRESHOLD = 30  # 湿度阈值（百分比）
WATERING_DURATION = 2  # 浇水持续时间（秒）

# ========== GPIO 初始化 ==========
GPIO.setmode(GPIO.BCM)
GPIO.setup(WATER_SENSOR_DO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
ADC.setup(PCF8591_ADDRESS)

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

def read_soil_moisture():
    """读取土壤湿度：0-255（0=很湿，255=很干）"""
    value = ADC.read(SOIL_MOISTURE_CHANNEL)
    return value

def moisture_to_percentage(value):
    """将 0-255 转换为湿度百分比（0%=很干，100%=很湿）"""
    # 反转：传感器返回值越大=越干，我们要显示越小
    percentage = 100 - int((value / 255) * 100)
    return percentage

def read_temperature():
    """读取温度：0-255 的模拟值"""
    value = ADC.read(TEMPERATURE_CHANNEL)
    return value

def convert_temperature(value):
    """将模拟值转换为摄氏度
    具体转换公式取决于你的传感器型号
    这里假设：0-255 对应 0-50°C（需要实际测试校准）
    """
    temperature = (value / 255.0) * 50
    return round(temperature, 1)

def send_pump_command(command):
    """发送指令给pump_control"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(command.encode(), ("127.0.0.1", 8003))
        s.close()
        print(f"[自动浇水] 发送指令: {command}")
    except Exception as e:
        print(f"[自动浇水] 发送失败: {e}")

def auto_watering_check(temperature, soil_percentage, water_status):
    """检查是否需要自动浇水"""
    if not AUTO_WATERING:
        return False
    
    if water_status == 0:  # 水位正常
        if temperature > TEMP_THRESHOLD and soil_percentage < MOISTURE_THRESHOLD:
            print(f"[自动浇水] 触发条件: 温度{temperature}°C > {TEMP_THRESHOLD}°C, 湿度{soil_percentage}% < {MOISTURE_THRESHOLD}%")
            send_pump_command("PUMP_ON")
            time.sleep(WATERING_DURATION)
            send_pump_command("PUMP_OFF")
            return True
    else:
        print("[自动浇水] 水位不足，取消自动浇水")
    return False

if __name__ == "__main__":
    print("智慧灌溉监测系统启动...")
    print(f"发送目标: {TABLET_IP}:{TABLET_PORT}")
    
    try:
        while True:
            # 1. 读取水位
            water_status = check_water_level()
            water_msg = "OK" if water_status == 0 else "LOW"
            
            # 2. 读取土壤湿度
            soil_value = read_soil_moisture()
            soil_percentage = moisture_to_percentage(soil_value)

            # 3. 读取温度
            temp_value = read_temperature()
            temperature = convert_temperature(temp_value)

            # 4. 打包数据（格式：WATER:状态|SOIL:百分比|TEMP:温度）
            message = f"WATER:{water_msg}|SOIL:{soil_percentage}|TEMP:{temperature}"
            
            # 5. 发送到平板
            send_to_tablet(message)

            # auto pump check
            auto_watering_check(temperature, soil_percentage, water_status)

            # 6. 终端显示（方便调试）
            print(f"  水位: {water_msg}, 土壤湿度: {soil_percentage}%, 温度: {temperature}°C")
            
            time.sleep(1)  # 每 2 秒更新一次
            
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\n程序已停止")