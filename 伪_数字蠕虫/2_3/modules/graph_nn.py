#!/usr/bin/env python3
"""
图神经网络模块 v2.3 - 复数神经网络 + 指数爆炸修复
蜉蝣阁 | ling 数字生命框架

v2.3 修复：
- tanh压缩：状态保持在[-1,1]范围，防止数值溢出
- 谱半径控制：权重归一化避免信号放大
- 权能量衰减：定期收缩总能量防止累积爆炸
"""

import secrets
import math
import random
from collections import deque


class 图神经网络:
    """复数神经网络，支持动态拓扑演化"""
    
    def __init__(self, 
                 节点数=10, 
                 连接概率=0.25, 
                 初始阈值=2.0, 
                 背景噪声=0.0,
                 启用指数爆炸修复=True):
        self.节点数 = 节点数
        self.状态 = [0 + 0j] * 节点数
        self.阈值 = [初始阈值] * 节点数
        self.初始阈值 = 初始阈值
        self.邻接 = {i: [] for i in range(节点数)}
        self.激活历史 = [0] * 节点数
        self.迭代次数 = 0
        self.背景噪声 = 背景噪声
        self.启用指数爆炸修复 = 启用指数爆炸修复
        
        # v2.3 新增：指数爆炸控制
        self.衰减计数器 = 0
        self.衰减周期 = 10  # 每10步衰减一次
        self.目标能量 = 1.0
        
        self._随机初始化连接(连接概率)
        
        # v2.3：初始化时执行谱半径控制
        if self.启用指数爆炸修复:
            self._谱半径控制()
    
    def _随机初始化连接(self, 连接概率):
        """随机初始化网络连接"""
        for 源 in range(self.节点数):
            for 目标 in range(self.节点数):
                if 源 != 目标 and secrets.randbelow(10000) / 10000 < 连接概率:
                    权重 = complex(
                        secrets.choice(range(-10, 10)) / 10,
                        secrets.choice(range(-10, 10)) / 10,
                    )
                    self.邻接[源].append((目标, 权重))
    
    def _谱半径控制(self):
        """
        v2.3 新增：谱半径控制
        将每条边的权重除以sqrt(出度+1)
        使网络的谱半径（最大特征值）接近1
        """
        for 源 in range(self.节点数):
            出度 = len(self.邻接[源])
            if 出度 == 0:
                continue
            
            归一化因子 = math.sqrt(出度 + 1)
            新连接列表 = []
            
            for 目标, 权重 in self.邻接[源]:
                归一化权重 = 权重 / 归一化因子
                新连接列表.append((目标, 归一化权重))
            
            self.邻接[源] = 新连接列表
    
    def _状态压缩(self):
        """
        v2.3 新增：tanh压缩
        将状态压缩到[-1,1]范围，保持复数方向信息
        """
        for i in range(self.节点数):
            if abs(self.状态[i]) > 0.001:  # 避免数值不稳定
                实部压缩 = math.tanh(self.状态[i].real)
                虚部压缩 = math.tanh(self.状态[i].imag)
                self.状态[i] = complex(实部压缩, 虚部压缩)
    
    def _权能量衰减(self):
        """
        v2.3 新增：权能量衰减
        当总连接能量超过目标能量时，等比例缩放所有权重
        """
        总能量 = sum(abs(权重)**2 for 连接列表 in self.邻接.values() 
                     for _, 权重 in 连接列表)
        
        if 总能量 > self.目标能量 * 1.5:  # 超过阈值才衰减
            缩放因子 = math.sqrt(self.目标能量 / 总能量)
            
            for 源 in self.邻接:
                self.邻接[源] = [
                    (目标, 权重 * 缩放因子)
                    for 目标, 权重 in self.邻接[源]
                ]
    
    def 一步传播(self, 外部输入=None):
        """神经网络前向传播一步"""
        新状态 = [0 + 0j] * self.节点数
        活动 = [0] * self.节点数
        
        for 源 in range(self.节点数):
            模长 = abs(self.状态[源])
            if 模长 > 0.1:
                活动[源] = 1
                for 目标, 权重 in self.邻接[源]:
                    新状态[目标] += self.状态[源] * 权重
        
        # 添加外部输入
        if 外部输入:
            for 节点, 值 in 外部输入.items():
                新状态[节点] += 值
        
        # 添加背景噪声
        if self.背景噪声 > 0:
            for i in range(self.节点数):
                实部 = secrets.choice([-1, 1]) * abs(random.gauss(0, self.背景噪声 / math.sqrt(2)))
                虚部 = secrets.choice([-1, 1]) * abs(random.gauss(0, self.背景噪声 / math.sqrt(2)))
                新状态[i] += complex(实部, 虚部)
        
        self.状态 = 新状态
        self.激活历史 = 活动
        self.迭代次数 += 1
        
        # v2.3：传播后压缩状态
        if self.启用指数爆炸修复:
            self._状态压缩()
        
        # v2.3：定期衰减权能量
        self.衰减计数器 += 1
        if self.衰减计数器 >= self.衰减周期:
            self.衰减计数器 = 0
            if self.启用指数爆炸修复:
                self._权能量衰减()
    
    def 激活判定(self):
        """根据阈值判断哪些神经元被激活"""
        for i in range(self.节点数):
            if abs(self.状态[i]) > self.阈值[i]:
                pass  # 保持激活状态
            else:
                self.状态[i] = 0 + 0j
    
    def STDP调整(self, 学习率=0.05, 弱化率=0.03, 衰减系数=0.998, 最大模长=2.0):
        """
        突触可塑性调整（STDP）
        - 共同激活的连接增强
        - 单方面激活的连接减弱
        """
        for 源 in range(self.节点数):
            新连接列表 = []
            for 目标, 权重 in self.邻接[源]:
                源激活 = self.激活历史[源]
                目标激活 = self.激活历史[目标]
                
                if 源激活 and 目标激活:
                    # 双向激活：强化
                    权重 = 权重 * (1 + 学习率)
                elif 源激活 and not 目标激活:
                    # 单向激活：弱化
                    权重 = 权重 * (1 - 弱化率)
                
                # 权重衰减
                权重 *= 衰减系数
                
                # v2.3：降低最大模长限制
                模长 = abs(权重)
                if 模长 > 最大模长:
                    权重 = 权重 / 模长 * 最大模长
                
                # 删除过弱的连接
                if abs(权重) >= 0.05:
                    新连接列表.append((目标, 权重))
            
            self.邻接[源] = 新连接列表
    
    def 局部调整(self, 修剪阈值=0.2, 生长概率=0.05):
        """
        局部结构调整：
        - 修剪弱连接
        - 在活跃节点处生长新连接
        """
        for 源 in range(self.节点数):
            # 修剪弱连接
            self.邻接[源] = [(目标, 权重) for 目标, 权重 in self.邻接[源] 
                            if abs(权重) >= 修剪阈值]
            
            # 生长新连接
            if abs(self.状态[源]) > self.阈值[源] * 0.5:
                for 目标 in range(self.节点数):
                    if 源 != 目标 and secrets.randbelow(10000) / 10000 < 生长概率:
                        if not any(t == 目标 for t, _ in self.邻接[源]):
                            新权重 = complex(
                                secrets.choice(range(-5, 5)) / 10,
                                secrets.choice(range(-5, 5)) / 10
                            )
                            # v2.3：新连接也做谱半径控制
                            if self.启用指数爆炸修复:
                                出度 = len(self.邻接[源]) + 1
                                新权重 = 新权重 / math.sqrt(出度)
                            self.邻接[源].append((目标, 新权重))
    
    def 全局阈值调整(self, 目标活跃比例=0.3, 调整率=0.02):
        """
        全局阈值调整：
        使活跃节点比例维持在目标值附近
        """
        活跃数 = sum(1 for i, s in enumerate(self.状态) if abs(s) > self.阈值[i])
        活跃比例 = 活跃数 / self.节点数
        偏离 = 活跃比例 - 目标活跃比例
        修正量 = 偏离 * 调整率
        
        for i in range(self.节点数):
            self.阈值[i] = max(0.5, min(5.0, self.阈值[i] + 修正量))
    
    def 运行一步(self, 外部输入=None):
        """执行神经网络的一步计算"""
        self.一步传播(外部输入)
        self.激活判定()
        self.STDP调整()
        self.局部调整()
        self.全局阈值调整()
        return self.状态
    
    def 获取输出(self):
        """获取当前激活的输出"""
        输出 = []
        for i, s in enumerate(self.状态):
            if abs(s) > self.阈值[i]:
                输出.append((i, s))
        return 输出
    
    def 获取活跃节点数(self):
        """获取当前活跃的节点数"""
        return sum(1 for s in self.状态 if abs(s) > 0.1)
    
    def 获取连接数(self):
        """获取当前连接总数"""
        return sum(len(v) for v in self.邻接.values())
    
    def 获取平均阈值(self):
        """获取平均阈值"""
        return sum(self.阈值) / len(self.阈值) if self.阈值 else 0
    
    def 获取统计(self):
        """获取网络状态统计"""
        # v2.3：增加更多统计信息
        总能量 = sum(abs(权重)**2 for 连接列表 in self.邻接.values() 
                     for _, 权重 in 连接列表)
        最大状态值 = max(abs(s) for s in self.状态) if self.状态 else 0
        平均状态值 = sum(abs(s) for s in self.状态) / len(self.状态) if self.状态 else 0
        
        return {
            '活跃节点数': self.获取活跃节点数(),
            '连接数': self.获取连接数(),
            '平均阈值': self.获取平均阈值(),
            '总能量': 总能量,
            '最大状态值': 最大状态值,
            '平均状态值': 平均状态值,
            '迭代次数': self.迭代次数
        }


