#!/usr/bin/env python3
"""
日志记录器 - WormLogger
"""
import os
import csv

class WormLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.file = None
        self.writer = None
    
    def open(self, filename: str):
        os.makedirs(self.log_dir, exist_ok=True)
        filepath = os.path.join(self.log_dir, filename)
        self.file = open(filepath, 'w', newline='', encoding='utf-8')
        fieldnames = [
            'tick', 'action', 'action_name', 'reward', 'total_reward', 'energy', 
            'food_eaten', 'pos_x', 'pos_y', 'local_food_count', 'local_poison_count',
            'nearest_food_dx', 'nearest_food_dy', 'nearest_poison_dx', 'nearest_poison_dy',
            'network_active_nodes', 'network_connections', 'network_avg_threshold',
            'last_output_activations'
        ]
        self.writer = csv.DictWriter(self.file, fieldnames=fieldnames)
        self.writer.writeheader()
        self.filepath = filepath
    
    def log(self, tick, action, reward, total_reward, obs, habitat, brainstem):
        food_count = sum(1 for row in obs.local_view for c in row if c == 1)
        poison_count = sum(1 for row in obs.local_view for c in row if c == 2)
        
        fd = obs.nearest_food_direction
        pd = obs.nearest_poison_direction
        
        stats = brainstem.get_network_stats()
        
        self.writer.writerow({
            'tick': tick,
            'action': int(action),
            'action_name': action.name,
            'reward': round(reward, 4),
            'total_reward': round(total_reward, 4),
            'energy': round(habitat.worm.energy, 2),
            'food_eaten': habitat.worm.total_food_eaten,
            'pos_x': obs.position.x,
            'pos_y': obs.position.y,
            'local_food_count': food_count,
            'local_poison_count': poison_count,
            'nearest_food_dx': fd.x if fd else 0,
            'nearest_food_dy': fd.y if fd else 0,
            'nearest_poison_dx': pd.x if pd else 0,
            'nearest_poison_dy': pd.y if pd else 0,
            'network_active_nodes': stats['活跃节点数'],
            'network_connections': stats['连接数'],
            'network_avg_threshold': round(stats['平均阈值'], 4),
            'last_output_activations': brainstem.get_output_activations()
        })
    
    def close(self):
        if self.file:
            self.file.close()
            return self.filepath
        return None
