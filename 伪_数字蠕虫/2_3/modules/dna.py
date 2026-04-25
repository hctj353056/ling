#!/usr/bin/env python3
"""
DNA机制模块 - 数字生命的遗传进化系统
蜉蝣阁 | ling 数字生命框架

v2.3 新增：
- DNA数据结构（邻接表+权重作为基因）
- 交叉算子（单点交叉）
- 变异算子（权重高斯噪声、新增/删除连接）
- 种群管理器（精英保留+锦标赛选择）
"""

import secrets
import math
import random
import json
import copy
from typing import List, Dict, Tuple, Optional, Any


class DNA编码器:
    """DNA编码器：将网络拓扑转换为可遗传的DNA序列"""
    
    @staticmethod
    def 编码(网络) -> dict:
        """
        将网络编码为DNA字典
        
        DNA结构：
        {
            '节点数': int,
            '邻接': {源节点: [(目标节点, 权重实部, 权重虚部), ...], ...},
            '阈值': [float, ...],
            '元数据': {...}
        }
        """
        dna = {
            '版本': '2.3',
            '节点数': 网络.节点数,
            '邻接': {},
            '阈值': list(网络.阈值),
            '元数据': {
                '总连接数': 网络.获取连接数(),
                '平均阈值': 网络.获取平均阈值(),
                '迭代次数': 网络.迭代次数
            }
        }
        
        for 源, 连接列表 in 网络.邻接.items():
            dna['邻接'][str(源)] = [
                (目标, 权重.real, 权重.imag)
                for 目标, 权重 in 连接列表
            ]
        
        return dna
    
    @staticmethod
    def 解码(dna: dict):
        """
        将DNA解码为网络参数
        
        返回: (邻接, 阈值, 元数据)
        """
        邻接 = {}
        for 源_str, 连接列表 in dna['邻接'].items():
            源 = int(源_str)
            邻接[源] = [
                (目标, complex(实部, 虚部))
                for 目标, 实部, 虚部 in 连接列表
            ]
        
        return 邻接, dna['阈值'], dna.get('元数据', {})


class DNA交叉器:
    """DNA交叉算子：两个亲本DNA产生子代DNA"""
    
    @staticmethod
    def 单点交叉(父本DNA: dict, 母本DNA: dict, 交叉点: Optional[int] = None) -> dict:
        """
        单点交叉：随机选择节点作为交叉点
        交叉点之前的基因来自父本，之后来自母本
        """
        节点数 = min(父本DNA['节点数'], 母本DNA['节点数'])
        
        if 交叉点 is None:
            交叉点 = random.randint(1, 节点数 - 1)
        
        子代DNA = {
            '版本': '2.3',
            '节点数': 节点数,
            '邻接': {},
            '阈值': [],
            '元数据': {
                '亲本1': '交叉',
                '亲本2': '交叉',
                '交叉点': 交叉点
            }
        }
        
        # 邻接基因交叉
        for i in range(节点数):
            if i < 交叉点:
                子代DNA['邻接'][str(i)] = list(父本DNA['邻接'].get(str(i), []))
            else:
                子代DNA['邻接'][str(i)] = list(母本DNA['邻接'].get(str(i), []))
        
        # 阈值基因交叉（按位置）
        父本阈值 = 父本DNA.get('阈值', [])
        母本阈值 = 母本DNA.get('阈值', [])
        for i in range(节点数):
            if i < 交叉点:
                if i < len(父本阈值):
                    子代DNA['阈值'].append(父本阈值[i])
                else:
                    子代DNA['阈值'].append(1.0)
            else:
                if i < len(母本阈值):
                    子代DNA['阈值'].append(母本阈值[i])
                else:
                    子代DNA['阈值'].append(1.0)
        
        return 子代DNA
    
    @staticmethod
    def 均匀交叉(父本DNA: dict, 母本DNA: dict, 基因交换概率: float = 0.5) -> dict:
        """
        均匀交叉：每个基因独立决定来自哪个亲本
        """
        节点数 = min(父本DNA['节点数'], 母本DNA['节点数'])
        
        子代DNA = {
            '版本': '2.3',
            '节点数': 节点数,
            '邻接': {},
            '阈值': [],
            '元数据': {
                '亲本1': '均匀交叉',
                '亲本2': '均匀交叉'
            }
        }
        
        for i in range(节点数):
            父本连接 = 父本DNA['邻接'].get(str(i), [])
            母本连接 = 母本DNA['邻接'].get(str(i), [])
            
            # 随机选择连接基因来源
            if random.random() < 基因交换概率:
                子代DNA['邻接'][str(i)] = list(父本连接)
            else:
                子代DNA['邻接'][str(i)] = list(母本连接)
        
        # 阈值基因独立选择
        父本阈值 = 父本DNA.get('阈值', [])
        母本阈值 = 母本DNA.get('阈值', [])
        for i in range(节点数):
            if random.random() < 基因交换概率:
                子代DNA['阈值'].append(父本阈值[i] if i < len(父本阈值) else 1.0)
            else:
                子代DNA['阈值'].append(母本阈值[i] if i < len(母本阈值) else 1.0)
        
        return 子代DNA


