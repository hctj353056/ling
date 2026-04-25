#!/usr/bin/env python3
"""
数字蠕虫日志模块 - WormLogger v1.0
"""

import csv
import os
import sys
from typing import Dict, Any, Optional

# ========== 动态获取脚本所在目录 ==========
def get_script_dir() -> str:
    """获取当前脚本所在的绝对目录（兼容Termux/任何环境）"""
    # 方式1：从 __file__ 获取（最可靠）
    if '__file__' in globals():
        return os.path.dirname(os.path.abspath(__file__))
    # 方式2：从 sys.argv[0] 获取
    if sys.argv and sys.argv[0]:
        script_path = sys.argv[0]
        if os.path.isfile(script_path):
            return os.path.dirname(os.path.abspath(script_path))
    # 方式3：回退到当前工作目录
    return os.getcwd()


class WormLogger:
    def __init__(self, log_dir: str = None):
        # 默认日志目录 = 脚本所在目录/logs
        if log_dir is None:
            log_dir = os.path.join(get_script_dir(), "logs")
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.csv_file = None
        self.csv_writer = None
        self.fields = [
            'tick', 'action', 'action_name', 'reward', 'total_reward',
            'energy', 'food_eaten', 'pos_x', 'pos_y',
            'local_food_count', 'local_poison_count',
            'nearest_food_dx', 'nearest_food_dy',
            'nearest_poison_dx', 'nearest_poison_dy',
            'network_active_nodes', 'network_connections',
            'network_avg_threshold', 'last_output_activations'
        ]
    
    def open(self, filename: str = "worm_log.csv"):
        filepath = os.path.join(self.log_dir, filename)
        self.csv_file = open(filepath, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fields)
        self.csv_writer.writeheader()
        print(f"📊 日志已开启: {filepath}")
    
    def log(self, tick: int, action, reward: float, total_reward: float,
            obs, habitat, brainstem=None):
        """记录一行数据"""
        row = {
            'tick': tick,
            'action': int(action),
            'action_name': action.name,
            'reward': reward,
            'total_reward': total_reward,
            'energy': obs.energy,
            'food_eaten': habitat.worm.total_food_eaten,
            'pos_x': obs.position.x,
            'pos_y': obs.position.y,
        }
        
        # 局部视野统计
        view = obs.local_view
        food_count = sum(1 for row in view for cell in row if cell == 1)
        poison_count = sum(1 for row in view for cell in row if cell == 2)
        row['local_food_count'] = food_count
        row['local_poison_count'] = poison_count
        
        # 最近目标方向
        if obs.nearest_food_direction:
            row['nearest_food_dx'] = obs.nearest_food_direction.x
            row['nearest_food_dy'] = obs.nearest_food_direction.y
        else:
            row['nearest_food_dx'] = ''
            row['nearest_food_dy'] = ''
            
        if obs.nearest_poison_direction:
            row['nearest_poison_dx'] = obs.nearest_poison_direction.x
            row['nearest_poison_dy'] = obs.nearest_poison_direction.y
        else:
            row['nearest_poison_dx'] = ''
            row['nearest_poison_dy'] = ''
        
        # 网络内部状态 (如果能访问到)
        if brainstem and brainstem.network:
            net = brainstem.network
            core = net.核心
            # 活跃节点数
            active = sum(1 for s in core.状态 if abs(s) > 0.1)
            row['network_active_nodes'] = active
            # 连接总数
            conn_count = sum(len(v) for v in core.邻接.values())
            row['network_connections'] = conn_count
            # 平均阈值
            avg_thresh = sum(core.阈值) / len(core.阈值)
            row['network_avg_threshold'] = avg_thresh
            # 最后一次输出激活强度 (6个动作)
            # 需要在brainstem里缓存，这里简单处理
            row['last_output_activations'] = ''
        
        self.csv_writer.writerow(row)
    
    def close(self):
        if self.csv_file:
            self.csv_file.close()