class 游戏AI网络:
    """
    游戏AI专用复数神经网络
    包含输入编码、输出解码、奖励学习等接口
    """
    
    def __init__(self, 
                 输入特征数=4, 
                 缓存长度=5, 
                 命令集=None, 
                 网络节点数=12, 
                 连接概率=0.3, 
                 背景噪声=0.02,
                 启用指数爆炸修复=True):
        self.输入特征数 = 输入特征数
        self.输入缓存 = deque(maxlen=缓存长度)
        
        if 命令集 is None:
            self.命令集 = ['+', '-', '<', '>', '.', ',', '[', ']']
        else:
            self.命令集 = list(命令集)
        
        self.输出节点数 = len(self.命令集)
        assert 网络节点数 >= self.输出节点数 + self.输入特征数, "节点数过小！"
        
        # v2.3：传递指数爆炸修复开关
        self.核心 = 图神经网络(
            节点数=网络节点数, 
            连接概率=连接概率, 
            初始阈值=2.0, 
            背景噪声=背景噪声,
            启用指数爆炸修复=启用指数爆炸修复
        )
        
        self.输入节点索引 = list(range(self.输入特征数))
        self.输出节点索引 = list(range(self.输入特征数, self.输入特征数 + self.输出节点数))
        self.输出序列 = []
        self.上次输出激活 = [(0.0, 0.0)] * self.输出节点数
    
    def 编码环境(self, 原始状态):
        """将环境特征编码为复数输入"""
        if len(原始状态) != self.输入特征数:
            raise ValueError("原始状态长度必须等于输入特征数")
        
        编码 = {}
        for i, val in enumerate(原始状态):
            编码[self.输入节点索引[i]] = complex(val, val * 0.5)
        return 编码
    
    def 推入缓存(self, 原始状态):
        """将环境状态推入输入缓存"""
        编码 = self.编码环境(原始状态)
        self.输入缓存.append(编码)
    
    def 决定动作(self):
        """基于当前网络状态决定动作"""
        # 取最新一帧输入
        外部输入 = self.输入缓存[-1] if len(self.输入缓存) > 0 else {}
        self.核心.运行一步(外部输入)
        
        # 读取输出层激活
        输出激活 = []
        for idx in self.输出节点索引:
            if idx < len(self.核心.状态):
                s = self.核心.状态[idx]
                输出激活.append((abs(s), s))
            else:
                输出激活.append((0.0, 0 + 0j))
        
        self.上次输出激活 = [(a[0], a[1].real) for a in 输出激活]
        
        # 竞争选出最强输出
        max_activation = 0
        max_idx = 0
        for i, (activation, _) in enumerate(输出激活):
            if activation > max_activation:
                max_activation = activation
                max_idx = i
        
        命令 = self.命令集[max_idx]
        self.输出序列.append(命令)
        
        return 命令, 输出激活
    
    def 给予奖励(self, 奖励值, 学习强度=0.1):
        """
        根据奖励调整网络连接
        正奖励强化最近输出，负奖励抑制
        """
        if not self.输出序列:
            return
        
        最近输出 = self.输出序列[-1]
        if 最近输出 in self.命令集:
            输出索引 = self.命令集.index(最近输出)
            对应节点 = self.输出节点索引[输出索引]
            
            # 调整输入到输出的连接权重
            调整量 = 学习强度 * 奖励值
            
            for 源 in self.核心.邻接:
                新连接 = []
                for 目标, 权重 in self.核心.邻接[源]:
                    if 目标 == 对应节点:
                        # 强化/弱化这条连接
                        权重 = 权重 * (1 + 调整量)
                    新连接.append((目标, 权重))
                self.核心.邻接[源] = 新连接
    
    def 获取统计(self):
        """获取网络统计信息"""
        return self.核心.获取统计()
    
    def 重置(self):
        """重置网络状态（保留连接结构）"""
        self.核心.状态 = [0 + 0j] * self.核心.节点数
        self.核心.激活历史 = [0] * self.核心.节点数
        self.输入缓存.clear()
        self.输出序列 = []
    
    def 导入结构(self, 邻接, 阈值):
        """
        v2.3 新增：导入外部网络结构
        用于DNA机制：加载进化后的网络结构
        """
        if 邻接:
            self.核心.邻接 = 邻接
        if 阈值:
            self.核心.阈值 = 阈值
            self.核心.初始阈值 = sum(阈值) / len(阈值) if 阈值 else 2.0