class DNA变异器:
    """DNA变异算子：引入遗传多样性"""
    
    def __init__(self,
                 权重变异率: float = 0.2,
                 权重变异强度: float = 0.3,
                 连接变异率: float = 0.1,
                 新增连接概率: float = 0.05,
                 删除连接概率: float = 0.03,
                 阈值变异率: float = 0.15,
                 阈值变异强度: float = 0.2):
        """
        变异参数：
        - 权重变异率: 每个连接权重变异的概率
        - 权重变异强度: 高斯噪声的标准差（相对值）
        - 连接变异率: 连接结构变异的概率
        - 新增/删除连接概率: 结构变异的具体操作
        - 阈值变异率: 每个节点阈值变异的概率
        - 阈值变异强度: 阈值调整的相对幅度
        """
        self.权重变异率 = 权重变异率
        self.权重变异强度 = 权重变异强度
        self.连接变异率 = 连接变异率
        self.新增连接概率 = 新增连接概率
        self.删除连接概率 = 删除连接概率
        self.阈值变异率 = 阈值变异率
        self.阈值变异强度 = 阈值变异强度
    
    def 高斯变异(self, dna: dict) -> dict:
        """
        高斯变异：对权重和阈值添加高斯噪声
        """
        子代DNA = copy.deepcopy(dna)
        子代DNA['元数据']['变异类型'] = '高斯'
        
        # 权重变异
        for 源_str, 连接列表 in 子代DNA['邻接'].items():
            for j in range(len(连接列表)):
                目标, 实部, 虚部 = 连接列表[j]
                if random.random() < self.权重变异率:
                    实部 += random.gauss(0, self.权重变异强度)
                    虚部 += random.gauss(0, self.权重变异强度)
                    连接列表[j] = (目标, 实部, 虚部)
        
        # 阈值变异
        for i in range(len(子代DNA['阈值'])):
            if random.random() < self.阈值变异率:
                偏移量 = 子代DNA['阈值'][i] * random.gauss(0, self.阈值变异强度)
                子代DNA['阈值'][i] = max(0.1, min(5.0, 子代DNA['阈值'][i] + 偏移量))
        
        return 子代DNA
    
    def 结构变异(self, dna: dict) -> dict:
        """
        结构变异：新增或删除连接
        """
        子代DNA = copy.deepcopy(dna)
        子代DNA['元数据']['变异类型'] = '结构'
        节点数 = 子代DNA['节点数']
        
        新邻接 = {}
        for 源_str, 连接列表 in 子代DNA['邻接'].items():
            源 = int(源_str)
            新连接 = []
            
            for 目标, 实部, 虚部 in 连接列表:
                if random.random() < self.删除连接概率:
                    continue  # 删除此连接
                新连接.append((目标, 实部, 虚部))
            
            # 新增连接
            for 目标 in range(节点数):
                if 源 != 目标 and not any(t == 目标 for t, _, _ in 新连接):
                    if random.random() < self.新增连接概率:
                        新权重 = (
                            random.uniform(-1, 1),
                            random.uniform(-1, 1)
                        )
                        新连接.append((目标, 新权重[0], 新权重[1]))
            
            新邻接[源_str] = 新连接
        
        子代DNA['邻接'] = 新邻接
        子代DNA['元数据']['总连接数'] = sum(len(v) for v in 新邻接.values())
        
        return 子代DNA
    
    def 混合变异(self, dna: dict) -> dict:
        """
        混合变异：依次应用高斯变异和结构变异
        """
        dna = self.高斯变异(dna)
        dna = self.结构变异(dna)
        dna['元数据']['变异类型'] = '混合'
        return dna


