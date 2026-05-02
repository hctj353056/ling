"""
ling demo - 一键运行，展示神经元网络模拟

运行方法：
    python demo.py
"""

import sys
import os
from neuron_simulator import NeuronSimulator


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '神经元网络'))



if __name__ == "__main__":
    print("=" * 60)
    print("ling 神经元网络模拟器 Demo")
    print("=" * 60)
    print()
    print("创建一个 10 神经元 × 4 连接密度的神经网络...")
    print("  输入神经元: [0, 1], 输出神经元: [8, 9]")
    print()

    sim = NeuronSimulator(
        n_neurons=10,
        connectivity=4,
        input_ids=[0, 1],
        output_ids=[8, 9],
        seed=42
    )

    print()
    print("运行 5 个周期 (交替给输入0和1发信号):")
    for cycle in range(5):
        if cycle % 2 == 0:
            result = sim.step({0: 2.0})
        else:
            result = sim.step({1: 2.0})
        out_states = sim.get_output_states()
        active = [n.id for n in sim.neurons if n.state == 1]
        print(f"  周期 {cycle + 1}: 输出={out_states}, 活跃=[{', '.join(map(str, active))}]")

    print()
    print("=" * 60)
    print("Demo 完成！更多示例见 神经元网络/ 和 伪_数字蠕虫/ 目录")
    print("=" * 60)