if __name__ == '__main__':
    # 简单测试
    print("=== 图神经网络 v2.3 测试 ===\n")
    
    # 测试基本功能
    net = 图神经网络(节点数=10, 连接概率=0.3, 启用指数爆炸修复=True)
    print(f"初始化：连接数={net.获取连接数()}, 平均阈值={net.获取平均阈值():.2f}")
    
    # 测试传播
    输入 = {0: 1+0j, 1: 0.5+0.25j}
    for i in range(20):
        net.运行一步(输入)
        stats = net.获取统计()
        if i % 5 == 0:
            print(f"步{i}: 活跃={stats['活跃节点数']}, 连接={stats['连接数']}, "
                  f"最大状态={stats['最大状态值']:.4f}, 总能量={stats['总能量']:.4f}")
    
    # 测试游戏AI网络
    print("\n--- 游戏AI网络测试 ---")
    game_net = 游戏AI网络(
        输入特征数=4, 
        命令集=['STAY', 'NORTH', 'SOUTH', 'EAST', 'WEST'],
        网络节点数=12,
        启用指数爆炸修复=True
    )
    
    for i in range(10):
        state = [0.5, 0.3, 0.1, 0.2]
        game_net.推入缓存(state)
        cmd, acts = game_net.决定动作()
        print(f"决策{i}: {cmd}, 激活={max(a[0] for a in acts):.4f}")
