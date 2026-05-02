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

<div align='center'>
  <a href="./README.md">中文</a> | <a href="./README_en.md">English</a>
</div>

---

## Project Introduction

This repository contains personal experimental projects and code by FuYou (hctj353056), focusing on neural network simulation and AI research.

**Core Philosophy:**
- Pure Python implementation with no external dependencies
- Optimized for mobile and low-resource environments
- Exploring biologically inspired neural network models

## Quick Start

### Run Neuron Network Simulator

```bash
# Basic version
python3 神经元网络/neuron_simulator.py

# Spatial interference version
python3 神经元网络/neuron_simulator_v2.py

# Chat system prototype
python3 神经元网络/neuron_chat.py
```

### Run Digital Worm Experiment

```bash
cd 伪_数字蠕虫/2_3
python3 00.py
```

## Project Structure

```
ling/
├── 神经元网络/                 # Core Neural Network Module
│   ├── neuron_simulator.py     # v1 Basic Version
│   ├── neuron_simulator_v2.py  # v2 Spatial Interference
│   ├── neuron_chat.py          # Chat System Prototype
│   ├── 图神经网络.py           # Graph Neural Network
│   ├── 图神经网络v2.py         # Improved GNN
│   └── 复数神经网络.py         # Complex Neural Network
├── 智能体构架/                  # Agent Architecture Experiments
│   ├── 内置版单神经元.py
│   ├── 标准化版单神经元.py
│   └── 模块化单神经元.py
├── 伪_数字蠕虫/                 # Digital Worm Experiment (Proof of Concept)
│   ├── 1_0/                    # Version 1.0
│   ├── 2_0/                    # Version 2.0
│   └── 2_3/                    # Current Version (with DNA Evolution)
├── images/                     # Project Images
├── .github/                    # GitHub Configuration
│   └── workflows/              # CI/CD Workflows
├── README.md                   # Documentation (Chinese)
├── README_en.md                # Documentation (English)
└── requirements.txt            # Dependencies
```

## Core Modules

### 🧠 Neural Network Simulator

`./神经元网络/` - Pure Python neural network models

**Core Features:**
- Neuron model: binary state, polarity, dynamic threshold, counter mechanism
- Network functions: sparse connection matrix, parallel computation, global time step
- Structural evolution: weight adjustment, connection pruning, new connection generation
- 3D spatial distribution + neighborhood interference mechanism

**Files:**
| File | Version | Description |
|------|---------|-------------|
| `neuron_simulator.py` | v1 | Basic neuron simulator |
| `neuron_simulator_v2.py` | v2 | Spatial interference version |
| `neuron_chat.py` | v3 | Chat system prototype |
| `图神经网络.py` | - | Basic GNN implementation |
| `图神经网络v2.py` | v2 | Improved GNN |
| `复数神经网络.py` | - | Complex-valued neural network |

### 🐛 Digital Worm Experiment

`./伪_数字蠕虫/` - Digital life simulation experiment

**Version Evolution:**
- **1.0**: Basic neural network control
- **2.0**: Modular architecture, snapshot system
- **2.3**: DNA evolution mechanism, optimized parameters

### 🤖 Agent Architecture

`./智能体构架/` - Agent architecture experiments

## Development Guide

### Requirements

- Python >= 3.10
- No external dependencies

### Code Style

Follow PEP 8, supports Chinese variable and function names.

## Related Projects

- [FSG-language](https://github.com/hctj353056/FSG-language) - FSG Logic Programming Language

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v2.3 | - | Added DNA evolution mechanism |
| v2.0 | - | Modular architecture refactoring |
| v1.0 | - | Initial version |

## Author

FuYou ♡

## License

MIT License

---

*FuShangGe · ling Project*
