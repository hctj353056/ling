#!/usr/bin/env python3
"""
脑干模块 (Brainstem) - 复数神经网络适配器 + DNA机制
蜉蝣阁 | ling 数字生命框架

v2.3 更新：
- 集成指数爆炸修复（信号放大5x + 阈值0.5）
- 支持DNA机制：可加载进化后的网络结构
- 支持精英学习：保存最优网络结构
"""

import random
import os
import json
from typing import List, Optional
from habitat import Observation, Action
from graph_nn import 游戏AI网络, 图神经网络
from dna import DNA编码器, 创建进化网络


class Brainstem:
    """脑干 - 连接数字蠕虫中枢和复数神经网络"""
    
    # DNA进化相关配置
    DNA保存路径 = "dna"
    最优DNA文件 = "最优_dna.json"
    DNA代数计数器 = "dna_generation.txt"
    
    def __init__(self,
                 input_features: int = 9,
                 cache_length: int = 5,
                 network_nodes: int = 20,
                 background_noise: float = 0.05,
                 enable_dna: bool = True):
        self.action_names = ['STAY', 'NORTH', 'SOUTH', 'WEST', 'EAST', 'EAT']
        self.action_count = len(self.action_names)
        
        # 初始化复数神经网络
        self.network = 游戏AI网络(
            输入特征数=input_features,
            缓存长度=cache_length,
            命令集=self.action_names,
            网络节点数=network_nodes,
            连接概率=0.3,
            背景噪声=background_noise,
            启用指数爆炸修复=True  # v2.3 启用
        )
        
        # v2.3: 降低初始阈值
        for i in range(self.network.核心.节点数):
            self.network.核心.阈值[i] = 0.5
        self.network.核心.初始阈值 = 0.5
        
        # DNA机制初始化
        self.enable_dna = enable_dna
        self.best_score = -float('inf')
        self.episode_count = 0
        self.dna_saved = False
        
        if self.enable_dna:
            self._初始化DNA目录()
            self._尝试加载最优DNA()
        
        self.input_features = input_features
        self.step_count = 0
    
    def _初始化DNA目录(self):
        """初始化DNA保存目录"""
        if not os.path.exists(self.DNA保存路径):
            os.makedirs(self.DNA保存路径)
    
    def _获取当前代数(self) -> int:
        """获取当前DNA代数"""
        try:
            with open(self.DNA代数计数器, 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    
    def _保存代数(self, 代数: int):
        """保存当前代数"""
        with open(self.DNA代数计数器, 'w') as f:
            f.write(str(代数))
    
    def _尝试加载最优DNA(self):
        """尝试加载历史最优DNA"""
        最优路径 = os.path.join(self.DNA保存路径, self.最优DNA文件)
        if os.path.exists(最优路径):
            try:
                with open(最优路径, 'r') as f:
                    dna = json.load(f)
                
                邻接, 阈值, _ = DNA编码器.解码(dna)
                self.network.导入结构(邻接, 阈值)
                print(f"  🧬 已加载历史最优DNA (适应度={dna.get('适应度', '?')})")
            except Exception as e:
                print(f"  ⚠️ 加载DNA失败: {e}")
    
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
        
        # ====== 本能优先层 ======
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
        # v2.3: 信号放大5x
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
    
    # ====== DNA机制接口 ======
    
    def 评估个体(self, 食物数: int, 存活步数: int, 能量: float) -> float:
        """
        评估当前个体的适应度
        
        适应度 = 食物数 * 10 + 存活步数 * 0.5 + max(0, 能量) * 0.1
        """
        return 食物数 * 10 + 存活步数 * 0.5 + max(0, 能量) * 0.1
    
    def episode结束(self, 食物数: int, 存活步数: int, 能量: float) -> bool:
        """
        一个回合结束时的处理：
        1. 评估适应度
        2. 如果是历史最优，保存DNA
        3. 重置网络
        
        返回: 是否保存了新的最优DNA
        """
        self.episode_count += 1
        
        if not self.enable_dna:
            return False
        
        适应度 = self.评估个体(食物数, 存活步数, 能量)
        saved_new_best = False
        
        # 检查是否是新最优
        if 适应度 > self.best_score:
            self.best_score = 适应度
            当前代数 = self._获取当前代数()
            
            # 保存DNA
            dna = DNA编码器.编码(self.network.核心)
            dna['适应度'] = 适应度
            dna['代数'] = 当前代数
            dna['食物数'] = 食物数
            dna['存活步数'] = 存活步数
            
            最优路径 = os.path.join(self.DNA保存路径, self.最优DNA文件)
            with open(最优路径, 'w') as f:
                json.dump(dna, f, indent=2)
            
            # 保存带时间戳的版本
            import time
            时间戳版本 = os.path.join(
                self.DNA保存路径, 
                f"dna_gen{当前代数}_{int(time.time())}.json"
            )
            with open(时间戳版本, 'w') as f:
                json.dump(dna, f, indent=2)
            
            saved_new_best = True
            self.dna_saved = True
            
            print(f"\n  🧬 新最优DNA! 适应度={适应度:.2f} (第{当前代数}代)")
        
        # 每5个回合增加代数
        if self.episode_count % 5 == 0:
            当前代数 = self._获取当前代数() + 1
            self._保存代数(当前代数)
        
        # 重置网络（保留结构）
        self.network.重置()
        
        return saved_new_best
    
    def 获取DNA统计(self) -> dict:
        """获取DNA机制统计"""
        return {
            '启用': self.enable_dna,
            '历史最优适应度': self.best_score,
            '回合数': self.episode_count,
            '当前代数': self._获取当前代数(),
            '最新保存': self.dna_saved
        }
    
    def 重置网络结构(self):
        """
        重置为全新随机网络结构
        （用于清除历史DNA的影响）
        """
        当前代数 = self._获取当前代数()
        
        self.network = 游戏AI网络(
            输入特征数=self.input_features,
            缓存长度=5,
            命令集=self.action_names,
            网络节点数=20,
            连接概率=0.3,
            背景噪声=0.05,
            启用指数爆炸修复=True
        )
        
        # v2.3: 降低初始阈值
        for i in range(self.network.核心.节点数):
            self.network.核心.阈值[i] = 0.5
        self.network.核心.初始阈值 = 0.5
        
        # 重置DNA状态
        self.best_score = -float('inf')
        self.episode_count = 0
        self.dna_saved = False
        
        # 增加代数表示新的进化线
        self._保存代数(当前代数 + 100)
        
        print(f"  🔄 网络已重置 (新进化线: 第{当前代数 + 100}代)")


if __name__ == '__main__':
    # 简单测试
    from habitat import Habitat
    
    print("=== Brainstem v2.3 测试 ===\n")
    
    brain = Brainstem(enable_dna=True)
    
    # 创建测试环境
    habitat = Habitat(world_width=20, world_height=10, seed=42)
    
    for episode in range(3):
        print(f"\n--- 回合 {episode + 1} ---")
        
        for tick in range(50):
            if not habitat.worm.alive:
                break
            
            obs = habitat._make_observation()
            action = brain.decide(obs)
            result = habitat.step(action)
            brain.give_reward(result.reward)
            
            if tick % 10 == 0:
                stats = brain.get_network_stats()
                print(f"  步{tick}: {action.name}, 能量={habitat.worm.energy:.1f}, "
                      f"活跃={stats['活跃节点数']}, 连接={stats['连接数']}")
        
        # 回合结束
        brain.episode结束(
            habitat.worm.total_food_eaten,
            habitat.tick_count,
            habitat.worm.energy
        )
        
        # 重置环境
        habitat = Habitat(world_width=20, world_height=10, seed=42 + episode + 1)
    
    # DNA统计
    print("\n" + "=" * 40)
    print("DNA机制统计:")
    for k, v in brain.获取DNA统计().items():
        print(f"  {k}: {v}")
