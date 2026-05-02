<div align='center'>
    <img src="./images/图像.jpg" alt="ling" width="100%">
    <h1>ling</h1>
</div>

<p align="center">
  <a href="https://github.com/hctj353056/ling/stargazers">
    <img src="https://img.shields.io/github/stars/hctj353056/ling.svg?style=popout-square" alt="GitHub stars">
  </a>
  <a href="https://github.com/hctj353056/ling/issues">
    <img src="https://img.shields.io/github/issues/hctj353056/ling.svg?style=popout-square" alt="GitHub issues">
  </a>
</p>

---

## 项目简介

本仓库存放蜉蝣（hctj353056）的个人实验项目和代码，专注于神经元网络模拟和人工智能研究。

**核心理念：**

- 纯Python实现，无外部依赖
- 适合移动端和低资源环境运行
- 探索生物启发的神经网络模型

## 快速开始

### 运行神经元网络模拟器

```bash
# 基础版本
python3 神经元网络/neuron_simulator.py

# 空间干涉版本
python3 神经元网络/neuron_simulator_v2.py

# 对话系统原型
python3 神经元网络/neuron_chat.py
```

### 运行数字蠕虫实验

```bash
cd 伪_数字蠕虫/2_3
python3 00.py
```

## 项目结构

```
ling/
├── 神经元网络/                 # 核心神经元网络模块
│   ├── neuron_simulator.py     # v1 基础版
│   ├── neuron_simulator_v2.py  # v2 空间干涉版
│   ├── neuron_chat.py          # 对话系统原型
│   ├── 图神经网络.py           # 图神经网络实现
│   ├── 图神经网络v2.py         # 图神经网络改进版
│   └── 复数神经网络.py         # 复数域神经网络
├── 智能体构架/                  # 智能体架构实验
│   ├── 内置版单神经元.py
│   ├── 标准化版单神经元.py
│   └── 模块化单神经元.py
├── 伪_数字蠕虫/                 # 数字蠕虫实验（概念验证）
│   ├── 1_0/                    # 初代版本
│   ├── 2_0/                    # 第二代版本
│   └── 2_3/                    # 当前版本（含DNA进化）
├── images/                     # 项目图片
├── .github/                    # GitHub配置
│   └── workflows/              # CI/CD工作流
├── README.md                   # 项目说明（中文）
├── README_en.md                # 项目说明（英文）
└── requirements.txt            # 依赖列表
```

## 核心模块

### 🧠 神经元网络模拟器

`./神经元网络/` - 纯Python实现的神经元网络模型

**核心特性：**

- 神经元模型：二值状态、极性、动态阈值、计数器机制
- 网络功能：稀疏连接矩阵、并行计算、全局时间步
- 结构演化：权重微调、连接修剪、新连接生成
- 三维空间分布 + 邻域干涉机制

**文件说明：**

| 文件                       | 版本 | 说明        |
| ------------------------ | -- | --------- |
| `neuron_simulator.py`    | v1 | 基础版神经元模拟器 |
| `neuron_simulator_v2.py` | v2 | 空间干涉版     |
| `neuron_chat.py`         | v3 | 对话系统原型    |
| `图神经网络.py`               | -  | 图神经网络基础实现 |
| `图神经网络v2.py`             | v2 | 改进版图神经网络  |
| `复数神经网络.py`              | -  | 复数域神经网络   |

### 🐛 数字蠕虫实验

`./伪_数字蠕虫/` - 数字生命模拟实验

**版本演进：**

- **1.0**：基础神经网络控制
- **2.0**：模块化架构，快照系统
- **2.3**：DNA进化机制，优化参数

### 🤖 智能体构架

`./智能体构架/` - 智能体架构实验

## 开发指南

### 环境要求

- Python >= 3.10
- 无外部依赖（推荐使用requirements.txt管理）

### 代码风格

遵循PEP 8规范，支持中文变量和函数名。

## 相关仓库

- [FSG-language](https://github.com/hctj353056/FSG-language) - FSG逻辑编程语言

## 版本历史

| 版本   | 日期 | 变更内容      |
| ---- | -- | --------- |
| v2.3 | -  | 添加DNA进化机制 |
| v2.0 | -  | 模块化架构重构   |
| v1.0 | -  | 初始版本      |

## 作者

蜉蝣子 ♡

## 许可证

MIT License

***

*蜉熵阁 · ling项目*
