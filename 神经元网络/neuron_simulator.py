#!/usr/bin/env python3
"""
简化的神经元网络模拟器
基于二值状态、极性和阈值机制的实验性神经网络

模型说明：
- 神经元状态：二值（0或1）
- 极性：+1（兴奋性）或-1（抑制性）
- 动态阈值：kb = (k + 1/N) × ka
- 结构可演化：权重微调、连接修剪与生成
"""

import random
from typing import List, Dict, Tuple, Optional
import time


class Neuron:
    """神经元类"""
    
    def __init__(self, nid: int, polarity: int = 1, is_input: bool = False, is_output: bool = False):
        self.id = nid                      # 神经元ID
        self.state = 0                      # 当前状态 (0或1)
        self.polarity = polarity            # 极性: +1兴奋性, -1抑制性
        self.k = 0.5                        # 阈值系数初始值
        self.ka = 1                         # 计数器初始值
        self.is_input = is_input            # 是否为输入神经元
        self.is_output = is_output          # 是否为输出神经元
        self.output_history = []            # 输出历史记录
        
    @property
    def kb(self) -> float:
        """计算动态阈值: kb = (k + 1/N) × ka"""
        return (self.k + 1.0 / NeuronSimulator.N) * self.ka
    
    def activate(self):
        """激活神经元：输出1，计数器+1"""
        self.state = 1
        self.ka = min(self.ka + 1, 20)      # 限制最大值防止溢出
        self.output_history.append(1)
        
    def deactivate(self):
        """抑制神经元：输出0"""
        self.state = 0
        self.output_history.append(0)
        
    def check_no_activation(self):
        """检查连续未激活：计数器-1"""
        self.ka = max(self.ka - 1, 1)       # 限制最小值为1
        
    def __repr__(self):
        polarity_str = "+" if self.polarity > 0 else "-"
        type_str = ""
        if self.is_input:
            type_str = "[IN]"
        elif self.is_output:
            type_str = "[OUT]"
        return f"N{self.id}({polarity_str},kb={self.kb:.2f},s={self.state}){type_str}"


class Synapse:
    """突触连接类"""
    
    def __init__(self, from_id: int, to_id: int, weight: float):
        self.from_id = from_id              # 源神经元ID
        self.to_id = to_id                  # 目标神经元ID
        self.weight = weight                # 连接权重 [0, 1]
        self.inactive_count = 0             # 连续未激活计数
        
    def strengthen(self):
        """强化连接：权重增加"""
        self.weight = min(self.weight + 0.01, 1.0)
        self.inactive_count = 0
        
    def weaken(self):
        """弱化连接：权重减少"""
        self.weight = max(self.weight - 0.005, 0.0)
        self.inactive_count += 1
        
    def is_pruned(self) -> bool:
        """检查是否应该被修剪：权重<0.05且连续10次未激活"""
        return self.weight < 0.05 and self.inactive_count >= 10
    
    def __repr__(self):
        return f"{self.from_id}->{self.to_id}(w={self.weight:.3f})"


