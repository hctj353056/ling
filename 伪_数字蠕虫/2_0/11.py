import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 自动定位脚本所在目录

import matplotlib
matplotlib.use('Agg')        # 无头后端，只保存图片，不显示窗口
import matplotlib.pyplot as plt
import numpy as np
import json

def load_snapshot(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_connectivity_evolution(snapshot_dir='snapshots'):
    ticks, conns = [], []
    files = sorted([f for f in os.listdir(snapshot_dir) if f.startswith("snapshot_") and f.endswith(".json")])
    for f in files:
        data = load_snapshot(os.path.join(snapshot_dir, f))
        ticks.append(data['tick'])
        total_conn = sum(len(edges) for edges in data['network']['adjacency'].values())
        conns.append(total_conn)
    
    plt.figure(figsize=(10, 4))
    plt.plot(ticks, conns, 'b-o')
    plt.xlabel('Tick')
    plt.ylabel('Total Connections')
    plt.title('Network Connectivity Evolution')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('connectivity.png', dpi=150)
    print(f"已保存 connectivity.png")

def plot_adjacency_heatmap(snapshot_path, node_count=20):
    data = load_snapshot(snapshot_path)
    adj = data['network']['adjacency']
    matrix = np.zeros((node_count, node_count))
    for src, edges in adj.items():
        s = int(src)
        for e in edges:
            w = e['weight']
            matrix[s, e['target']] = np.sqrt(w[0]**2 + w[1]**2)
    
    plt.figure(figsize=(8, 6))
    plt.imshow(matrix, cmap='hot', interpolation='nearest')
    plt.colorbar(label='Weight Magnitude')
    plt.title(f"Adjacency Matrix at tick {data['tick']}")
    plt.xlabel('Target Node')
    plt.ylabel('Source Node')
    plt.tight_layout()
    plt.savefig(f'adjacency_tick_{data["tick"]:06d}.png', dpi=150)
    print(f"已保存 adjacency_tick_{data['tick']:06d}.png")

# 运行
plot_connectivity_evolution('snapshots')
plot_adjacency_heatmap('snapshots/latest.json')