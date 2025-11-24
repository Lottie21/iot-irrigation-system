 # usage_tracker.py

import json
import time
from datetime import datetime
from config import *

class UsageTracker:
    def __init__(self):
        try:
            with open(DATA_FILE, "r") as f:
                self.data = json.load(f)
        except:
            self.data = {
                "total_water_L": 0,
                "total_energy_Wh": 0,
                "total_cost_water": 0,
                "total_cost_elec": 0,
                "history": []  # 各次浇水的详细记录
            }
            self._save()

    def _save(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def record_pump_run(self, seconds, voltage, current):
        """记录一次浇水"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 水量
        water_used = FLOW_RATE_L_PER_S * seconds
        water_cost = water_used * WATER_PRICE_PER_L
        
        # 电量
        energy_Wh = (voltage * current * seconds) / 3600
        energy_cost = (energy_Wh / 1000) * ELECTRICITY_PRICE_PER_KWH
        
        # 累计
        self.data["total_water_L"] += water_used
        self.data["total_cost_water"] += water_cost
        self.data["total_energy_Wh"] += energy_Wh
        self.data["total_cost_elec"] += energy_cost
        
        # 保存可读文本
        total_cost = water_cost + energy_cost
        text = f"{timestamp} - 本次浇水: {seconds:.1f}秒, 用水{water_used:.3f}L, 费用{total_cost:.4f}MOP"
        self.data["history"].append(text)
        
        self._save()
        return {
            "water_L": water_used,
            "total_cost": total_cost
        }

    def get_summary(self):
        """返回总用量，给App用"""
        return {
            "total_water_L": round(self.data["total_water_L"], 3),
            "total_cost_water": round(self.data["total_cost_water"], 6),
            "total_energy_Wh": round(self.data["total_energy_Wh"], 3),
            "total_cost_elec": round(self.data["total_cost_elec"], 6)
        }

    def get_history(self):
        """返回每次浇水历史记录"""
        return self.data["history"]
    
    def reset_history(self):
        """清空所有统计数据"""
        self.data = {
            "total_water_L": 0,
            "total_energy_Wh": 0,
            "total_cost_water": 0,
            "total_cost_elec": 0,
            "history": []
        }
        self._save()
        print("[统计] 数据已清零")