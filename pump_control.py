import RPi.GPIO as GPIO
import socket
import time
import json
from usage_tracker import UsageTracker
from config import PUMP_VOLTAGE, PUMP_CURRENT

# ========== 硬件配置 ==========
PUMP_RELAY_PIN = 18

# ========== 网络配置 ==========
RASPI_RECEIVE_PORT = 8003

# ========== 初始化 ==========
GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_RELAY_PIN, GPIO.OUT)
GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)

tracker = UsageTracker()
pump_start_time = None

def pump_on():
    global pump_start_time
    GPIO.output(PUMP_RELAY_PIN, GPIO.HIGH)
    pump_start_time = time.time()
    print("[Pump] ON")

def pump_off():
    global pump_start_time
    GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)
    
    if pump_start_time is not None:
        duration = time.time() - pump_start_time
        entry = tracker.record_pump_run(duration, PUMP_VOLTAGE, PUMP_CURRENT)
        print(f"[Pump] OFF - 本次浇水: {duration:.1f}秒, "
              f"用水{entry['water_L']:.3f}L, "
              f"费用{entry['total_cost']:.4f}MOP")
        pump_start_time = None

if __name__ == "__main__":
    print("水泵控制启动...")
    print(f"监听端口: {RASPI_RECEIVE_PORT}")
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("", RASPI_RECEIVE_PORT))
    
    try:
        while True:
            data, addr = s.recvfrom(128)
            command = data.decode('UTF-8').strip()
            
            if command == "PUMP_ON":
                pump_on()
                
            elif command == "PUMP_OFF":
                pump_off()
                
            elif command == "GET_STATS":
                stats = tracker.get_summary()
                response = (f"WATER:{stats['total_water_L']:.3f}|"
                        f"WCOST:{stats['total_cost_water']:.4f}|"
                        f"ENERGY:{stats['total_energy_Wh']:.2f}|"
                        f"ECOST:{stats['total_cost_elec']:.4f}")
                s.sendto(response.encode('UTF-8'), addr)
                print(f"[统计] 发送累计数据")
                
            elif command == "GET_HISTORY":
                history = tracker.get_history()
                if len(history) == 0:
                    response = "暂无浇水记录"
                else:
                    # 最近10条
                    recent = history[-10:]
                    response = "📜 浇水历史（最近10条）\n\n" + "\n".join(recent)
                s.sendto(response.encode('UTF-8'), addr)
                print(f"[统计] 发送历史记录 {len(history)} 条")
                
            elif command == "RESET_STATS":
                tracker.reset_history()
                s.sendto(b"OK", addr)
                print("[统计] 统计数据已清零")
                
    except KeyboardInterrupt:
        pump_off()
        GPIO.cleanup()
        print("\n水泵控制已停止")