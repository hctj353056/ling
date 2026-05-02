# 内置版单神经元.py
# 2026.4.23
# 作者：蜉蝣
# 编码：utf-8

import random

兴奋性阈值 = 3 + 0j
抑制性阈值 = 0 + 3j

def 判断激活状态(输出):
    兴奋 = 输出.real > 兴奋性阈值.real
    抑制 = 输出.imag > 抑制性阈值.imag
    
    if 兴奋 and 抑制:
        激活输出 = 输出.real + 0j
    elif 兴奋:
        激活输出 = 输出.real + 0j
    elif 抑制:
        激活输出 = 0 + 输出.imag * 1j
    else:
        激活输出 = 0
    
    激活状态 = 1 if 兴奋 or 抑制 else 0
    return 激活状态, 激活输出

def 随机神经元():
    输入1 = complex(random.uniform(0, 10), random.uniform(0, 10))
    print(输入1)
    输入2 = complex(random.uniform(0, 10), random.uniform(0, 10))
    print(输入2)
    输入3 = complex(random.uniform(0, 10), random.uniform(0, 10))
    print(输入3)
    输入4 = complex(random.uniform(0, 10), random.uniform(0, 10))
    print(输入4)
    输入5 = complex(random.uniform(0, 10), random.uniform(0, 10))
    print(输入5)
    输出 = 输入1 + 输入2 + 输入3 + 输入4 + 输入5
    return 判断激活状态(输出)
激活状态, 激活输出 = 随机神经元()

def 神经元2():
    列表 = [随机神经元(), 随机神经元(), 随机神经元(), 随机神经元(), 随机神经元()]
    输入列表 = [列表[i] for i in range(5)]
    print(输入列表)
    处理列表 = [输入列表[i][1] for i in range(5)]
    print(处理列表)
    输出 = sum(处理列表)
    return 判断激活状态(输出)
激活状态, 激活输出 = 神经元2()

def 输出神经元():
    列表 = [神经元2(), 神经元2(), 神经元2(), 神经元2(), 神经元2()]
    输入列表 = [列表[i] for i in range(5)]
    print(输入列表)
    处理列表 = [输入列表[i][1] for i in range(5)]
    print(处理列表)
    输出 = sum(处理列表)
    return 判断激活状态(输出)
激活状态, 激活输出 = 输出神经元()
print(激活状态, 激活输出)