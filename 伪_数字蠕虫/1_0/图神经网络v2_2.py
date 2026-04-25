# 图节点复数神经元网络 v2.2 —— 游戏AI原型
# 2026.4.24
# 新增：输入缓存 + bf打字机输出 + 奖励机制
# 编码：utf-8

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
            self.邻接[源] = [
                (目标, 权重) for 目标, 权重 in self.邻接[源]
                if abs(权重) >= 修剪阈值
            ]
            
            if abs(self.状态[源]) > self.阈值[源] * 0.5:
                for 目标 in range(self.节点数):
                    if 源 != 目标 and secrets.randbelow(10000) / 10000 < 生长概率:
                        if not any(t == 目标 for t, _ in self.邻接[源]):
                            新权重 = complex(
                                secrets.choice(range(-5, 5)) / 10,
                                secrets.choice(range(-5, 5)) / 10,
                            )
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
    
    def 打印状态(self, 步数=None):
        标签 = f"第{步数}步" if 步数 else "状态"
        活跃 = sum(1 for s in self.状态 if abs(s) > 0.1)
        连接数 = sum(len(v) for v in self.邻接.values())
        print(f"{标签}: 活跃={活跃}, 连接={连接数}")
        for i, s in enumerate(self.状态):
            模长 = abs(s)
            if 模长 > 0.1:
                相位 = math.degrees(math.atan2(s.imag, s.real))
                print(f" 节点{i}: |{模长:.2f}| ∠{相位:.1f}°")


# ============ 游戏AI包装器 ============
class 游戏AI网络:
    def __init__(self, 输入特征数=4, 缓存长度=5, 命令集=None, 网络节点数=12, 连接概率=0.3, 背景噪声=0.02):
        """
        输入特征数: 环境状态编码成几个复数（每个复数实部、虚部各一个特征）
        缓存长度: 保留最近多少帧的输入（每一步先压入新特征，然后取最早一帧喂给网络）
        命令集: 可用的 bf 命令字符列表，默认全部 8 个
        """
        self.输入特征数 = 输入特征数
        
        # 输入缓存：deque中每个元素是一个字典 {节点索引: 复数值}
        self.输入缓存 = deque(maxlen=缓存长度)
        
        # 输出命令定义
        if 命令集 is None:
            self.命令集 = ['+', '-', '<', '>', '.', ',', '[', ']']
        else:
            self.命令集 = list(命令集)
        self.输出节点数 = len(self.命令集)
        
        # 占用前几个节点作为输出节点
        assert 网络节点数 >= self.输出节点数 + self.输入特征数, "节点数过小！"
        
        # 核心复数网络
        self.核心 = 图神经网络(
            节点数=网络节点数, 
            连接概率=连接概率, 
            初始阈值=2.0, 
            背景噪声=背景噪声
        )
        
        # 将输入节点固定映射到网络的前 输入特征数 个节点
        self.输入节点索引 = list(range(self.输入特征数))
        
        # 输出节点映射到接下来的 输出节点数 个节点
        self.输出节点索引 = list(range(self.输入特征数, self.输入特征数 + self.输出节点数))
        
        # 记录输出的bf序列
        self.输出序列 = []
    
    def 编码环境(self, 原始状态):
        """将游戏状态（例如 [x,y,vx,vy]）编码成复数字典"""
        if len(原始状态) != self.输入特征数:
            raise ValueError("原始状态长度必须等于输入特征数")
        
        编码 = {}
        for i, val in enumerate(原始状态):
            编码[self.输入节点索引[i]] = complex(val, val * 0.5)
        return 编码
    
    def 推入缓存(self, 原始状态):
        """外部每获得一帧状态，就叫这个方法"""
        编码 = self.编码环境(原始状态)
        self.输入缓存.append(编码)
    
    def 决定动作(self):
        """
        网络向前运行一步，从缓存取最早的一帧作为输入，
        然后根据输出节点的激活程度选出命令。
        返回 (bf命令字符, 节点激活强度列表)
        """
        # 取缓存中最早的一帧（如果缓存未满则跳过，使用空输入）
        外部输入 = self.输入缓存[0] if len(self.输入缓存) > 0 else {}
        
        # 运行网络核心
        self.核心.运行一步(外部输入)
        
        # 读取输出节点状态
        输出激活 = []
        for idx in self.输出节点索引:
            模长 = abs(self.核心.状态[idx])
            相位 = math.atan2(self.核心.状态[idx].imag, self.核心.状态[idx].real)
            输出激活.append((模长, 相位))
        
        # 选择最大模长的节点作为动作（竞争态）
        output_idx = max(range(len(输出激活)), key=lambda i: 输出激活[i][0])
        命令 = self.命令集[output_idx]
        
        self.输出序列.append(命令)
        return 命令, 输出激活
    
    def 打印打字机(self):
        """将已输出序列像打字机一样打印出来"""
        print("打字机输出: ", " ".join(self.输出序列))
    
    def 给予奖励(self, 奖励值, 学习强度=0.1):
        """
        简单奖励机制：根据奖励值调整输出节点的阈值，
        正奖励降低阈值（更容易激活），负奖励提高阈值。
        这只是最简单的联想，未来可以接入权重学习。
        """
        for idx in self.输出节点索引:
            # 奖励调制阈值
            self.核心.阈值[idx] += -奖励值 * 学习强度
            self.核心.阈值[idx] = max(0.5, min(5.0, self.核心.阈值[idx]))


# ============ 演示 ============
if __name__ == "__main__":
    print("=" * 55)
    print("游戏AI原型：复数神经网络 + bf 打字机键盘")
    print("=" * 55)
    
    # 创建AI，4个环境特征（比如位置和速度），缓存长度3，输出8个bf命令
    ai = 游戏AI网络(输入特征数=4, 缓存长度=3, 网络节点数=16, 背景噪声=0.03)
    
    # 模拟环境：随机生成一些状态帧推入缓存
    import random
    for 帧 in range(20):
        # 模拟环境返回4个特征值
        原始状态 = [random.uniform(-2, 2) for _ in range(4)]
        ai.推入缓存(原始状态)
        
        # AI决定动作
        命令, 激活 = ai.决定动作()
        
        # 模拟显示
        print(f"帧{帧:2d}: 输入={[f'{v:.1f}' for v in 原始状态]} → 输出bf命令='{命令}' (激活强度={[f'{a[0]:.2f}' for a in 激活]})")
    
    # 如果需要训练，可以在这里调用 ai.给予奖励(...)
    
    # 最后打印打字机效果
    ai.打印打字机()
