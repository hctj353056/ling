#!/usr/bin/env python3
"""
脑干模块 (Brainstem) - 复数神经网络适配器
蜉蝣阁 | ling 数字生命框架

连接中枢 Habitat 与 复数图神经网络 (图神经网络v2.2)
功能:
- 观测编码: Observation → 特征向量 → 复数输入
- 动作决策: 复数网络前向传播 → Action
- 奖励学习: 环境奖励 → 网络联想调整
"""

import sys
from typing import List
from habitat import Observation, Action
# 导入现有的复数网络
from 图神经网络v2_2 import 游戏AI网络   # 请确保文件名匹配


class Brainstem:
    """脑干 - 连接数字蠕虫中枢和复数神经网络"""

    def __init__(self,
                 input_features: int = 8,
                 cache_length: int = 5,
                 network_nodes: int = 20,
                 background_noise: float = 0.02):
        """
        初始化脑干

        Args:
            input_features: 从观测中提取的特征数
            cache_length: 输入缓存长度 (时序记忆)
            network_nodes: 复数网络节点总数
            background_noise: 背景噪声强度
        """
        # Action 名字列表，与中枢的 Action 枚举顺序一致
        self.action_names = [
            'STAY', 'NORTH', 'SOUTH', 'WEST', 'EAST', 'EAT'
        ]
        self.action_count = len(self.action_names)

        # 初始化复数神经网络
        self.network = 游戏AI网络(
            输入特征数=input_features,
            缓存长度=cache_length,
            命令集=self.action_names,   # 用 Action 名字代替 BF 字符
            网络节点数=network_nodes,
            连接概率=0.3,
            背景噪声=background_noise
        )

        # 特征提取元信息
        self.input_features = input_features

    # ==================== 观测 → 特征向量 ====================
    def extract_features(self, obs: Observation) -> List[float]:
        """
        从标准化观测中提取固定长度的特征向量

        特征说明 (8 维)：
        0: 归一化能量 (0~1)
        1: 局部视野中食物数量 / 视野格数 (归一化)
        2: 局部视野中毒物数量 / 视野格数
        3: 脚下是否有食物 (0/1)
        4: 脚下是否有毒物 (0/1)
        5: 最近食物的方向 x 分量 (归一化到 [-1,1])
        6: 最近食物的方向 y 分量 (归一化到 [-1,1])
        7: 最近毒物的方向 x 分量 (归一化到 [-1,1])   # 若没有毒物则为0
        8: 最近毒物的方向 y 分量 (归一化到 [-1,1])   # 若没有毒物则为0
        (总共 9 个特征，可根据脑的需要调整)
        """
        # 能量
        energy = obs.energy / 200.0  # 假设最大能量 200

        # 局部视野分析 (3x3 网格，中心是自己)
        view = obs.local_view  # 3×3 整数矩阵
        food_count = 0
        poison_count = 0
        under_food = 1 if view[1][1] == 1 else 0  # 中心点：CellType.FOOD=1
        under_poison = 1 if view[1][1] == 2 else 0

        for row in view:
            for cell in row:
                if cell == 1:   # FOOD
                    food_count += 1
                elif cell == 2: # POISON
                    poison_count += 1

        view_size = 9  # 3x3
        food_ratio = food_count / view_size
        poison_ratio = poison_count / view_size

        # 食物方向 (相对坐标，视野外则没有)
        food_dir = obs.nearest_food_direction
        if food_dir:
            food_dir_x = food_dir.x / 10.0   # 假设最大距离 10
            food_dir_y = food_dir.y / 10.0
        else:
            food_dir_x = 0.0
            food_dir_y = 0.0

        # 毒物方向
        poison_dir = obs.nearest_poison_direction
        if poison_dir:
            poison_dir_x = poison_dir.x / 10.0
            poison_dir_y = poison_dir.y / 10.0
        else:
            poison_dir_x = 0.0
            poison_dir_y = 0.0

        # 组合特征向量 (可根据需要调整数量)
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
        # 如果特征数不匹配，裁剪或填充
        if len(features) != self.input_features:
            # 简单截断或补零
            features = features[:self.input_features]
            while len(features) < self.input_features:
                features.append(0.0)
        return features

    # ==================== 观测 → 动作 ====================
    def decide(self, obs: Observation) -> Action:
        """
        根据观测选择动作

        Args:
            obs: 标准化观测

        Returns:
            Action: 中枢可执行的动作
        """
        # 1. 提取特征向量
        features = self.extract_features(obs)

        # 2. 将特征推入网络缓存 (保留历史)
        self.network.推入缓存(features)

        # 3. 网络前向运行一步，得到 BF 命令字符串
        command_str, activations = self.network.决定动作()

        # 4. 将命令字符串映射回 Action
        try:
            action_idx = self.action_names.index(command_str)
            action = Action(action_idx)
        except (ValueError, IndexError):
            # 容错：如果映射失败，选择 STAY
            action = Action.STAY

        return action

    # ==================== 奖励 → 学习 ====================
    def give_reward(self, reward: float):
        """
        向网络传递环境奖励，触发内部学习

        Args:
            reward: 每步获得的奖励值 (通常为能量变化)
        """
        # 归一化奖励到 [-1, 1] 区间再传入网络
        # 根据能量变化范围动态调整 (此处保守归一化)
        clamped = max(-50.0, min(50.0, reward))
        normalized = clamped / 50.0   # 映射到 [-1, 1]
        self.network.给予奖励(normalized, 学习强度=0.1)

    # ==================== 网络状态保存/加载 (预留) ====================
    def save_state(self, filename: str):
        """保存网络状态 (未实现，可扩展)"""
        pass

    def load_state(self, filename: str):
        """加载网络状态 (未实现，可扩展)"""
        pass


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 简单测试：创建脑干，喂观测，看输出
    from habitat import Habitat, Observation, Action, Position

    # 创建中枢
    habitat = Habitat(world_width=10, world_height=5, seed=42)

    # 创建脑干 (特征数 = 7，匹配上面提取的特征数)
    brain = Brainstem(input_features=9, cache_length=3, network_nodes=16)

    # 获取初始观测
    obs = habitat._make_observation()
    print("初始观测:", obs)

    # 提取特征
    feats = brain.extract_features(obs)
    print("特征向量:", feats)

    # 决策动作
    action = brain.decide(obs)
    print("决策动作:", action)

    # 模拟一步中枢执行
    result = habitat.step(action)
    print("中枢执行结果:", result.info)

    # 将奖励传回脑干
    brain.give_reward(result.reward)
    print("奖励已传回网络")