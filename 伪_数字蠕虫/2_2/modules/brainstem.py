#!/usr/bin/env python3
"""
脑干模块 (Brainstem) - 复数神经网络适配器
蜉蝣阁 | ling 数字生命框架

v1.2 修复版：
- 强化输入信号
- 大幅降低初始阈值
- 添加本能反射层
"""

import random
from typing import List
from habitat import Observation, Action
from graph_nn import 游戏AI网络


class Brainstem:
    """脑干 - 连接数字蠕虫中枢和复数神经网络"""

    def __init__(self,
                 input_features: int = 9,
                 cache_length: int = 5,
                 network_nodes: int = 20,
                 background_noise: float = 0.05):
        self.action_names = ['STAY', 'NORTH', 'SOUTH', 'WEST', 'EAST', 'EAT']
        self.action_count = len(self.action_names)

        # 初始化复数神经网络
        self.network = 游戏AI网络(
            输入特征数=input_features,
            缓存长度=cache_length,
            命令集=self.action_names,
            网络节点数=network_nodes,
            连接概率=0.3,
            背景噪声=background_noise
        )
        
        # v1.2 修复1: 大幅降低初始阈值
        for i in range(self.network.核心.节点数):
            self.network.核心.阈值[i] = 0.5
        self.network.核心.初始阈值 = 0.5

        self.input_features = input_features
        self.step_count = 0
    
    def extract_features(self, obs: Observation) -> List[float]:
        """从标准化观测中提取特征向量"""
        energy = obs.energy / 200.0
        view = obs.local_view
        food_count = 0
        poison_count = 0
        under_food = 1 if view[1][1] == 1 else 0
        under_poison = 1 if view[1][1] == 2 else 0

        for row in view:
            for cell in row:
                if cell == 1:
                    food_count += 1
                elif cell == 2:
                    poison_count += 1

        food_ratio = food_count / 9
        poison_ratio = poison_count / 9

        food_dir = obs.nearest_food_direction
        if food_dir:
            food_dir_x = food_dir.x / 10.0
            food_dir_y = food_dir.y / 10.0
        else:
            food_dir_x = 0.0
            food_dir_y = 0.0

        poison_dir = obs.nearest_poison_direction
        if poison_dir:
            poison_dir_x = poison_dir.x / 10.0
            poison_dir_y = poison_dir.y / 10.0
        else:
            poison_dir_x = 0.0
            poison_dir_y = 0.0

        features = [
            energy,
            food_ratio,
            poison_ratio,
            under_food,
            under_poison,
            food_dir_x,
            food_dir_y,
            poison_dir_x,
            poison_dir_y
        ]
        return features

    def decide(self, obs: Observation) -> Action:
        """根据观测选择动作"""
        features = self.extract_features(obs)
        self.step_count += 1
        
        # ====== v1.2 修复2: 本能优先层 ======
        # 1. 脚下有食物 → 立即吃
        if obs.local_view[1][1] == 1:
            self.network.推入缓存(features)
            self.network.决定动作()
            return Action.EAT
        
        # 2. 脚下有毒物 → 随机远离
        if obs.local_view[1][1] == 2:
            self.network.推入缓存(features)
            self.network.决定动作()
            return random.choice([Action.NORTH, Action.SOUTH, Action.WEST, Action.EAST])
        
        # 3. 最近食物方向 → 50%概率趋近
        if obs.nearest_food_direction and random.random() < 0.5:
            dx, dy = obs.nearest_food_direction
            if abs(dx) >= abs(dy):
                action = Action.EAST if dx > 0 else Action.WEST
            else:
                action = Action.SOUTH if dy > 0 else Action.NORTH
            self.network.推入缓存(features)
            self.network.决定动作()
            return action
        
        # 4. 最近毒物方向 → 30%概率躲避
        if obs.nearest_poison_direction and random.random() < 0.3:
            dx, dy = obs.nearest_poison_direction
            if abs(dx) >= abs(dy):
                action = Action.WEST if dx > 0 else Action.EAST
            else:
                action = Action.NORTH if dy > 0 else Action.SOUTH
            self.network.推入缓存(features)
            self.network.决定动作()
            return action
        
        # ====== 网络决策层 ======
        # v1.2 修复3: 信号放大
        features_amplified = [f * 5.0 for f in features]
        self.network.推入缓存(features_amplified)
        command_str, activations = self.network.决定动作()

        try:
            action_idx = self.action_names.index(command_str)
            action = Action(action_idx)
        except (ValueError, IndexError):
            action = Action.STAY

        return action

    def give_reward(self, reward: float):
        """向网络传递环境奖励"""
        clamped = max(-50.0, min(50.0, reward))
        normalized = clamped / 50.0
        self.network.给予奖励(normalized, 学习强度=0.1)
    
    def get_network_stats(self) -> dict:
        """获取网络状态统计"""
        return self.network.获取统计()
    
    def get_output_activations(self) -> str:
        """获取输出激活字符串"""
        acts = self.network.上次输出激活
        return "|".join([f"{a[0]:.3f}" for a in acts])
