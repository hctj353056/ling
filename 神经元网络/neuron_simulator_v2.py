#!/usr/bin/env python3
"""
神经元网络模拟器 v2.0
基于二值状态、极性和阈值机制的实验性神经网络

v2.0 新增功能：
- 文字输入与UTF-8编码映射
- 神经元三维空间分布
- 空间干涉机制（噪声/从众效应）
- 改进的激活计算

模型说明：
- 神经元状态：二值（0或1）
- 极性：+1（兴奋性）或-1（抑制性）
- 动态阈值：kb = (k + 1/N) × ka
- 空间干涉：邻居激活比例影响自身阈值
"""

import random
import math
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import time


class Neuron:
    """神经元类 - 包含三维坐标属性"""
    
    def __init__(self, nid: int, polarity: int = 1, is_input: bool = False, 
                 is_output: bool = False, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.id = nid                      # 神经元ID
        self.state = 0                      # 当前状态 (0或1)
        self.polarity = polarity            # 极性: +1兴奋性, -1抑制性
        self.k = 0.5                        # 阈值系数初始值
        self.ka = 1                         # 计数器初始值
        self.is_input = is_input            # 是否为输入神经元
        self.is_output = is_output          # 是否为输出神经元
        self.output_history = []            # 输出历史记录
        
        # ========== v2.0新增：三维坐标 ==========
        self.x = x                          # x坐标
        self.y = y                          # y坐标
        self.z = z                          # z坐标
        
        # ========== v2.0新增：空间干涉相关 ==========
        self.interference_signal = 0.0      # 干涉信号（正值=激活效应，负值=抑制效应）
        self.neighbor_activation_ratio = 0.0  # 邻居激活比例
        self.affected_by_herding = False    # 是否受到从众效应影响
        self.herding_type = None            # 从众类型: "inhibited"(被抑制) / "activated"(被激活)
        
    @property
    def kb(self) -> float:
        """计算动态阈值: kb = (k + 1/N) × ka
        v2.0: 阈值会受到空间干涉信号的影响"""
        base_kb = (self.k + 1.0 / NeuronSimulator.N) * self.ka
        # 干涉信号会影响阈值：正信号降低阈值（更容易激活），负信号提高阈值（更难激活）
        return base_kb - self.interference_signal
    
    def distance_to(self, other: 'Neuron') -> float:
        """计算到另一个神经元的欧几里得距离"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def activate(self):
        """激活神经元：输出1，计数器+1"""
        self.state = 1
        self.ka = min(self.ka + 1, 20)
        self.output_history.append(1)
        
    def deactivate(self):
        """抑制神经元：输出0"""
        self.state = 0
        self.output_history.append(0)
        
    def check_no_activation(self):
        """检查连续未激活：计数器-1"""
        self.ka = max(self.ka - 1, 1)
        
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
    """神经元网络模拟器 v2.0"""
    
    N = 10  # 神经元总数，将在初始化时设置
    
    def __init__(self, n_neurons: int = 10, connectivity: int = 4, 
                 input_ids: List[int] = None, output_ids: List[int] = None,
                 seed: int = None,
                 neighborhood_radius: float = 5.0,
                 interference_strength: float = 0.5,
                 spatial_layout: str = "random"):
        """
        初始化模拟器 v2.0
        
        Args:
            n_neurons: 神经元总数
            connectivity: 每个神经元的平均下游连接数
            input_ids: 输入神经元ID列表
            output_ids: 输出神经元ID列表
            seed: 随机种子
            neighborhood_radius: 邻域半径R（空间干涉范围）
            interference_strength: 干涉强度系数
            spatial_layout: 空间布局模式: "random"(随机) / "grid"(网格) / "sphere"(球面)
        """
        if seed is not None:
            random.seed(seed)
            
        NeuronSimulator.N = n_neurons
        self.n_neurons = n_neurons
        self.tick = 0
        self.neurons: List[Neuron] = []
        self.synapses: List[Synapse] = []
        
        # ========== v2.0新增：空间干涉参数 ==========
        self.neighborhood_radius = neighborhood_radius  # 邻域半径
        self.interference_strength = interference_strength  # 干涉强度
        self.spatial_layout = spatial_layout
        
        # 初始化神经元（带三维坐标）
        self._init_neurons(input_ids or [], output_ids or [])
        
        # 初始化连接矩阵
        self._init_synapses(connectivity)
        
        # 统计信息
        self.activation_history = []
        self.herding_events = []  # 记录从众效应事件
        
    def _init_neurons(self, input_ids: List[int], output_ids: List[int]):
        """初始化神经元 - v2.0添加三维坐标"""
        coordinates = self._generate_spatial_coordinates()
        
        for i in range(self.n_neurons):
            # 随机分配极性，80%兴奋性，20%抑制性
            polarity = 1 if random.random() < 0.8 else -1
            
            is_input = i in input_ids
            is_output = i in output_ids
            
            x, y, z = coordinates[i]
            
            self.neurons.append(Neuron(
                nid=i,
                polarity=polarity,
                is_input=is_input,
                is_output=is_output,
                x=x, y=y, z=z
            ))
            
    def _generate_spatial_coordinates(self) -> List[Tuple[float, float, float]]:
        """
        生成神经元的三维空间坐标
        v2.0新增功能
        """
        coords = []
        
        if self.spatial_layout == "random":
            # 随机分布：在一个立方体内随机放置
            for _ in range(self.n_neurons):
                x = random.uniform(-10, 10)
                y = random.uniform(-10, 10)
                z = random.uniform(-10, 10)
                coords.append((x, y, z))
                
        elif self.spatial_layout == "grid":
            # 网格排列：尽量均匀分布
            dim = int(math.ceil(self.n_neurons ** (1/3)))
            for i in range(self.n_neurons):
                xi = i % dim
                yi = (i // dim) % dim
                zi = i // (dim * dim)
                x = (xi - dim/2) * 3.0
                y = (yi - dim/2) * 3.0
                z = (zi - dim/2) * 3.0
                coords.append((x, y, z))
                
        elif self.spatial_layout == "sphere":
            # 球面分布：神经元分布在一个球体表面或内部
            for i in range(self.n_neurons):
                # 使用球坐标系转换
                theta = random.uniform(0, 2 * math.pi)  # 方位角
                phi = random.uniform(0, math.pi)         # 极角
                r = random.uniform(5, 10)                # 半径
                x = r * math.sin(phi) * math.cos(theta)
                y = r * math.sin(phi) * math.sin(theta)
                z = r * math.cos(phi)
                coords.append((x, y, z))
        else:
            # 默认随机
            for _ in range(self.n_neurons):
                coords.append((random.uniform(-10, 10), 
                              random.uniform(-10, 10), 
                              random.uniform(-10, 10)))
                              
        return coords
        
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
    
    # ========== v2.0新增：文字输入编码功能 ==========
    def encode_text(self, text: str) -> Dict[int, float]:
        """
        将文字字符串编码为神经元激活信号
        
        算法：
        1. 将字符串按UTF-8编码为字节
        2. 每个字节值映射到对应的输入神经元
        3. 如果输入神经元数量不足，循环复用
        
        Args:
            text: 输入字符串
            
        Returns:
            {神经元ID: 激活强度} 的字典
        """
        # 获取UTF-8编码的字节
        utf8_bytes = text.encode('utf-8')
        
        # 获取输入神经元ID列表
        input_neurons = [n.id for n in self.neurons if n.is_input]
        
        if not input_neurons:
            print("警告：没有输入神经元，无法编码文字")
            return {}
            
        signals = {}
        
        # 将每个字节映射到输入神经元
        for i, byte_val in enumerate(utf8_bytes):
            neuron_id = input_neurons[i % len(input_neurons)]
            # 字节值范围0-255，映射到激活强度
            # 归一化到0-3范围
            signal = (byte_val / 255.0) * 3.0
            signals[neuron_id] = signals.get(neuron_id, 0) + signal
            
        return signals
    
    def encode_char(self, char: str) -> Dict[int, float]:
        """
        将单个字符编码为神经元激活信号
        
        Args:
            char: 单个字符
            
        Returns:
            {神经元ID: 激活强度}
        """
        return self.encode_text(char)
    
    def get_neighbors(self, neuron_id: int) -> List[int]:
        """
        获取指定神经元邻域内的所有神经元ID
        
        Args:
            neuron_id: 神经元ID
            
        Returns:
            邻域内神经元ID列表（不包含自己）
        """
        neuron = self.neurons[neuron_id]
        neighbors = []
        
        for other in self.neurons:
            if other.id != neuron_id:
                distance = neuron.distance_to(other)
                if distance <= self.neighborhood_radius:
                    neighbors.append(other.id)
                    
        return neighbors
    
    def _calculate_interference(self) -> Dict[int, float]:
        """
        计算空间干涉信号（从众效应）
        v2.0新增核心功能
        
        干涉规则：
        - 邻居激活比例 > 50% → 抑制自己（增加阈值 kb）
        - 邻居激活比例 ≤ 50% → 激活自己（降低阈值 kb）
        
        Returns:
            {神经元ID: 干涉信号值}
        """
        interference_signals = {}
        
        for neuron in self.neurons:
            neighbor_ids = self.get_neighbors(neuron.id)
            
            if not neighbor_ids:
                # 没有邻居，不受干涉
                interference_signals[neuron.id] = 0.0
                neuron.neighbor_activation_ratio = 0.0
                continue
            
            # 计算邻居的激活比例
            active_neighbors = sum(1 for nid in neighbor_ids if self.neurons[nid].state == 1)
            activation_ratio = active_neighbors / len(neighbor_ids)
            neuron.neighbor_activation_ratio = activation_ratio
            
            # 根据激活比例计算干涉信号
            # 正值表示邻居多数激活（会抑制自己），负值表示邻居多数抑制（会激活自己）
            if activation_ratio > 0.5:
                # 邻居多数激活 → 从众效应：抑制自己（正信号增加阈值）
                interference = self.interference_strength * (activation_ratio - 0.5) * 2
            else:
                # 邻居多数抑制 → 从众效应：激活自己（负信号降低阈值）
                interference = -self.interference_strength * (0.5 - activation_ratio) * 2
                
            interference_signals[neuron.id] = interference
            
        return interference_signals
    
    def apply_input(self, input_signals: Dict[int, float]):
        """
        应用外部输入信号
        
        Args:
            input_signals: {神经元ID: 信号强度}
        """
        for nid, signal in input_signals.items():
            if 0 <= nid < self.n_neurons:
                self.neurons[nid]._external_signal = signal
                
    def step(self, external_inputs: Dict[int, float] = None, 
             enable_interference: bool = True) -> Dict[str, any]:
        """
        执行一个时间步 - v2.0改进版
        
        Args:
            external_inputs: 外部输入信号
            enable_interference: 是否启用空间干涉
            
        Returns:
            步执行结果统计
        """
        self.tick += 1
        external_inputs = external_inputs or {}
        
        # ========== Phase 0: 计算空间干涉信号 ==========
        if enable_interference:
            interference_signals = self._calculate_interference()
            herding_this_tick = []
            
            for neuron in self.neurons:
                neuron.interference_signal = interference_signals.get(neuron.id, 0.0)
                
                # 记录从众效应
                if neuron.affected_by_herding:
                    herding_this_tick.append({
                        'neuron_id': neuron.id,
                        'type': neuron.herding_type,
                        'neighbor_ratio': neuron.neighbor_activation_ratio
                    })
        
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
                
        # Phase 2: 并行更新所有神经元状态（加入干涉信号）
        activations = []
        inhibited_by_herding = []   # 被从众效应抑制的
        activated_by_herding = []  # 被从众效应激活的
        
        for nid, neuron in enumerate(self.neurons):
            b = neuron_inputs[nid]
            kb = neuron.kb  # 动态阈值（现在包含干涉影响）
            
            # ========== v2.0改进：b + 干涉信号 > kb ==========
            # 干涉信号在阈值计算时已经体现
            # 实际上现在是: b > kb(interference) 即 b > (base_kb - interference_signal)
            # 等价于: b + interference_signal > base_kb
            
            # 记录干涉前的激活判断
            would_activate = b > (neuron.k + 1.0/self.N) * neuron.ka  # 无干涉时的判断
            
            if b > kb:
                neuron.activate()
                activations.append(nid)
                
                # 检查是否因为从众效应而激活
                if enable_interference and not would_activate and neuron.interference_signal < 0:
                    activated_by_herding.append(nid)
                    neuron.affected_by_herding = True
                    neuron.herding_type = "activated"
            else:
                neuron.deactivate()
                
                # 检查是否因为从众效应而被抑制
                if enable_interference and would_activate and neuron.interference_signal > 0:
                    inhibited_by_herding.append(nid)
                    neuron.affected_by_herding = True
                    neuron.herding_type = "inhibited"
                else:
                    neuron.affected_by_herding = False
                    neuron.herding_type = None
                    
        # Phase 3: 更新突触权重（结构演化）
        self._evolve_structure(activations)
        
        # Phase 4: 记录历史
        herding_record = {
            'tick': self.tick,
            'inhibited': inhibited_by_herding,
            'activated': activated_by_herding,
            'total_affected': len(inhibited_by_herding) + len(activated_by_herding)
        }
        self.herding_events.append(herding_record)
        
        self.activation_history.append({
            'tick': self.tick,
            'activations': activations.copy(),
            'total_active': len(activations)
        })
        
        return {
            'tick': self.tick,
            'activations': activations,
            'inputs': neuron_inputs,
            'interference': interference_signals if enable_interference else {},
            'herding': herding_record
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
            
        # 新连接生成：每100tick随机添加弱连接
        if self.tick % 100 == 0 and len(self.synapses) < self.n_neurons * 5:
            # 随机选择源和目标
            from_id = random.randint(0, self.n_neurons - 1)
            to_id = random.randint(0, self.n_neurons - 1)
            
            if from_id != to_id and not self._synapse_exists(from_id, to_id):
                new_syn = Synapse(from_id, to_id, weight=0.1)
                self.synapses.append(new_syn)
    
    def get_spatial_distribution(self) -> str:
        """
        获取神经元的三维空间分布信息
        v2.0新增可视化
        """
        lines = []
        lines.append("\n" + "="*60)
        lines.append("神经元三维空间分布")
        lines.append("="*60)
        lines.append(f"空间布局模式: {self.spatial_layout}")
        lines.append(f"邻域半径R: {self.neighborhood_radius}")
        lines.append(f"干涉强度: {self.interference_strength}")
        lines.append("\n[神经元坐标]")
        
        # 按空间位置排序显示
        sorted_neurons = sorted(self.neurons, key=lambda n: (n.z, n.y, n.x))
        
        for neuron in sorted_neurons:
            state_str = "■" if neuron.state == 1 else "□"
            type_str = ""
            if neuron.is_input:
                type_str = " [输入]"
            elif neuron.is_output:
                type_str = " [输出]"
            lines.append(f"  {state_str} N{neuron.id:2d}: ({neuron.x:+6.2f}, {neuron.y:+6.2f}, {neuron.z:+6.2f})"
                        f" 邻居激活={neuron.neighbor_activation_ratio:.1%}{type_str}")
                        
        # 显示邻居关系统计
        lines.append("\n[邻域统计]")
        neighbor_counts = [len(self.get_neighbors(n.id)) for n in self.neurons]
        lines.append(f"  平均邻居数: {sum(neighbor_counts)/len(neighbor_counts):.1f}")
        lines.append(f"  最少邻居: {min(neighbor_counts)}")
        lines.append(f"  最多邻居: {max(neighbor_counts)}")
        
        return "\n".join(lines)
    
    def get_spatial_activation_pattern(self) -> str:
        """
        获取当前的空间激活模式
        v2.0新增可视化
        """
        lines = []
        lines.append("\n" + "-"*60)
        lines.append("空间激活模式")
        lines.append("-"*60)
        
        # 按z轴分层显示
        z_layers = defaultdict(list)
        for neuron in self.neurons:
            z_layers[round(neuron.z, 1)].append(neuron)
            
        for z in sorted(z_layers.keys()):
            layer = z_layers[z]
            lines.append(f"\n  [Z={z:+6.2f} 层] ({len(layer)}个神经元)")
            
            # 在二维平面上显示
            for neuron in sorted(layer, key=lambda n: (n.y, n.x)):
                state_char = "■" if neuron.state == 1 else "□"
                polarity_char = "+" if neuron.polarity > 0 else "-"
                
                # 从众效应标记
                herding_mark = ""
                if neuron.affected_by_herding:
                    if neuron.herding_type == "inhibited":
                        herding_mark = " ↓抑制"
                    else:
                        herding_mark = " ↑激活"
                
                lines.append(f"    {state_char} N{neuron.id:2d}({polarity_char}) "
                           f"@({neuron.x:+5.1f},{neuron.y:+5.1f}){herding_mark}")
                           
        return "\n".join(lines)
    
    def get_herding_summary(self) -> str:
        """
        获取从众效应的统计摘要
        v2.0新增
        """
        if not self.herding_events:
            return "\n[从众效应统计] 暂无数据"
            
        lines = []
        lines.append("\n" + "="*60)
        lines.append("从众效应统计")
        lines.append("="*60)
        
        total_inhibited = sum(e['inhibited'] for e in self.herding_events)
        total_activated = sum(e['activated'] for e in self.herding_events)
        total_affected = sum(e['total_affected'] for e in self.herding_events)
        
        lines.append(f"  总从众事件: {total_affected}")
        lines.append(f"  被抑制事件: {total_inhibited}")
        lines.append(f"  被激活事件: {total_activated}")
        lines.append(f"  平均每步受影响: {total_affected/len(self.herding_events):.1f}个神经元")
        
        # 显示最近5步的详细记录
        lines.append("\n[最近5步从众记录]")
        for event in self.herding_events[-5:]:
            inhibited = event['inhibited']
            activated = event['activated']
            if inhibited or activated:
                lines.append(f"  T{event['tick']}: 抑制{len(inhibited)}个 {inhibited}, "
                           f"激活{len(activated)}个 {activated}")
            else:
                lines.append(f"  T{event['tick']}: 无从众效应")
                
        return "\n".join(lines)
    
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
            
            # v2.0新增：干涉信息
            interference_str = ""
            if n.interference_signal != 0:
                sign = "+" if n.interference_signal > 0 else ""
                interference_str = f" 干涉={sign}{n.interference_signal:.2f}"
            
            lines.append(f"  {state_str} N{i:2d}: 极性={polarity_str}, 阈值kb={n.kb:5.2f}, "
                        f"计数器ka={n.ka:2d}{type_str}{interference_str}")
            
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
                       pause: float = 0.1, enable_interference: bool = True,
                       show_spatial: bool = False):
        """
        运行模拟 - v2.0改进版
        
        Args:
            n_steps: 模拟步数
            input_patterns: 输入模式列表，循环使用
            pause: 每步暂停时间（秒）
            enable_interference: 是否启用空间干涉
            show_spatial: 是否显示空间分布信息
        """
        print("\n" + "="*60)
        print("神经元网络模拟器 v2.0 启动")
        print("="*60)
        print(f"神经元数量: {self.n_neurons}")
        print(f"初始连接数: {len(self.synapses)}")
        print(f"输入神经元: {[n.id for n in self.neurons if n.is_input]}")
        print(f"输出神经元: {[n.id for n in self.neurons if n.is_output]}")
        print(f"邻域半径R: {self.neighborhood_radius}")
        print(f"干涉强度: {self.interference_strength}")
        print(f"空间布局: {self.spatial_layout}")
        print(f"模拟步数: {n_steps}")
        print(f"空间干涉: {'启用' if enable_interference else '禁用'}")
        print("="*60)
        
        # 首次显示空间分布
        if show_spatial:
            print(self.get_spatial_distribution())
        
        input_patterns = input_patterns or [{}]
        
        for step in range(n_steps):
            # 选择输入模式
            input_pattern = input_patterns[step % len(input_patterns)]
            
            # 执行一步
            result = self.step(input_pattern, enable_interference)
            
            # 显示状态
            print(self.get_network_state())
            
            # 显示激活的神经元
            if result['activations']:
                print(f"\n  ★ 激活神经元: {result['activations']}")
            
            # 显示从众效应
            herding = result['herding']
            if herding['inhibited']:
                print(f"\n  ↓ 从众被抑制: {herding['inhibited']}")
            if herding['activated']:
                print(f"\n  ↑ 从众被激活: {herding['activated']}")
            
            # 显示空间激活模式
            if show_spatial:
                print(self.get_spatial_activation_pattern())
            
            # 暂停以便观察
            if pause > 0:
                time.sleep(pause)
                
        # 最终统计
        self._print_summary()
        
        # 显示从众效应统计
        if enable_interference:
            print(self.get_herding_summary())
    
    def run_text_input(self, text: str, n_steps: int = 10, 
                       enable_interference: bool = True,
                       show_spatial: bool = True):
        """
        运行文字输入模拟 - v2.0新增功能
        
        Args:
            text: 输入文字
            n_steps: 模拟步数
            enable_interference: 是否启用空间干涉
            show_spatial: 是否显示空间分布
        """
        print("\n" + "="*60)
        print("文字输入模拟")
        print("="*60)
        print(f"输入文字: \"{text}\"")
        
        # UTF-8编码分析
        utf8_bytes = text.encode('utf-8')
        print(f"UTF-8编码 ({len(utf8_bytes)}字节): {[b for b in utf8_bytes]}")
        
        # 编码为神经元信号
        signals = self.encode_text(text)
        print(f"神经元激活映射: {signals}")
        
        print("="*60)
        
        # 运行模拟
        input_patterns = [signals]
        
        for step in range(n_steps):
            # 每步逐渐衰减输入
            decay = 0.9 ** step
            decayed_signals = {k: v * decay for k, v in signals.items()}
            
            result = self.step(decayed_signals, enable_interference)
            
            print(f"\n{'='*60}")
            print(f"时间步 #{self.tick} (输入衰减={decay:.2%})")
            print("="*60)
            
            # 显示空间激活模式
            if show_spatial:
                print(self.get_spatial_activation_pattern())
            
            # 显示从众效应
            herding = result['herding']
            if herding['inhibited']:
                print(f"\n↓ 从众被抑制: {herding['inhibited']}")
            if herding['activated']:
                print(f"\n↑ 从众被激活: {herding['activated']}")
            
            print(f"\n激活神经元: {result['activations']}")
            print(f"输出状态: {self.get_output_states()}")
            
            time.sleep(0.1)
            
        # 最终统计
        print("\n" + "="*60)
        print("模拟完成")
        print("="*60)
        self._print_summary()
        
        if enable_interference:
            print(self.get_herding_summary())
    
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


# ==================== 演示函数 ====================

def demo_basic():
    """基础演示：简单的网络运行"""
    print("\n" + "▶"*20 + " 基础演示 " + "◀"*20 + "\n")
    
    sim = NeuronSimulator(
        n_neurons=10,
        connectivity=4,
        input_ids=[0, 1],
        output_ids=[8, 9],
        seed=42
    )
    
    input_patterns = [
        {0: 2.0},
        {1: 2.0},
    ]
    
    sim.run_simulation(n_steps=20, input_patterns=input_patterns, pause=0)


def demo_spatial_interference():
    """空间干涉演示 - v2.0新功能"""
    print("\n" + "▶"*20 + " 空间干涉演示 " + "◀"*20 + "\n")
    
    sim = NeuronSimulator(
        n_neurons=20,
        connectivity=4,
        input_ids=[0, 1, 2],
        output_ids=[18, 19],
        seed=42,
        neighborhood_radius=8.0,
        interference_strength=0.6,
        spatial_layout="random"
    )
    
    # 显示初始空间分布
    print(sim.get_spatial_distribution())
    
    input_patterns = [
        {0: 2.0, 1: 0.0},
        {0: 0.0, 1: 2.0},
    ]
    
    print("\n运行模拟（启用空间干涉）...\n")
    sim.run_simulation(n_steps=30, input_patterns=input_patterns, pause=0, 
                      enable_interference=True, show_spatial=True)


def demo_text_input():
    """文字输入演示 - v2.0新功能"""
    print("\n" + "▶"*20 + " 文字输入演示 " + "◀"*20 + "\n")
    
    sim = NeuronSimulator(
        n_neurons=16,
        connectivity=3,
        input_ids=[0, 1, 2, 3],
        output_ids=[14, 15],
        seed=100,
        neighborhood_radius=6.0,
        interference_strength=0.5,
        spatial_layout="grid"
    )
    
    # 测试不同文字输入
    test_texts = ["你好", "Hi", "Hello"]
    
    for text in test_texts:
        print(f"\n{'='*60}")
        print(f"测试文字输入: \"{text}\"")
        print("="*60)
        
        # 重置网络
        sim = NeuronSimulator(
            n_neurons=16,
            connectivity=3,
            input_ids=[0, 1, 2, 3],
            output_ids=[14, 15],
            seed=100,
            neighborhood_radius=6.0,
            interference_strength=0.5,
            spatial_layout="grid"
        )
        
        sim.run_text_input(text, n_steps=15, enable_interference=True, show_spatial=True)


def demo_herding_effect():
    """从众效应对比演示 - v2.0新功能"""
    print("\n" + "▶"*20 + " 从众效应对比演示 " + "◀"*20 + "\n")
    
    # 创建两个网络：一个有干涉，一个无干涉
    sim_with = NeuronSimulator(
        n_neurons=15,
        connectivity=4,
        input_ids=[0],
        output_ids=[13, 14],
        seed=42,
        neighborhood_radius=10.0,
        interference_strength=0.8,
        spatial_layout="sphere"
    )
    
    sim_without = NeuronSimulator(
        n_neurons=15,
        connectivity=4,
        input_ids=[0],
        output_ids=[13, 14],
        seed=42,
        neighborhood_radius=10.0,
        interference_strength=0.0,
        spatial_layout="sphere"
    )
    
    input_pattern = {0: 3.0}
    
    print("[无空间干涉]")
    for _ in range(20):
        sim_without.step(input_pattern, enable_interference=False)
    print(f"  最终激活数: {sum(n.state for n in sim_without.neurons)}")
    
    print("\n[有空间干涉]")
    for _ in range(20):
        sim_with.step(input_pattern, enable_interference=True)
    print(f"  最终激活数: {sum(n.state for n in sim_with.neurons)}")
    
    print(sim_with.get_herding_summary())


def demo_learning():
    """学习演示"""
    print("\n" + "▶"*20 + " 学习演示 " + "◀"*20 + "\n")
    
    sim = NeuronSimulator(
        n_neurons=15,
        connectivity=3,
        input_ids=[0, 1],
        output_ids=[13, 14],
        seed=123
    )
    
    input_patterns = [
        {0: 3.0, 1: 0.0},
        {0: 0.0, 1: 3.0},
    ]
    
    print("开始学习训练 (200步)...\n")
    sim.run_simulation(n_steps=200, input_patterns=input_patterns, pause=0)
    
    print("\n" + "▶"*20 + " 学习后测试 " + "◀"*20 + "\n")
    
    print("测试输入模式A (输入0激活):")
    result_a = sim.step({0: 3.0, 1: 0.0})
    print(f"  输出状态: {sim.get_output_states()}")
    
    print("\n测试输入模式B (输入1激活):")
    result_b = sim.step({0: 0.0, 1: 3.0})
    print(f"  输出状态: {sim.get_output_states()}")


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("  神经元网络模拟器 v2.0")
    print("  新增：文字输入、三维空间、空间干涉机制")
    print("█"*60)
    
    # 运行所有演示
    demo_basic()
    input("\n按Enter继续运行空间干涉演示...")
    
    demo_spatial_interference()
    input("\n按Enter继续运行文字输入演示...")
    
    demo_text_input()
    input("\n按Enter继续运行从众效应对比演示...")
    
    demo_herding_effect()
