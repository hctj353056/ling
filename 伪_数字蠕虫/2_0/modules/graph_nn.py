import secrets
import math
import random
from collections import deque

class 图神经网络:
    def __init__(self, 节点数=10, 连接概率=0.25, 初始阈值=2.0, 背景噪声=0.0):
        self.节点数 = 节点数
        self.状态 = [0 + 0j] * 节点数
        self.阈值 = [初始阈值] * 节点数
        self.邻接 = {i: [] for i in range(节点数)}
        self.激活历史 = [0] * 节点数
        self.迭代次数 = 0
        self.背景噪声 = 背景噪声
        self._随机初始化连接(连接概率)
    
    def _随机初始化连接(self, 连接概率):
        for 源 in range(self.节点数):
            for 目标 in range(self.节点数):
                if 源 != 目标 and secrets.randbelow(10000) / 10000 < 连接概率:
                    权重 = complex(
                        secrets.choice(range(-10, 10)) / 10,
                        secrets.choice(range(-10, 10)) / 10,
                    )
                    self.邻接[源].append((目标, 权重))
    
    def 一步传播(self, 外部输入=None):
        新状态 = [0 + 0j] * self.节点数
        活动 = [0] * self.节点数
        for 源 in range(self.节点数):
            模长 = abs(self.状态[源])
            if 模长 > 0.1:
                活动[源] = 1
                for 目标, 权重 in self.邻接[源]:
                    新状态[目标] += self.状态[源] * 权重
        if 外部输入:
            for 节点, 值 in 外部输入.items():
                新状态[节点] += 值
        if self.背景噪声 > 0:
            for i in range(self.节点数):
                实部 = secrets.choice([-1, 1]) * abs(random.gauss(0, self.背景噪声 / math.sqrt(2)))
                虚部 = secrets.choice([-1, 1]) * abs(random.gauss(0, self.背景噪声 / math.sqrt(2)))
                新状态[i] += complex(实部, 虚部)
        self.状态 = 新状态
        self.激活历史 = 活动
        self.迭代次数 += 1
    
    def 激活判定(self):
        新状态 = []
        for i in range(self.节点数):
            if abs(self.状态[i]) > self.阈值[i]:
                新状态.append(self.状态[i])
            else:
                新状态.append(0 + 0j)
        self.状态 = 新状态
    
    def STDP调整(self, 学习率=0.05, 弱化率=0.03, 衰减系数=0.998, 最大模长=5.0):
        for 源 in range(self.节点数):
            新连接列表 = []
            for 目标, 权重 in self.邻接[源]:
                源激活 = self.激活历史[源]
                目标激活 = self.激活历史[目标]
                if 源激活 and 目标激活:
                    权重 = 权重 * (1 + 学习率)
                elif 源激活 and not 目标激活:
                    权重 = 权重 * (1 - 弱化率)
                权重 *= 衰减系数
                模长 = abs(权重)
                if 模长 > 最大模长:
                    权重 = 权重 / 模长 * 最大模长
                if abs(权重) >= 0.05:
                    新连接列表.append((目标, 权重))
            self.邻接[源] = 新连接列表
    
    def 局部调整(self, 修剪阈值=0.2, 生长概率=0.05):
        for 源 in range(self.节点数):
            self.邻接[源] = [(目标, 权重) for 目标, 权重 in self.邻接[源] if abs(权重) >= 修剪阈值]
            if abs(self.状态[源]) > self.阈值[源] * 0.5:
                for 目标 in range(self.节点数):
                    if 源 != 目标 and secrets.randbelow(10000) / 10000 < 生长概率:
                        if not any(t == 目标 for t, _ in self.邻接[源]):
                            新权重 = complex(secrets.choice(range(-5, 5)) / 10, secrets.choice(range(-5, 5)) / 10)
                            self.邻接[源].append((目标, 新权重))
    
    def 全局阈值调整(self, 目标活跃比例=0.3, 调整率=0.02):
        活跃数 = sum(1 for i, s in enumerate(self.状态) if abs(s) > self.阈值[i])
        活跃比例 = 活跃数 / self.节点数
        偏离 = 活跃比例 - 目标活跃比例
        修正量 = 偏离 * 调整率
        for i in range(self.节点数):
            self.阈值[i] = max(0.5, min(5.0, self.阈值[i] + 修正量))
    
    def 运行一步(self, 外部输入=None):
        self.一步传播(外部输入)
        self.激活判定()
        self.STDP调整()
        self.局部调整()
        self.全局阈值调整()
        return self.状态
    
    def 获取输出(self):
        输出 = []
        for i, s in enumerate(self.状态):
            if abs(s) > self.阈值[i]:
                输出.append((i, s))
        return 输出
    
    def 获取活跃节点数(self):
        return sum(1 for s in self.状态 if abs(s) > 0.1)
    
    def 获取连接数(self):
        return sum(len(v) for v in self.邻接.values())
    
    def 获取平均阈值(self):
        return sum(self.阈值) / len(self.阈值) if self.阈值 else 0

