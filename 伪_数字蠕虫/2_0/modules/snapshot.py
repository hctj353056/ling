#!/usr/bin/env python3
"""
网络快照模块 - Network Snapshot
保存复数神经网络的状态以便后续分析和可视化
"""

import json
import os
import math
from typing import Dict, List, Any


def serialize_complex(z: complex) -> List[float]:
    """将复数序列化为 [real, imag]"""
    return [z.real, z.imag]


def serialize_network(network) -> Dict[str, Any]:
    """
    序列化游戏AI网络为字典
    network: 游戏AI网络 实例
    """
    core = network.核心
    
    # 邻接表
    adjacency = {}
    for src, edges in core.邻接.items():
        adjacency[str(src)] = [
            {"target": tgt, "weight": serialize_complex(w)}
            for tgt, w in edges
        ]
    
    # 节点状态
    nodes = []
    for i in range(core.节点数):
        nodes.append({
            "id": i,
            "state": serialize_complex(core.状态[i]),
            "threshold": core.阈值[i],
            "active_history": core.激活历史[i],
        })
    
    # 输出序列
    output_sequence = network.输出序列[-100:] if network.输出序列 else []  # 只保留最近100个命令
    
    return {
        "node_count": core.节点数,
        "iteration": core.迭代次数,
        "adjacency": adjacency,
        "nodes": nodes,
        "output_sequence": output_sequence,
        "cache_length": len(network.输入缓存),
        "command_set": network.命令集,
    }


def save_snapshot(brainstem, tick: int, food_eaten: int, energy: float,
                  snapshot_dir: str = "snapshots"):
    """
    保存一个网络快照
    
    Args:
        brainstem: Brainstem 实例
        tick: 当前步数
        food_eaten: 累计食物数
        energy: 当前能量
        snapshot_dir: 保存目录
    """
    os.makedirs(snapshot_dir, exist_ok=True)
    
    network_data = serialize_network(brainstem.network)
    snapshot = {
        "tick": tick,
        "food_eaten": food_eaten,
        "energy": energy,
        "network": network_data,
        "action_names": brainstem.action_names,
    }
    
    # 保存带 tick 的文件
    filename = os.path.join(snapshot_dir, f"snapshot_{tick:06d}.json")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    # 同时更新 latest.json
    latest_path = os.path.join(snapshot_dir, "latest.json")
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    return filename