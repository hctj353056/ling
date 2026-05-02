# 内置版单神经元.py
# 2026.4.23
# 作者：蜉蝣
# 编码：utf-8

import random

判断 = input("随机测试（1）兴奋状态（2）抑制状态（3）手动输入（0）：")

if 判断 == "1":
    # 生成随机复数
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
elif 判断 == "2":
    # 测试兴奋状态
    输入1 = complex(random.uniform(0, 10), 0)
    输入2 = complex(random.uniform(0, 10), 0)
    输入3 = complex(random.uniform(0, 10), 0)
    输入4 = complex(random.uniform(0, 10), 0)
    输入5 = complex(random.uniform(0, 10), 0)
elif 判断 == "3":
    # 测试抑制状态
    输入1 = complex(0, random.uniform(0, 10))
    输入2 = complex(0, random.uniform(0, 10))
    输入3 = complex(0, random.uniform(0, 10))
    输入4 = complex(0, random.uniform(0, 10))
    输入5 = complex(0, random.uniform(0, 10))
elif 判断 == "0":
    输入1 = complex(input("1："))
    输入2 = complex(input("2："))
    输入3 = complex(input("3："))
    输入4 = complex(input("4："))
    输入5 = complex(input("5："))
else:
    print("输入错误")
    exit()

输出 = 输入1 + 输入2 + 输入3 + 输入4 + 输入5
兴奋性阈值 = 3 + 0j
抑制性阈值 = 0 + 3j
兴奋 = 输出.real > 兴奋性阈值.real
抑制 = 输出.imag > 抑制性阈值.imag

# 根据兴奋或抑制状态输出相应的复数形式
if 兴奋 and 抑制:
    # 同时满足兴奋和抑制条件，优先输出兴奋状态
    激活输出 = 输出.real + 0j
elif 兴奋:
    激活输出 = 输出.real + 0j
elif 抑制:
    激活输出 = 0 + 输出.imag * 1j
else:
    激活输出 = 0
激活状态 = 1 if 兴奋 or 抑制 else 0

print(激活状态, 激活输出)

