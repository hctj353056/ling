# 图节点复数神经元网络 v2
# 2026.4.24
# 改进：相位保留 + 模长激活 + 竞争态
# 编码：utf-8

import secrets
import math

class 图神经网络:
    def __init__(self, 节点数=10, 初始阈值=2.0):
        self.节点数 = 节点数
        # 每个节点的状态（复数）
        self.状态 = [0+0j] * 节点数
        # 每个节点的阈值（标量，基于模长）
        self.阈值 = [初始阈值] * 节点数
        # 邻接表：{源节点: [(目标节点, 权重复数), ...]}
        self.邻接 = {i: [] for i in range(节点数)}
        # 活动历史
        self.激活历史 = [0] * 节点数
        # 统计
        self.迭代次数 = 0
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
            模长 = abs(self.状态[源])
            if 模长 > 0.1:  # 有活动才发放
                活动[源] = 1
                for 目标, 权重 in self.邻接[源]:
                    新状态[目标] += self.状态[源] * 权重
        
        if 外部输入:
            for 节点, 值 in 外部输入.items():
                新状态[节点] += 值
        
        self.状态 = 新状态
        self.激活历史 = 活动
        self.迭代次数 += 1
    
    def 激活判定(self):
        """基于模长的激活判定，保留完整相位信息"""
        新状态 = []
        for i in range(self.节点数):
            当前 = self.状态[i]
            模长 = abs(当前)
            
            if 模长 > self.阈值[i]:
                # 激活：保留完整复数，相位信息不丢失
                新状态.append(当前)
            else:
                # 未激活：衰减到零
                新状态.append(0+0j)
        
        self.状态 = 新状态
    
    def STDP调整(self, 学习率=0.1, 弱化率=0.05):
        """时序依赖可塑性 - 强化共激活，弱化单向激活"""
        for 源 in range(self.节点数):
            for idx, (目标, 权重) in enumerate(self.邻接[源]):
                源激活 = self.激活历史[源]
                目标激活 = self.激活历史[目标]
                
                if 源激活 and 目标激活:
                    # 双向激活：强化
                    新权重 = 权重 + 学习率 * 权重
                    self.邻接[源][idx] = (目标, 新权重)
                elif 源激活 and not 目标激活:
                    # 单向激活：弱化
                    新权重 = 权重 - 弱化率 * abs(权重)
                    if abs(新权重) > 0.1:
                        self.邻接[源][idx] = (目标, 新权重)
    
    def 局部调整(self, 修剪阈值=0.2, 生长概率=0.05):
        """修剪弱连接 + 生长新连接"""
        for 源 in range(self.节点数):
            # 修剪
            self.邻接[源] = [(目标, 权重) for 目标, 权重 in self.邻接[源] 
                            if abs(权重) >= 修剪阈值]
            
            # 生长
            if abs(self.状态[源]) > self.阈值[源] * 0.5:  # 活跃度较高
                for 目标 in range(self.节点数):
                    if 源 != 目标 and secrets.choice([True, False, False, False, False]):
                        if not any(t == 目标 for t, _ in self.邻接[源]):
                            新权重 = complex(
                                secrets.choice(range(-5, 5)) / 10,
                                secrets.choice(range(-5, 5)) / 10
                            )
                            self.邻接[源].append((目标, 新权重))
    
    def 全局阈值调整(self, 目标活跃比例=0.3, 调整率=0.02):
        """根据活跃节点比例调整阈值"""
        活跃数 = sum(1 for s in self.状态 if abs(s) > self.阈值[self.状态.index(s)])
        活跃比例 = 活跃数 / self.节点数
        
        偏离 = 活跃比例 - 目标活跃比例
        修正量 = 偏离 * 调整率
        
        for i in range(self.节点数):
            新阈值 = self.阈值[i] + 修正量
            self.阈值[i] = max(0.5, min(5.0, 新阈值))  # 限制范围
    
    def 运行一步(self, 外部输入=None):
        self.一步传播(外部输入)
        self.激活判定()
        self.STDP调整()
        self.局部调整()
        self.全局阈值调整()
        return self.状态
    
    def 获取输出(self):
        """获取激活的节点状态（用于输出层）"""
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
                print(f"    节点{i}: |{模长:.2f}| ∠{相位:.1f}°")


if __name__ == "__main__":
    print("=" * 55)
    print("图节点复数神经网络 v2 - 相位保留 + 模长激活")
    print("=" * 55)
    
    网 = 图神经网络(节点数=8, 初始阈值=2.0)
    连接数 = sum(len(v) for v in 网.邻接.values())
    print(f"\n初始：{网.节点数}个节点, {连接数}条连接, 阈值=2.0")
    
    # 输入序列
    输入序列 = [
        {0: 3+1j},      # 节点0：强兴奋+弱抑制 → 相位约18°
        {1: 1+3j},      # 节点1：弱兴奋+强抑制 → 相位约72°
        {2: 2+2j},      # 节点2：平衡 → 相位45°
        {},              # 无输入
        {3: 4+0j},      # 节点3：纯兴奋
        {},              # 无输入
        {4: 0+4j},      # 节点4：纯抑制
        {},              # 无输入
        {5: 3-2j},      # 节点5：第四象限
        {},              # 无输入
    ]
    
    for i, 输入 in enumerate(输入序列, 1):
        网.运行一步(外部输入=输入 if 输入 else None)
        网.打印状态(i)
    
    print(f"\n最终活跃节点: {网.获取输出()}")
    print(f"最终连接数: {sum(len(v) for v in 网.邻接.values())}")
