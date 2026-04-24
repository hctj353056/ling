# 图节点复数神经元网络
# 2026.4.24
# 编码：utf-8

import secrets

class 图神经网络:
    def __init__(self, 节点数=10, 初始兴奋阈值=3+0j, 初始抑制阈值=0+3j):
        self.节点数 = 节点数
        self.状态 = [0+0j] * 节点数
        self.兴奋阈值 = [初始兴奋阈值] * 节点数
        self.抑制阈值 = [初始抑制阈值] * 节点数
        self.邻接 = {i: [] for i in range(节点数)}
        self.激活历史 = [0] * 节点数
        self._随机初始化连接()
    
    def _随机初始化连接(self, 连接概率=0.3):
        for 源 in range(self.节点数):
            for 目标 in range(self.节点数):
                if 源 != 目标 and secrets.choice([True, False, False, False]):
                    权重 = complex(
                        secrets.choice(range(-10, 10)) / 10,
                        secrets.choice(range(-10, 10)) / 10
                    )
                    self.邻接[源].append((目标, 权重))
    
    def 一步传播(self, 外部输入=None):
        新状态 = [0+0j] * self.节点数
        活动 = [0] * self.节点数
        
        for 源 in range(self.节点数):
            if abs(self.状态[源]) > 0.1:
                活动[源] = 1
                for 目标, 权重 in self.邻接[源]:
                    新状态[目标] += self.状态[源] * 权重
        
        if 外部输入:
            for 节点, 值 in 外部输入.items():
                新状态[节点] += 值
        
        self.状态 = 新状态
        self.激活历史 = 活动
    
    def 激活判定(self):
        激活结果 = []
        for i in range(self.节点数):
            输出 = self.状态[i]
            实部 = 输出.real
            虚部 = 输出.imag
            兴奋 = 实部 > self.兴奋阈值[i].real
            抑制 = 虚部 > self.抑制阈值[i].imag
            if 兴奋 and 抑制:
                激活输出 = 实部 + 0j
            elif 兴奋:
                激活输出 = 实部 + 0j
            elif 抑制:
                激活输出 = 0 + 虚部*1j
            else:
                激活输出 = 0+0j
            激活结果.append(激活输出)
        self.状态 = 激活结果
    
    def STDP调整(self, 学习率=0.1):
        """时序依赖可塑性"""
        for 源 in range(self.节点数):
            for idx, (目标, 权重) in enumerate(self.邻接[源]):
                if self.激活历史[源] and self.激活历史[目标]:
                    新权重 = 权重 + 学习率 * 权重
                    self.邻接[源][idx] = (目标, 新权重)
                elif self.激活历史[源] and not self.激活历史[目标]:
                    新权重 = 权重 - 学习率 * abs(权重) * 0.5
                    if abs(新权重) > 0.1:
                        self.邻接[源][idx] = (目标, 新权重)
    
    def 局部调整图结构(self, 修剪阈值=0.2, 生长概率=0.1):
        for 源 in range(self.节点数):
            self.邻接[源] = [(目标, 权重) for 目标, 权重 in self.邻接[源] 
                            if abs(权重) >= 修剪阈值]
            
            if abs(self.状态[源]) > 2:
                for 目标 in range(self.节点数):
                    if 源 != 目标 and secrets.choice([True, False, False, False, False]):
                        if not any(t == 目标 for t, _ in self.邻接[源]):
                            新权重 = complex(
                                secrets.choice(range(-5, 5)) / 10,
                                secrets.choice(range(-5, 5)) / 10
                            )
                            self.邻接[源].append((目标, 新权重))
    
    def 全局阈值调整(self, 目标平均活动=0.5, 调整率=0.05):
        总活动 = sum(abs(s) for s in self.状态) / self.节点数
        if 总活动 > 0.1:
            偏离 = 总活动 - 目标平均活动
            for i in range(self.节点数):
                修正量 = 偏离 * 调整率
                新实 = max(0.1, self.兴奋阈值[i].real - 修正量)
                新虚 = max(0.1, self.抑制阈值[i].imag - 修正量)
                self.兴奋阈值[i] = complex(新实, self.兴奋阈值[i].imag)
                self.抑制阈值[i] = complex(self.抑制阈值[i].real, 新虚)
    
    def 运行一步(self, 外部输入=None):
        self.一步传播(外部输入)
        self.激活判定()
        self.STDP调整()
        self.局部调整图结构()
        self.全局阈值调整()
        return self.状态
    
    def 打印状态(self, 步数):
        活跃 = sum(1 for s in self.状态 if abs(s) > 0.1)
        连接数 = sum(len(v) for v in self.邻接.values())
        print(f"第{步数}步: 活跃={活跃}, 连接={连接数}")
        if 活跃 > 0:
            for i, s in enumerate(self.状态):
                if abs(s) > 0.1:
                    print(f"    节点{i}: {s:.2f}")


if __name__ == "__main__":
    print("=" * 50)
    print("图节点复数神经网络")
    print("=" * 50)
    
    网 = 图神经网络(节点数=8, 初始兴奋阈值=2+0j, 初始抑制阈值=0+2j)
    连接数 = sum(len(v) for v in 网.邻接.values())
    print(f"\n初始：{网.节点数}个节点, {连接数}条连接")
    
    # 外部注入模式：模拟感觉输入
    输入序列 = [
        {0: 3+0j},      # 节点0强兴奋
        {1: 0+3j},      # 节点1强抑制
        {2: 4+0j, 3: 0+4j},  # 多节点
        {},             # 无输入
        {},             # 无输入
        {4: 5+0j},      # 节点4
        {},             # 无输入
        {},             # 无输入
        {},             # 无输入
        {},             # 无输入
    ]
    
    for i, 输入 in enumerate(输入序列, 1):
        网.运行一步(外部输入=输入 if 输入 else None)
        网.打印状态(i)
    
    print(f"\n最终活跃节点: {[i for i, s in enumerate(网.状态) if abs(s) > 0.1]}")
    print(f"最终连接数: {sum(len(v) for v in 网.邻接.values())}")
