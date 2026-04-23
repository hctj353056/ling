# 复数神经网络框架
# 2026.4.24
# 作者：蜉蝣

import json
import random

class 复数神经网络:
    def __init__(self, 配置路径):
        with open(配置路径, 'r', encoding='utf-8') as f:
            self.配置 = json.load(f)
        
        self.神经元数 = self.配置["神经元数"]
        self.状态 = [0j] * self.神经元数  # 每个神经元的复数状态
        self.阈值 = self._初始化阈值()
        self.连接 = self.配置["连接"]
        self.词表 = self.配置["词表"]
    
    def _初始化阈值(self):
        """根据角色初始化阈值"""
        阈值表 = {}
        for 角色, 范围 in self.配置["角色范围"].items():
            阈值表[角色] = complex(
                self.配置["阈值"][角色]["实部"],
                self.配置["阈值"][角色]["虚部"]
            )
        return 阈值表
    
    def _获取阈值(self, 神经元编号):
        """根据编号获取阈值"""
        for 角色, 范围 in self.配置["角色范围"].items():
            if 范围[0] <= 神经元编号 <= 范围[1]:
                return self.阈值[角色]
        return 3 + 3j  # 默认阈值
    
    def _计算神经元输入(self, 目标编号):
        """计算目标神经元接收到的总输入"""
        总输入 = 0j
        for 连接 in self.连接:
            if 连接["to"] == 目标编号:
                权重列表 = 连接["weights"]
                for i, 源编号 in enumerate(连接["from"]):
                    总输入 += self.状态[源编号] * 权重列表[i]
        return 总输入
    
    def _激活函数(self, 编号, 总输入):
        """复数阈值激活函数"""
        阈值 = self._获取阈值(编号)
        兴奋 = 总输入.real > 阈值.real
        抑制 = 总输入.imag > 阈值.imag
        
        if 兴奋 and 抑制:
            return complex(总输入.real, 0)  # 优先兴奋
        elif 兴奋:
            return complex(总输入.real, 0)
        elif 抑制:
            return complex(0, 总输入.imag)
        else:
            return 0j
    
    def 前向传播(self, 输入向量):
        """单次前向传播"""
        # 1. 写入输入层
        输入范围 = self.配置["角色范围"]["输入"]
        for i in range(输入范围[1] - 输入范围[0] + 1):
            self.状态[输入范围[0] + i] = complex(输入向量[i], 0)
        
        # 2. 计算中间层
        中间范围 = self.配置["角色范围"]["中间"]
        for 编号 in range(中间范围[0], 中间范围[1] + 1):
            总输入 = self._计算神经元输入(编号)
            self.状态[编号] = self._激活函数(编号, 总输入)
        
        # 3. 计算输出层
        输出范围 = self.配置["角色范围"]["输出"]
        for 编号 in range(输出范围[0], 输出范围[1] + 1):
            总输入 = self._计算神经元输入(编号)
            self.状态[编号] = self._激活函数(编号, 总输入)
        
        return self.状态
    
    def 获取输出(self):
        """获取输出层状态"""
        输出范围 = self.配置["角色范围"]["输出"]
        return [self.状态[i] for i in range(输出范围[0], 输出范围[1] + 1)]
    
    def 词表匹配(self, 复数向量):
        """软匹配到词表"""
        结果 = {}
        for 词, 词复数 in self.词表.items():
            if isinstance(词复数, (int, float)):
                词复数 = complex(词复数, 0)
            距离 = abs(复数向量 - 词复数)
            结果[词] = max(0, 1 - 距离 / 10)  # 归一化距离
        return 结果


# ========== 示例配置 ==========
示例配置 = {
    "神经元数": 32,
    "角色范围": {
        "输入": [0, 7],
        "中间": [8, 23],
        "输出": [24, 31]
    },
    "阈值": {
        "输入": {"实部": 0, "虚部": 0},
        "中间": {"实部": 3, "虚部": 3},
        "输出": {"实部": 3, "虚部": 3}
    },
    "连接": [
        {"from": [0, 1, 2], "to": 8, "weights": [0.5, 0.3, 0.2]},
        {"from": [3, 4], "to": 8, "weights": [0.4, 0.6]},
        {"from": [8, 9], "to": 24, "weights": [0.6, 0.4]},
        {"from": [10, 11, 12], "to": 25, "weights": [0.3, 0.3, 0.4]},
    ],
    "词表": {
        "走": 24,
        "停": 25,
        "左转": 26,
        "右转": 27
    }
}

if __name__ == "__main__":
    # 保存示例配置
    with open("网络配置.json", "w", encoding="utf-8") as f:
        json.dump(示例配置, f, ensure_ascii=False, indent=2)
    
    # 创建网络
    网络 = 复数神经网络("网络配置.json")
    
    # 测试输入
    输入 = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    网络.前向传播(输入)
    
    # 输出结果
    输出 = 网络.获取输出()
    print("输出层状态:", 输出)
    
    # 词表匹配
    for i, 复数 in enumerate(输出):
        print(f"输出{i}: {复数}")
    
    print("词表匹配:", 网络.词表匹配(输出[0] if 输出[0] else 0j))