class DNAManager:
    """
    DNA管理器：管理种群、执行遗传算法
    
    遗传算法流程：
    1. 初始化种群（从网络或随机）
    2. 评估适应度（食物数量、存活时间等）
    3. 选择（精英保留 + 锦标赛选择）
    4. 交叉（产生子代）
    5. 变异（引入多样性）
    6. 重复步骤2-5
    """
    
    def __init__(self,
                 种群大小: int = 10,
                 精英数量: int = 2,
                 锦标赛规模: int = 3,
                 变异器: Optional[DNA变异器] = None):
        self.种群大小 = 种群大小
        self.精英数量 = 精英数量
        self.锦标赛规模 = 锦标赛规模
        self.变异器 = 变异器 or DNA变异器()
        
        self.种群: List[dict] = []  # DNA列表
        self.适应度: List[float] = []  # 对应适应度
        self.代际历史: List[dict] = []  # 进化历史
        self.当前代数 = 0
        
        # 最优DNA缓存
        self.最优DNA: Optional[dict] = None
        self.最优适应度 = float('-inf')
    
    def 初始化种群(self, 模板网络=None, 节点数: int = 12):
        """
        初始化种群：
        - 如果提供了模板网络，复制N份作为初始种群
        - 否则创建随机种群
        """
        self.种群 = []
        
        if 模板网络 is not None:
            for _ in range(self.种群大小):
                dna = DNA编码器.编码(模板网络)
                self.种群.append(dna)
        else:
            for _ in range(self.种群大小):
                dna = self._随机生成DNA(节点数)
                self.种群.append(dna)
        
        self.适应度 = [0.0] * self.种群大小
    
    def _随机生成DNA(self, 节点数: int) -> dict:
        """生成随机DNA"""
        dna = {
            '版本': '2.3',
            '节点数': 节点数,
            '邻接': {},
            '阈值': [1.0] * 节点数,
            '元数据': {'来源': '随机生成'}
        }
        
        for i in range(节点数):
            连接列表 = []
            for j in range(节点数):
                if i != j and random.random() < 0.3:  # 30%连接概率
                    连接 = (
                        j,
                        random.uniform(-1, 1),
                        random.uniform(-1, 1)
                    )
                    连接列表.append(连接)
            dna['邻接'][str(i)] = 连接列表
        
        return dna
    
    def 评估种群(self, 评估函数):
        """
        评估种群中每个个体的适应度
        
        评估函数签名: 评估函数(dna: dict) -> float
        """
        for i, dna in enumerate(self.种群):
            适应度 = 评估函数(dna)
            self.适应度[i] = 适应度
            
            # 更新最优
            if 适应度 > self.最优适应度:
                self.最优适应度 = 适应度
                self.最优DNA = copy.deepcopy(dna)
    
    def 选择(self) -> List[dict]:
        """
        选择操作：
        1. 精英保留：直接复制最优个体
        2. 锦标赛选择：从随机子集中选择最优者
        """
        选中个体 = []
        
        # 精英保留
        精英索引 = sorted(range(len(self.适应度)), 
                          key=lambda i: self.适应度[i],
                          reverse=True)[:self.精英数量]
        for idx in 精英索引:
            选中个体.append(copy.deepcopy(self.种群[idx]))
        
        # 锦标赛选择填充剩余位置
        while len(选中个体) < self.种群大小:
            候选池 = random.sample(range(len(self.种群)), 
                                    min(self.锦标赛规模, len(self.种群)))
            最优候选 = max(候选池, key=lambda i: self.适应度[i])
            选中个体.append(copy.deepcopy(self.种群[最优候选]))
        
        return 选中个体
    
    def 繁殖(self, 被选中的个体: List[dict]) -> List[dict]:
        """
        繁殖操作：交叉 + 变异
        """
        子代种群 = []
        
        # 精英个体直接进入下一代
        for i in range(min(self.精英数量, len(被选中的个体))):
            子代种群.append(被选中的个体[i])
        
        # 剩余位置通过交叉变异产生
        while len(子代种群) < self.种群大小:
            父本 = random.choice(被选中的个体)
            母本 = random.choice(被选中的个体)
            
            # 交叉
            if random.random() < 0.8:  # 80%交叉率
                if random.random() < 0.5:
                    子代 = DNA交叉器.单点交叉(父本, 母本)
                else:
                    子代 = DNA交叉器.均匀交叉(父本, 母本)
            else:
                子代 = copy.deepcopy(父本)
            
            # 变异
            子代 = self.变异器.混合变异(子代)
            
            子代种群.append(子代)
        
        return 子代种群[:self.种群大小]
    
    def 进化一步(self, 评估函数) -> dict:
        """
        执行一步进化
        """
        # 评估
        self.评估种群(评估函数)
        
        # 选择
        被选中 = self.选择()
        
        # 繁殖
        子代 = self.繁殖(被选中)
        
        # 更新种群
        self.种群 = 子代
        self.当前代数 += 1
        
        # 记录历史
        历史记录 = {
            '代数': self.当前代数,
            '最优适应度': self.最优适应度,
            '平均适应度': sum(self.适应度) / len(self.适应度),
            '适应度方差': self._计算方差(self.适应度)
        }
        self.代际历史.append(历史记录)
        
        return 历史记录
    
    def _计算方差(self, 数值列表: List[float]) -> float:
        均值 = sum(数值列表) / len(数值列表)
        方差 = sum((x - 均值) ** 2 for x in 数值列表) / len(数值列表)
        return 方差
    
    def 获取最优DNA(self) -> Optional[dict]:
        """获取历史最优DNA"""
        return self.最优DNA
    
    def 保存DNA(self, dna: dict, 文件路径: str):
        """保存DNA到文件"""
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(dna, f, indent=2, ensure_ascii=False)
    
    def 加载DNA(self, 文件路径: str) -> dict:
        """从文件加载DNA"""
        with open(文件路径, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def 导出种群(self) -> str:
        """导出种群统计信息"""
        lines = [
            f"=== DNA种群统计 (第{self.当前代数}代) ===",
            f"种群大小: {len(self.种群)}",
            f"精英数量: {self.精英数量}",
            f"最优适应度: {self.最优适应度:.4f}",
            f"平均适应度: {sum(self.适应度)/len(self.适应度):.4f}",
            "",
            "各DNA连接数:"
        ]
        
        for i, dna in enumerate(self.种群):
            连接数 = sum(len(v) for v in dna['邻接'].values())
            lines.append(f"  DNA-{i}: 连接={连接数}, 适应度={self.适应度[i]:.4f}")
        
        return "\n".join(lines)


class DNAEvolver:
    """
    DNA进化器：封装完整的进化流程
    
    使用方式：
    1. 创建进化器并初始化种群
    2. 设置评估函数
    3. 调用 run() 开始进化
    """
    
    def __init__(self, 种群管理器: DNAManager):
        self.manager = 种群管理器
        self.评估函数 = None
        self.回调函数 = None
        self.是否停止 = False
    
    def 设置评估函数(self, 函数):
        """设置适应度评估函数"""
        self.评估函数 = 函数
    
    def 设置回调(self, 函数):
        """设置每代结束后的回调函数"""
        self.回调函数 = 函数
    
    def 停止(self):
        """请求停止进化"""
        self.是否停止 = True
    
    def run(self, 最大代数: int = 50) -> dict:
        """
        运行进化
        
        返回: 进化结果摘要
        """
        if self.评估函数 is None:
            raise ValueError("必须先设置评估函数")
        
        进化结果 = {
            '最终代数': 0,
            '最终最优适应度': 0,
            '历史': []
        }
        
        for 代 in range(最大代数):
            if self.是否停止:
                break
            
            # 执行一步进化
            历史 = self.manager.进化一步(self.评估函数)
            进化结果['历史'].append(历史)
            进化结果['最终代数'] = 代 + 1
            进化结果['最终最优适应度'] = 历史['最优适应度']
            
            # 回调
            if self.回调函数:
                self.回调函数(代, 历史, self.manager)
        
        return 进化结果


# ============ 辅助函数 ============

def 创建进化网络(模板网络, dna: dict):
    """
    根据DNA创建新网络（用于将进化后的DNA应用到网络）
    
    不会修改原模板网络，返回新的邻接和阈值
    """
    邻接, 阈值, 元数据 = DNA编码器.解码(dna)
    return 邻接, 阈值


def 克隆网络到DNA(网络) -> dict:
    """将网络克隆为DNA"""
    return DNA编码器.编码(网络)


def 比较DNA相似度(dna1: dict, dna2: dict) -> float:
    """
    计算两个DNA的相似度（0-1之间）
    1表示完全相同，0表示完全不同
    """
    if dna1['节点数'] != dna2['节点数']:
        return 0.0
    
    节点数 = dna1['节点数']
    总权重差 = 0.0
    总连接数 = 0
    
    for i in range(节点数):
        连接1 = dict(dna1['邻接'].get(str(i), []))
        连接2 = dict(dna2['邻接'].get(str(i), []))
        
        所有目标 = set(连接1.keys()) | set(连接2.keys())
        for 目标 in 所有目标:
            总连接数 += 1
            if 目标 in 连接1 and 目标 in 连接2:
                w1 = complex(*连接1[目标])
                w2 = complex(*连接2[目标])
                差 = abs(w1 - w2)
                总权重差 += min(差, 2.0) / 2.0  # 归一化
            else:
                总权重差 += 1.0  # 一方有连接一方没有
    
    相似度 = 1.0 - (总权重差 / max(总连接数, 1))
    return max(0.0, min(1.0, 相似度))


if __name__ == '__main__':
    # 简单测试
    print("=== DNA机制测试 ===\n")
    
    # 创建随机DNA
    manager = DNAManager(种群大小=5, 精英数量=1)
    manager.初始化种群(节点数=8)
    print("初始种群已创建")
    
    # 模拟评估函数
    def 模拟评估(dna):
        连接数 = sum(len(v) for v in dna['邻接'].values())
        return 连接数 / 100.0  # 简单模拟：连接数越多越好
    
    # 评估
    manager.评估种群(模拟评估)
    print(f"最优适应度: {manager.最优适应度:.4f}")
    
    # 繁殖一代
    被选中 = manager.选择()
    子代 = manager.繁殖(被选中)
    manager.种群 = 子代
    manager.当前代数 = 1
    
    print("已完成一轮遗传操作")
    
    # 导出统计
    print("\n" + manager.导出种群())