class NeuronSimulator:
    """神经元网络模拟器"""
    
    N = 10  # 神经元总数，将在初始化时设置
    
    def __init__(self, n_neurons: int = 10, connectivity: int = 4, 
                 input_ids: List[int] = None, output_ids: List[int] = None,
                 seed: int = None):
        """
        初始化模拟器
        
        Args:
            n_neurons: 神经元总数
            connectivity: 每个神经元的平均下游连接数
            input_ids: 输入神经元ID列表
            output_ids: 输出神经元ID列表
            seed: 随机种子（用于可重复实验）
        """
        if seed is not None:
            random.seed(seed)
            
        NeuronSimulator.N = n_neurons
        self.n_neurons = n_neurons
        self.tick = 0
        self.neurons: List[Neuron] = []
        self.synapses: List[Synapse] = []
        
        # 初始化神经元
        self._init_neurons(input_ids or [], output_ids or [])
        
        # 初始化连接矩阵
        self._init_synapses(connectivity)
        
        # 统计信息
        self.activation_history = []
        
    def _init_neurons(self, input_ids: List[int], output_ids: List[int]):
        """初始化神经元"""
        for i in range(self.n_neurons):
            # 随机分配极性，80%兴奋性，20%抑制性
            polarity = 1 if random.random() < 0.8 else -1
            
            is_input = i in input_ids
            is_output = i in output_ids
            
            self.neurons.append(Neuron(
                nid=i,
                polarity=polarity,
                is_input=is_input,
                is_output=is_output
            ))
            
    def _init_synapses(self, avg_connections: int):
        """初始化稀疏连接矩阵"""
        for i in range(self.n_neurons):
            # 计算下游连接数（稀疏：平均3-5个）
            n_downstream = max(1, min(avg_connections + random.randint(-1, 1), self.n_neurons - 1))
            
            # 随机选择下游神经元
            downstream_ids = random.sample(
                [j for j in range(self.n_neurons) if j != i],
                n_downstream
            )
            
            for j in downstream_ids:
                # 避免重复连接
                if not self._synapse_exists(i, j):
                    # 随机权重 [0.3, 0.8]
                    weight = random.uniform(0.3, 0.8)
                    self.synapses.append(Synapse(i, j, weight))
                    
    def _synapse_exists(self, from_id: int, to_id: int) -> bool:
        """检查连接是否已存在"""
        return any(s.from_id == from_id and s.to_id == to_id for s in self.synapses)
    
    def _get_upstream_synapses(self, neuron_id: int) -> List[Tuple[Synapse, Neuron]]:
        """获取所有上游突触及其源神经元"""
        result = []
        for syn in self.synapses:
            if syn.to_id == neuron_id:
                result.append((syn, self.neurons[syn.from_id]))
        return result
    
    def _get_downstream_synapses(self, neuron_id: int) -> List[Synapse]:
        """获取所有下游突触"""
        return [s for s in self.synapses if s.from_id == neuron_id]
    
    def apply_input(self, input_signals: Dict[int, float]):
        """
        应用外部输入信号
        
        Args:
            input_signals: {神经元ID: 信号强度}
        """
        for nid, signal in input_signals.items():
            if 0 <= nid < self.n_neurons:
                # 输入信号直接累加到b值（需要单独处理）
                self.neurons[nid]._external_signal = signal
                
    def step(self, external_inputs: Dict[int, float] = None) -> Dict[str, any]:
        """
        执行一个时间步
        
        Args:
            external_inputs: 外部输入信号
            
        Returns:
            步执行结果统计
        """
        self.tick += 1
        external_inputs = external_inputs or {}
        
        # Phase 1: 计算每个神经元的输入总和
        neuron_inputs = {}
        for nid, neuron in enumerate(self.neurons):
            # 初始化（包括外部输入）
            neuron_inputs[nid] = external_inputs.get(nid, 0)
            
            # 累加上游信号
            # b = Σ(上游输出 × 上游极性 × 权重 × A)
            for syn, upstream_neuron in self._get_upstream_synapses(nid):
                signal = upstream_neuron.state * upstream_neuron.polarity * syn.weight * 1.0
                neuron_inputs[nid] += signal
                
        # Phase 2: 并行更新所有神经元状态
        activations = []
        for nid, neuron in enumerate(self.neurons):
            b = neuron_inputs[nid]
            kb = neuron.kb  # 动态阈值
            
            if b > kb:
                neuron.activate()
                activations.append(nid)
            else:
                neuron.deactivate()
                
        # Phase 3: 更新突触权重（结构演化）
        self._evolve_structure(activations)
        
        # Phase 4: 记录历史
        self.activation_history.append({
            'tick': self.tick,
            'activations': activations.copy(),
            'total_active': len(activations)
        })
        
        return {
            'tick': self.tick,
            'activations': activations,
            'inputs': neuron_inputs
        }
    
    def _evolve_structure(self, activations: List[int]):
        """结构演化：权重微调、修剪、新生成"""
        
        # 遍历所有突触
        synapses_to_remove = []
        
        for syn in self.synapses:
            if syn.from_id in activations:
                # 激活的连接：强化
                syn.strengthen()
            else:
                # 未激活的连接：弱化
                syn.weaken()
                
            # 检查是否应该修剪
            if syn.is_pruned():
                synapses_to_remove.append(syn)
                
        # 移除被修剪的连接
        for syn in synapses_to_remove:
            self.synapses.remove(syn)
            print(f"    [修剪] 移除弱连接: {syn}")
            
        # 新连接生成：每100tick随机添加弱连接
        if self.tick % 100 == 0 and len(self.synapses) < self.n_neurons * 5:
            # 随机选择源和目标
            from_id = random.randint(0, self.n_neurons - 1)
            to_id = random.randint(0, self.n_neurons - 1)
            
            if from_id != to_id and not self._synapse_exists(from_id, to_id):
                new_syn = Synapse(from_id, to_id, weight=0.1)
                self.synapses.append(new_syn)
                print(f"    [新生] 添加新连接: {new_syn}")
                
    def get_network_state(self) -> str:
        """获取当前网络状态的可读描述"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"时间步 #{self.tick}")
        lines.append(f"{'='*60}")
        
        # 显示神经元状态
        lines.append("\n[神经元状态]")
        for i, n in enumerate(self.neurons):
            state_str = "■" if n.state == 1 else "□"
            polarity_str = "+" if n.polarity > 0 else "-"
            type_str = " [输入]" if n.is_input else (" [输出]" if n.is_output else "")
            lines.append(f"  {state_str} N{i:2d}: 极性={polarity_str}, 阈值kb={n.kb:5.2f}, 计数器ka={n.ka:2d}{type_str}")
            
        # 显示活跃的输入总和
        lines.append("\n[输入汇总]")
        for nid, neuron in enumerate(self.neurons):
            if neuron.is_input:
                upstream = self._get_upstream_synapses(nid)
                b = sum(n.state * n.polarity * s.weight for s, n in upstream)
                lines.append(f"  N{nid}: b={b:.3f} > kb={neuron.kb:.3f}? {b > neuron.kb}")
                
        # 显示输出神经元状态
        lines.append("\n[输出神经元]")
        for neuron in self.neurons:
            if neuron.is_output:
                state_str = "激活" if neuron.state == 1 else "抑制"
                lines.append(f"  N{neuron.id}: {state_str}")
                
        # 显示连接统计
        lines.append(f"\n[连接统计] 总连接数: {len(self.synapses)}")
        
        # 显示活跃的连接
        active_synapses = [s for s in self.synapses if self.neurons[s.from_id].state == 1]
        if active_synapses:
            lines.append(f"  活跃连接: {', '.join(str(s) for s in active_synapses[:5])}" + 
                        (" ..." if len(active_synapses) > 5 else ""))
        
        return "\n".join(lines)
    
    def run_simulation(self, n_steps: int, input_patterns: List[Dict[int, float]] = None, 
                       pause: float = 0.1):
        """
        运行模拟
        
        Args:
            n_steps: 模拟步数
            input_patterns: 输入模式列表，循环使用
            pause: 每步暂停时间（秒）
        """
        print("\n" + "="*60)
        print("神经元网络模拟器启动")
        print("="*60)
        print(f"神经元数量: {self.n_neurons}")
        print(f"初始连接数: {len(self.synapses)}")
        print(f"输入神经元: {[n.id for n in self.neurons if n.is_input]}")
        print(f"输出神经元: {[n.id for n in self.neurons if n.is_output]}")
        print(f"模拟步数: {n_steps}")
        print("="*60)
        
        input_patterns = input_patterns or [{}]
        
        for step in range(n_steps):
            # 选择输入模式
            input_pattern = input_patterns[step % len(input_patterns)]
            
            # 执行一步
            result = self.step(input_pattern)
            
            # 显示状态
            print(self.get_network_state())
            
            # 显示激活的神经元
            if result['activations']:
                print(f"\n  ★ 激活神经元: {result['activations']}")
            
            # 暂停以便观察
            if pause > 0:
                time.sleep(pause)
                
        # 最终统计
        self._print_summary()
        
    def _print_summary(self):
        """打印模拟总结"""
        print("\n" + "="*60)
        print("模拟结束 - 统计总结")
        print("="*60)
        
        # 连接变化
        print(f"\n[连接变化]")
        print(f"  初始连接数: ~{self.n_neurons * 4}")
        print(f"  最终连接数: {len(self.synapses)}")
        
        # 神经元激活统计
        print(f"\n[神经元激活统计]")
        for neuron in self.neurons:
            active_count = sum(neuron.output_history)
            total = len(neuron.output_history)
            rate = active_count / total if total > 0 else 0
            print(f"  N{neuron.id}: {active_count}/{total} ({rate*100:.1f}%)")
            
        # 输出模式
        print(f"\n[输出模式序列]")
        output_patterns = []
        for neuron in self.neurons:
            if neuron.is_output:
                pattern = ''.join(str(s) for s in neuron.output_history[-20:])
                output_patterns.append(f"N{neuron.id}: {pattern}")
        for p in output_patterns:
            print(f"  {p}")
            
    def get_output_states(self) -> List[int]:
        """获取所有输出神经元的当前状态"""
        return [n.state for n in self.neurons if n.is_output]
        
    def get_connection_matrix(self) -> List[List[float]]:
        """获取连接权重矩阵"""
        matrix = [[0.0] * self.n_neurons for _ in range(self.n_neurons)]
        for syn in self.synapses:
            matrix[syn.from_id][syn.to_id] = syn.weight
        return matrix


def demo_basic():
    """基础演示：简单的网络运行"""
    print("\n" + "▶"*20 + " 基础演示 " + "◀"*20 + "\n")
    
    # 创建网络：10个神经元，0和1为输入，8和9为输出
    sim = NeuronSimulator(
        n_neurons=10,
        connectivity=4,
        input_ids=[0, 1],
        output_ids=[8, 9],
        seed=42
    )
    
    # 运行模拟：20步，循环两种输入模式
    # 模式1：激活输入0
    # 模式2：激活输入1
    input_patterns = [
        {0: 2.0},   # 模式1：给输入0强信号
        {1: 2.0},   # 模式2：给输入1强信号
    ]
    
    sim.run_simulation(n_steps=20, input_patterns=input_patterns, pause=0)


def demo_learning():
    """学习演示：观察网络如何学会对特定输入产生特定输出"""
    print("\n" + "▶"*20 + " 学习演示 " + "◀"*20 + "\n")
    
    # 创建稍大的网络
    sim = NeuronSimulator(
        n_neurons=15,
        connectivity=3,
        input_ids=[0, 1],
        output_ids=[13, 14],
        seed=123
    )
    
    # 训练模式：希望网络学会
    # 输入[0]激活 → 输出[13]激活
    # 输入[1]激活 → 输出[14]激活
    
    input_patterns = [
        {0: 3.0, 1: 0.0},  # 输入模式A
        {0: 0.0, 1: 3.0},  # 输入模式B
    ]
    
    print("开始学习训练 (200步)...\n")
    sim.run_simulation(n_steps=200, input_patterns=input_patterns, pause=0)
    
    # 观察学习效果
    print("\n" + "▶"*20 + " 学习后测试 " + "◀"*20 + "\n")
    
    # 测试模式A
    print("测试输入模式A (输入0激活):")
    result_a = sim.step({0: 3.0, 1: 0.0})
    print(f"  输出状态: {sim.get_output_states()}")
    
    # 测试模式B
    print("\n测试输入模式B (输入1激活):")
    result_b = sim.step({0: 0.0, 1: 3.0})
    print(f"  输出状态: {sim.get_output_states()}")


def demo_evolution():
    """演化演示：观察网络的结构变化"""
    print("\n" + "▶"*20 + " 结构演化演示 " + "◀"*20 + "\n")
    
    sim = NeuronSimulator(
        n_neurons=12,
        connectivity=5,
        input_ids=[0],
        output_ids=[10, 11],
        seed=999
    )
    
    print(f"初始状态: {len(sim.synapses)} 个连接")
    
    # 快速演化观察
    input_patterns = [{0: 2.5}]
    
    print("\n观察前50步的结构变化...\n")
    sim.run_simulation(n_steps=50, input_patterns=input_patterns, pause=0)
    
    print(f"\n最终状态: {len(sim.synapses)} 个连接")
    
    # 显示连接矩阵
    print("\n[最终连接矩阵] (权重 > 0.1)")
    matrix = sim.get_connection_matrix()
    for i, row in enumerate(matrix):
        connections = [f"N{j}:{w:.2f}" for j, w in enumerate(row) if w > 0.1]
        if connections:
            print(f"  N{i}: {', '.join(connections)}")


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("  神经元网络模拟器 v1.0")
    print("  基于二值状态、极性和动态阈值的实验性神经网络")
    print("█"*60)
    
    # 运行所有演示
    demo_basic()
    
    # 取消注释以下行运行更多演示
    # demo_learning()
    # demo_evolution()
    
    print("\n" + "="*60)
    print("所有演示完成！")
    print("="*60)