class 游戏AI网络:
    def __init__(self, 输入特征数=4, 缓存长度=5, 命令集=None, 网络节点数=12, 连接概率=0.3, 背景噪声=0.02):
        self.输入特征数 = 输入特征数
        self.输入缓存 = deque(maxlen=缓存长度)
        if 命令集 is None:
            self.命令集 = ['+', '-', '<', '>', '.', ',', '[', ']']
        else:
            self.命令集 = list(命令集)
        self.输出节点数 = len(self.命令集)
        assert 网络节点数 >= self.输出节点数 + self.输入特征数, "节点数过小！"
        self.核心 = 图神经网络(节点数=网络节点数, 连接概率=连接概率, 初始阈值=2.0, 背景噪声=背景噪声)
        self.输入节点索引 = list(range(self.输入特征数))
        self.输出节点索引 = list(range(self.输入特征数, self.输入特征数 + self.输出节点数))
        self.输出序列 = []
        self.上次输出激活 = [(0.0, 0.0)] * self.输出节点数
    
    def 编码环境(self, 原始状态):
        if len(原始状态) != self.输入特征数:
            raise ValueError("原始状态长度必须等于输入特征数")
        编码 = {}
        for i, val in enumerate(原始状态):
            编码[self.输入节点索引[i]] = complex(val, val * 0.5)
        return 编码
    
    def 推入缓存(self, 原始状态):
        编码 = self.编码环境(原始状态)
        self.输入缓存.append(编码)
    
    def 决定动作(self):
        # 取最新一帧（修复：取最新而不是最旧）
        外部输入 = self.输入缓存[-1] if len(self.输入缓存) > 0 else {}
        self.核心.运行一步(外部输入)
        输出激活 = []
        for idx in self.输出节点索引:
            模长 = abs(self.核心.状态[idx])
            相位 = math.atan2(self.核心.状态[idx].imag, self.核心.状态[idx].real)
            输出激活.append((模长, 相位))
        
        self.上次输出激活 = 输出激活
        
        # 选择最大模长的节点（修复：全0时随机）
        max_val = max(a[0] for a in 输出激活)
        if max_val < 0.01:  # 全都太弱，随机选择
            output_idx = random.randint(0, len(输出激活) - 1)
        else:
            output_idx = max(range(len(输出激活)), key=lambda i: 输出激活[i][0])
        
        命令 = self.命令集[output_idx]
        self.输出序列.append(命令)
        return 命令, 输出激活
    
    def 打印打字机(self):
        print("打字机输出: ", " ".join(self.输出序列))
    
    def 给予奖励(self, 奖励值, 学习强度=0.1):
        for idx in self.输出节点索引:
            self.核心.阈值[idx] += -奖励值 * 学习强度
            self.核心.阈值[idx] = max(0.5, min(5.0, self.核心.阈值[idx]))
    
    def 获取统计(self):
        return {
            '活跃节点数': self.核心.获取活跃节点数(),
            '连接数': self.核心.获取连接数(),
            '平均阈值': self.核心.获取平均阈值()
        }
