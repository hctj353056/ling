#!/usr/bin/env python3
"""
神经元网络对话系统 v3.0
基于神经元网络模拟器 v2 的模块化对话系统

架构：
- InputModule: 用户输入 → UTF-8编码 → 输入神经元激活
- NeuralCore: 神经网络核心，处理信号传播
- OutputModule: 输出神经元 → 思维链(内隐) + 回复(外显) + 动作
- EmotionModule: 情绪评价 → 学习信号

太极球空间结构：
- 第一象限 (x>0, y>0): 输入神经元
- 第三象限 (x<0, y<0): 输出神经元
  - 内隐输出区：思维链
  - 外显输出区：正式回复
  - 动作输出区：工具调用
"""

import random
import math
import os
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


# ==================== 神经元类 ====================

class Neuron:
    """神经元类"""
    
    def __init__(self, nid: int, polarity: int = 1, 
                 is_input: bool = False, is_inner: bool = False,
                 is_outer: bool = False, is_action: bool = False,
                 x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.id = nid
        self.state = 0
        self.polarity = polarity
        self.k = 0.5
        self.ka = 1
        self.is_input = is_input
        self.is_inner = is_inner      # 内隐输出（思维链）
        self.is_outer = is_outer      # 外显输出（回复）
        self.is_action = is_action    # 动作输出
        self.x = x
        self.y = y
        self.z = z
        self.output_history = []
        self.interference_signal = 0.0
        self.neighbor_activation_ratio = 0.0
        self.affected_by_herding = False
        self.herding_type = None
        
        # 输出神经元类型标记
        if is_inner:
            self.output_type = "inner"
        elif is_outer:
            self.output_type = "outer"
        elif is_action:
            self.output_type = "action"
        else:
            self.output_type = "hidden"
    
    @property
    def kb(self) -> float:
        """动态阈值"""
        base_kb = (self.k + 1.0 / NeuralCore.NEURON_COUNT) * self.ka
        return base_kb - self.interference_signal
    
    def distance_to(self, other: 'Neuron') -> float:
        """计算距离"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def activate(self):
        self.state = 1
        self.ka = min(self.ka + 1, 20)
        self.output_history.append(1)
        
    def deactivate(self):
        self.state = 0
        self.output_history.append(0)
        
    def check_no_activation(self):
        self.ka = max(self.ka - 1, 1)
        
    def __repr__(self):
        state = "■" if self.state == 1 else "□"
        polarity = "+" if self.polarity > 0 else "-"
        type_str = ""
        if self.is_input:
            type_str = "[IN]"
        elif self.is_inner:
            type_str = "[思维]"
        elif self.is_outer:
            type_str = "[回复]"
        elif self.is_action:
            type_str = "[动作]"
        return f"N{self.id}({polarity},kb={self.kb:.2f},s={self.state}){type_str}"


# ==================== 突触类 ====================

class Synapse:
    """突触连接"""
    
    def __init__(self, from_id: int, to_id: int, weight: float):
        self.from_id = from_id
        self.to_id = to_id
        self.weight = weight
        self.inactive_count = 0
        
    def strengthen(self, amount: float = 0.02):
        self.weight = min(self.weight + amount, 1.0)
        self.inactive_count = 0
        
    def weaken(self, amount: float = 0.005):
        self.weight = max(self.weight - amount, 0.0)
        self.inactive_count += 1
        
    def is_pruned(self) -> bool:
        return self.weight < 0.05 and self.inactive_count >= 10


# ==================== 输入模块 ====================

class InputModule:
    """输入模块：用户输入 → UTF-8编码 → 输入神经元激活"""
    
    def __init__(self, input_neurons: List[int], network: 'NeuralCore' = None):
        self.input_neurons = input_neurons
        self.network = network
        self.encoding_history = []
        
    def encode(self, text: str) -> Dict[int, float]:
        """
        将文字编码为神经元激活信号
        
        Args:
            text: 输入字符串
            
        Returns:
            {神经元ID: 激活强度}
        """
        if not text:
            return {}
            
        # UTF-8编码
        utf8_bytes = text.encode('utf-8')
        
        signals = {}
        for i, byte_val in enumerate(utf8_bytes):
            neuron_id = self.input_neurons[i % len(self.input_neurons)]
            # 归一化到激活强度
            signal = (byte_val / 255.0) * 3.0
            signals[neuron_id] = signals.get(neuron_id, 0) + signal
            
        self.encoding_history.append({
            'text': text,
            'bytes': list(utf8_bytes),
            'signals': signals.copy()
        })
        
        return signals
    
    def inject(self, network: 'NeuralCore'):
        """注入到网络"""
        self.network = network
        # 更新输入神经元列表
        self.input_neurons = [n.id for n in network.neurons if n.is_input]
        
    def get_encoding_info(self, text: str) -> str:
        """获取编码信息"""
        utf8_bytes = text.encode('utf-8')
        lines = [
            f"文字: \"{text}\"",
            f"UTF-8字节 ({len(utf8_bytes)}个): {[b for b in utf8_bytes]}",
            f"输入神经元: {self.input_neurons}",
        ]
        return "\n".join(lines)


# ==================== 情绪模块 ====================

class EmotionModule:
    """情绪评价模块：多维情绪张量"""
    
    def __init__(self):
        self.tensor = {
            "评分": 0.5,        # 用户评分 [0, 1]
            "相关性": 0.5,      # 自动计算
            "流畅度": 0.5,      # 自动计算
        }
        self.history = []
        
    def set_user_rating(self, score: float):
        """
        设置用户评分
        
        Args:
            score: 评分 [0, 1]
        """
        self.tensor["评分"] = max(0.0, min(1.0, score))
        self.history.append({
            'type': 'rating',
            'score': score,
            'tensor': self.tensor.copy()
        })
        
    def auto_evaluate(self, inner_output: str, outer_output: str, 
                       expected_keywords: List[str] = None):
        """
        自动评估输出质量
        
        Args:
            inner_output: 内隐输出（思维链）
            outer_output: 外显输出（回复）
            expected_keywords: 期望包含的关键词
        """
        # 计算流畅度（基于输出长度和连贯性）
        words = outer_output.split()
        if len(words) > 0:
            # 简单的流畅度评估
            fluency = min(1.0, len(words) / 10.0)  # 假设10词为理想长度
            self.tensor["流畅度"] = 0.3 + 0.7 * fluency
        
        # 计算相关性（如果有关键词）
        if expected_keywords:
            matches = sum(1 for kw in expected_keywords if kw in outer_output)
            relevance = matches / len(expected_keywords) if expected_keywords else 0.5
            self.tensor["相关性"] = 0.5 + 0.5 * relevance
        
        self.history.append({
            'type': 'auto',
            'inner': inner_output,
            'outer': outer_output,
            'tensor': self.tensor.copy()
        })
        
    def to_learning_signal(self) -> float:
        """
        将情绪张量转换为学习信号
        
        Returns:
            学习信号 [-1, 1]
        """
        # 加权平均
        score = self.tensor["评分"]
        relevance = self.tensor["相关性"]
        fluency = self.tensor["流畅度"]
        
        # 综合评分
        combined = 0.5 * score + 0.3 * relevance + 0.2 * fluency
        
        # 转换为 [-1, 1]
        signal = (combined - 0.5) * 2
        
        self.history.append({
            'type': 'signal',
            'combined': combined,
            'signal': signal
        })
        
        return signal
    
    def reset(self):
        """重置为默认值"""
        self.tensor = {
            "评分": 0.5,
            "相关性": 0.5,
            "流畅度": 0.5,
        }


# ==================== 神经网络核心 ====================

class NeuralCore:
    """神经网络核心"""
    
    NEURON_COUNT = 0  # 类变量，将在初始化时设置
    
    def __init__(self, neuron_count: int = 100, input_count: int = 20,
                 inner_count: int = 10, outer_count: int = 10, 
                 action_count: int = 5, connectivity: int = 5,
                 seed: int = None, interference_strength: float = 0.5):
        """
        初始化神经网络
        
        Args:
            neuron_count: 总神经元数
            input_count: 输入神经元数
            inner_count: 内隐输出神经元数（思维链）
            outer_count: 外显输出神经元数（回复）
            action_count: 动作输出神经元数
            connectivity: 每个神经元的平均连接数
            seed: 随机种子
            interference_strength: 空间干涉强度
        """
        if seed is not None:
            random.seed(seed)
            
        NeuralCore.NEURON_COUNT = neuron_count
        self.n_neurons = neuron_count
        self.input_count = input_count
        self.inner_count = inner_count
        self.outer_count = outer_count
        self.action_count = action_count
        self.tick = 0
        self.neurons: List[Neuron] = []
        self.synapses: List[Synapse] = []
        self.interference_strength = interference_strength
        self.activation_history = []
        
        # 初始化
        self._init_neurons()
        self._init_synapses(connectivity)
        
    def _init_neurons(self):
        """初始化神经元（太极球空间结构）"""
        # 计算各区域
        hidden_count = self.n_neurons - self.input_count - self.inner_count - self.outer_count - self.action_count
        
        neuron_id = 0
        
        # 第一象限 (x>0, y>0): 输入神经元
        for i in range(self.input_count):
            angle = (i / self.input_count) * 2 * math.pi
            r = 8
            x = r * math.cos(angle)
            y = r * math.sin(angle)
            z = random.uniform(-2, 2)
            self.neurons.append(Neuron(
                nid=neuron_id, polarity=1, is_input=True,
                x=x, y=y, z=z
            ))
            neuron_id += 1
            
        # 中间区域: 隐藏神经元
        for i in range(hidden_count):
            # 在原点附近随机分布
            x = random.uniform(-3, 3)
            y = random.uniform(-3, 3)
            z = random.uniform(-3, 3)
            polarity = 1 if random.random() < 0.8 else -1
            self.neurons.append(Neuron(
                nid=neuron_id, polarity=polarity,
                x=x, y=y, z=z
            ))
            neuron_id += 1
            
        # 第三象限 (x<0, y<0): 输出神经元
        
        # 内隐输出区（思维链）- 区域1
        for i in range(self.inner_count):
            angle = (i / self.inner_count) * math.pi + math.pi
            r = 8
            x = r * math.cos(angle) * 0.5  # 更靠近中心
            y = r * math.sin(angle) * 0.5
            z = random.uniform(-1, 1)
            self.neurons.append(Neuron(
                nid=neuron_id, polarity=1, is_inner=True,
                x=x, y=y, z=z
            ))
            neuron_id += 1
            
        # 外显输出区（回复）- 区域2
        for i in range(self.outer_count):
            angle = (i / self.outer_count) * math.pi + math.pi
            r = 8
            x = r * math.cos(angle) * 1.5  # 靠外
            y = r * math.sin(angle) * 1.5
            z = random.uniform(-1, 1)
            self.neurons.append(Neuron(
                nid=neuron_id, polarity=1, is_outer=True,
                x=x, y=y, z=z
            ))
            neuron_id += 1
            
        # 动作输出区 - 区域3
        for i in range(self.action_count):
            angle = math.pi + (i / self.action_count) * math.pi
            r = 8
            x = r * math.cos(angle) * 2  # 最外围
            y = r * math.sin(angle) * 2
            z = random.uniform(-1, 1)
            self.neurons.append(Neuron(
                nid=neuron_id, polarity=1, is_action=True,
                x=x, y=y, z=z
            ))
            neuron_id += 1
            
    def _init_synapses(self, avg_connections: int):
        """初始化连接"""
        for i in range(self.n_neurons):
            n_downstream = max(1, min(avg_connections + random.randint(-2, 2), self.n_neurons - 1))
            
            downstream_ids = random.sample(
                [j for j in range(self.n_neurons) if j != i],
                n_downstream
            )
            
            for j in downstream_ids:
                if not self._synapse_exists(i, j):
                    weight = random.uniform(0.3, 0.8)
                    self.synapses.append(Synapse(i, j, weight))
                    
    def _synapse_exists(self, from_id: int, to_id: int) -> bool:
        return any(s.from_id == from_id and s.to_id == to_id for s in self.synapses)
    
    def _get_upstream_synapses(self, neuron_id: int) -> List[Tuple[Synapse, Neuron]]:
        result = []
        for syn in self.synapses:
            if syn.to_id == neuron_id:
                result.append((syn, self.neurons[syn.from_id]))
        return result
    
    def _get_downstream_synapses(self, neuron_id: int) -> List[Synapse]:
        return [s for s in self.synapses if s.from_id == neuron_id]
    
    def get_neighbors(self, neuron_id: int, radius: float = 10.0) -> List[int]:
        neuron = self.neurons[neuron_id]
        neighbors = []
        for other in self.neurons:
            if other.id != neuron_id and neuron.distance_to(other) <= radius:
                neighbors.append(other.id)
        return neighbors
    
    def _calculate_interference(self):
        """计算空间干涉"""
        interference_signals = {}
        
        for neuron in self.neurons:
            neighbor_ids = self.get_neighbors(neuron.id)
            
            if not neighbor_ids:
                interference_signals[neuron.id] = 0.0
                neuron.neighbor_activation_ratio = 0.0
                continue
                
            active_neighbors = sum(1 for nid in neighbor_ids if self.neurons[nid].state == 1)
            activation_ratio = active_neighbors / len(neighbor_ids)
            neuron.neighbor_activation_ratio = activation_ratio
            
            if activation_ratio > 0.5:
                interference = self.interference_strength * (activation_ratio - 0.5) * 2
            else:
                interference = -self.interference_strength * (0.5 - activation_ratio) * 2
                
            interference_signals[neuron.id] = interference
            
        return interference_signals
    
    def process(self, input_signals: Dict[int, float], 
                ticks: int = 20, 
                enable_interference: bool = True) -> Dict[str, any]:
        """
        处理输入信号
        
        Args:
            input_signals: {神经元ID: 信号强度}
            ticks: 运行步数
            enable_interference: 是否启用空间干涉
            
        Returns:
            处理结果
        """
        results = {
            'ticks': [],
            'final_activations': [],
            'inner_activations': [],
            'outer_activations': [],
            'action_activations': [],
        }
        
        for t in range(ticks):
            self.tick += 1
            
            # 衰减输入
            decay = 0.85 ** t
            decayed_signals = {k: v * decay for k, v in input_signals.items()}
            
            # 干涉
            if enable_interference:
                interference = self._calculate_interference()
                for neuron in self.neurons:
                    neuron.interference_signal = interference.get(neuron.id, 0.0)
            
            # 计算输入
            neuron_inputs = {}
            for nid, neuron in enumerate(self.neurons):
                neuron_inputs[nid] = decayed_signals.get(nid, 0)
                
                for syn, upstream in self._get_upstream_synapses(nid):
                    signal = upstream.state * upstream.polarity * syn.weight * 1.0
                    neuron_inputs[nid] += signal
                    
            # 更新状态
            activations = []
            for nid, neuron in enumerate(self.neurons):
                b = neuron_inputs[nid]
                
                if b > neuron.kb:
                    neuron.activate()
                    activations.append(nid)
                else:
                    neuron.deactivate()
                    neuron.check_no_activation()
                    
            # 演化结构
            self._evolve_structure(activations)
            
            # 记录
            results['ticks'].append({
                'tick': self.tick,
                'activations': activations.copy()
            })
            
            # 记录输出区域激活
            results['inner_activations'].extend([n for n in activations if self.neurons[n].is_inner])
            results['outer_activations'].extend([n for n in activations if self.neurons[n].is_outer])
            results['action_activations'].extend([n for n in activations if self.neurons[n].is_action])
            
        # 最终状态
        results['final_activations'] = [n.id for n in self.neurons if n.state == 1]
        
        self.activation_history.append(results)
        
        return results
    
    def _evolve_structure(self, activations: List[int]):
        """结构演化"""
        synapses_to_remove = []
        
        for syn in self.synapses:
            if syn.from_id in activations:
                syn.strengthen()
            else:
                syn.weaken()
                
            if syn.is_pruned():
                synapses_to_remove.append(syn)
                
        for syn in synapses_to_remove:
            self.synapses.remove(syn)
            
        # 随机添加新连接
        if self.tick % 50 == 0 and len(self.synapses) < self.n_neurons * 5:
            from_id = random.randint(0, self.n_neurons - 1)
            to_id = random.randint(0, self.n_neurons - 1)
            if from_id != to_id and not self._synapse_exists(from_id, to_id):
                self.synapses.append(Synapse(from_id, to_id, weight=0.1))
                
    def learn(self, emotion_signal: float):
        """
        根据情绪信号调整连接权重
        
        Args:
            emotion_signal: 学习信号 [-1, 1]
        """
        if emotion_signal == 0:
            return
            
        adjustment = emotion_signal * 0.01
        
        # 调整最近激活的连接
        last_result = self.activation_history[-1] if self.activation_history else None
        if last_result:
            final_activations = last_result['final_activations']
            
            for syn in self.synapses:
                # 如果这个连接参与了激活
                if syn.from_id in final_activations:
                    if adjustment > 0:
                        syn.strengthen(abs(adjustment))
                    else:
                        syn.weaken(abs(adjustment))
                        
    def get_active_output_neurons(self) -> Dict[str, List[int]]:
        """获取当前活跃的输出神经元"""
        return {
            'inner': [n.id for n in self.neurons if n.is_inner and n.state == 1],
            'outer': [n.id for n in self.neurons if n.is_outer and n.state == 1],
            'action': [n.id for n in self.neurons if n.is_action and n.state == 1],
        }


# ==================== 输出模块 ====================

class OutputModule:
    """输出模块：神经元激活 → 思维链/回复/动作"""
    
    # 预设回复模板
    GREETING_TEMPLATES = [
        "你好！有什么我可以帮你的吗？",
        "嗨！很高兴见到你。",
        "你好，今天怎么样？",
    ]
    
    QUESTION_TEMPLATES = [
        "让我想想...",
        "这是个有趣的问题。",
        "关于这个，我可以这样回答：",
    ]
    
    ACTION_TEMPLATES = {
        0: "搜索中...",
        1: "计算中...",
        2: "分析中...",
        3: "查找中...",
        4: "处理中...",
    }
    
    def __init__(self, network: NeuralCore = None):
        self.network = network
        self.thought_patterns = [
            "接收到输入信号，开始处理...",
            "激活相关联想区域...",
            "检索记忆模式...",
            "生成响应候选...",
            "评估多个选项...",
            "选择最优响应...",
            "准备输出...",
        ]
        
    def inject(self, network: NeuralCore):
        """注入网络"""
        self.network = network
        
    def decode_inner(self) -> str:
        """
        解码内隐输出 → 思维链（红色显示）
        
        Returns:
            思维链字符串
        """
        if not self.network:
            return "[无网络连接]"
            
        # 获取内隐神经元激活
        inner_ids = [n.id for n in self.network.neurons if n.is_inner and n.state == 1]
        
        if not inner_ids:
            # 如果没有内隐激活，生成简单思维链
            active_count = sum(1 for n in self.network.neurons if n.state == 1)
            return f"[TICK {self.network.tick}] 激活神经元: {active_count}个"
        
        # 基于激活模式生成思维链
        active_neurons = len(inner_ids)
        total_inner = sum(1 for n in self.network.neurons if n.is_inner)
        
        # 简单的模式匹配
        thought = self._generate_thought(inner_ids, active_neurons, total_inner)
        
        return thought
    
    def _generate_thought(self, active_ids: List[int], count: int, total: int) -> str:
        """生成思维链文本"""
        thoughts = []
        
        # 添加基础思维
        thoughts.append(f"内隐区域激活: {count}/{total}")
        
        # 基于ID模式添加细节
        if len(active_ids) > 0:
            avg_id = sum(active_ids) / len(active_ids)
            thoughts.append(f"平均激活位置: N{avg_id:.0f}")
            
        # 随机添加思维元素
        if count >= 3:
            thoughts.append("模式识别: 发现关联结构")
        if any(n.id % 2 == 0 for n in self.network.neurons if n.is_inner and n.state == 1):
            thoughts.append("时序特征: 检测到偶数序列")
        if any(n.id % 3 == 0 for n in self.network.neurons if n.is_inner and n.state == 1):
            thoughts.append("分组特征: 检测到三的倍数")
            
        # 添加通用思维
        thoughts.append(random.choice(self.thought_patterns))
        
        return " → ".join(thoughts[:4])
    
    def decode_outer(self) -> str:
        """
        解码外显输出 → 回复（蓝色显示）
        
        Returns:
            回复字符串
        """
        if not self.network:
            return "[无网络连接]"
            
        # 获取外显神经元激活
        outer_ids = [n.id for n in self.network.neurons if n.is_outer and n.state == 1]
        
        if not outer_ids:
            # 如果没有外显激活，使用预设模板
            return self._generate_fallback_response()
        
        # 基于激活模式生成回复
        return self._generate_response(outer_ids)
    
    def _generate_response(self, active_ids: List[int]) -> str:
        """基于激活模式生成回复"""
        # 获取激活的神经元ID的某些特征
        pattern_sum = sum(active_ids)
        pattern_hash = pattern_sum % 100
        
        # 简单分类
        if pattern_hash < 33:
            return random.choice(self.GREETING_TEMPLATES)
        elif pattern_hash < 66:
            return random.choice(self.QUESTION_TEMPLATES)
        else:
            return f"基于激活模式 {pattern_hash} 的响应"
    
    def _generate_fallback_response(self) -> str:
        """生成后备回复"""
        responses = [
            "我在思考中...",
            "让我组织一下语言...",
            "这个问题值得深思...",
            "我正在处理你的请求...",
        ]
        return random.choice(responses)
    
    def check_action(self) -> Optional[str]:
        """
        检查动作神经元
        
        Returns:
            动作指令，如果没有则返回None
        """
        if not self.network:
            return None
            
        action_ids = [n.id for n in self.network.neurons if n.is_action and n.state == 1]
        
        if action_ids:
            # 返回激活的动作
            return self.ACTION_TEMPLATES.get(action_ids[0] % len(self.ACTION_TEMPLATES), 
                                              f"动作{action_ids[0]}")
        return None


# ==================== 对话管理器 ====================

class NeuronChat:
    """神经元网络对话管理器"""
    
    def __init__(self, neuron_count: int = 100, 
                 input_count: int = 20, inner_count: int = 10,
                 outer_count: int = 10, action_count: int = 5,
                 seed: int = None):
        """
        初始化对话系统
        """
        self.network = NeuralCore(
            neuron_count=neuron_count,
            input_count=input_count,
            inner_count=inner_count,
            outer_count=outer_count,
            action_count=action_count,
            seed=seed
        )
        
        input_ids = [n.id for n in self.network.neurons if n.is_input]
        self.input_module = InputModule(input_ids, self.network)
        self.output_module = OutputModule(self.network)
        self.emotion_module = EmotionModule()
        
        self.conversation_history = []
        self.tick_count = 0
        
    def chat(self, user_input: str, ticks: int = 20, 
             show_thinking: bool = True) -> Tuple[str, str, Optional[str]]:
        """
        处理对话
        
        Args:
            user_input: 用户输入
            ticks: 处理步数
            show_thinking: 是否显示思维链
            
        Returns:
            (思维链, 回复, 动作)
        """
        if not user_input.strip():
            return "", "", None
            
        # 编码输入
        signals = self.input_module.encode(user_input)
        
        # 处理
        results = self.network.process(signals, ticks=ticks)
        
        # 解码输出
        inner_text = self.output_module.decode_inner()
        outer_text = self.output_module.decode_outer()
        action = self.output_module.check_action()
        
        # 记录
        self.conversation_history.append({
            'input': user_input,
            'inner': inner_text,
            'outer': outer_text,
            'action': action,
        })
        
        self.tick_count += ticks
        
        return inner_text, outer_text, action
    
    def rate(self, score: float):
        """
        评分并学习
        
        Args:
            score: 评分 [0, 1]
        """
        self.emotion_module.set_user_rating(score)
        signal = self.emotion_module.to_learning_signal()
        self.network.learn(signal)
        
    def get_network_info(self) -> str:
        """获取网络信息"""
        lines = [
            f"神经元总数: {self.network.n_neurons}",
            f"输入神经元: {self.network.input_count}",
            f"内隐神经元: {self.network.inner_count}",
            f"外显神经元: {self.network.outer_count}",
            f"动作神经元: {self.network.action_count}",
            f"突触连接: {len(self.network.synapses)}",
            f"总处理步数: {self.tick_count}",
            f"对话轮次: {len(self.conversation_history)}",
        ]
        return "\n".join(lines)
    
    def reset(self):
        """重置系统"""
        self.conversation_history = []
        self.tick_count = 0
        self.emotion_module.reset()


# ==================== 交互循环 ====================

def interactive_mode():
    """交互模式"""
    print("\n" + "="*60)
    print("🧠 神经元网络对话系统 v3.0")
    print("="*60)
    print("基于太极球空间结构的模块化神经网络对话系统")
    print("\n颜色说明:")
    print("  \033[91m[思维] 红色 = 内隐处理（思维链）\033[0m")
    print("  \033[94m[回复] 蓝色 = 外显输出（正式回复）\033[0m")
    print("\n命令:")
    print("  :quit 或 :q - 退出")
    print("  :rate <0-1> - 对上一条回复评分")
    print("  :info - 显示网络信息")
    print("  :reset - 重置对话历史")
    print("="*60 + "\n")
    
    # 初始化对话系统
    chat = NeuronChat(
        neuron_count=80,
        input_count=15,
        inner_count=8,
        outer_count=8,
        action_count=4,
        seed=42
    )
    
    last_inner = ""
    last_outer = ""
    
    while True:
        try:
            user_input = input("\n\033[92m你\033[0m > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n退出对话系统...")
            break
            
        if not user_input:
            continue
            
        # 命令处理
        if user_input.lower() in [':quit', ':q', '退出', 'exit']:
            print("\n感谢使用！再见！\n")
            break
            
        elif user_input.lower() == ':info':
            print("\n" + chat.get_network_info())
            continue
            
        elif user_input.lower() == ':reset':
            chat.reset()
            last_inner = ""
            last_outer = ""
            print("\n对话历史已重置")
            continue
            
        elif user_input.lower().startswith(':rate '):
            try:
                score = float(user_input.split()[1])
                if 0 <= score <= 1:
                    if last_outer:
                        chat.rate(score)
                        print(f"\n✓ 已评分: {score:.1f}")
                    else:
                        print("\n⚠ 还没有可评分的回复")
                else:
                    print("\n⚠ 评分范围应为 0-1")
            except (ValueError, IndexError):
                print("\n⚠ 无效的评分格式，使用 :rate <0-1>")
            continue
            
        # 正常对话
        inner_text, outer_text, action = chat.chat(user_input, ticks=15)
        
        last_inner = inner_text
        last_outer = outer_text
        
        # 输出思维链（红色）
        if inner_text:
            print(f"\n\033[91m[思维] {inner_text}\033[0m")
        
        # 输出回复（蓝色）
        if outer_text:
            print(f"\033[94m[回复] {outer_text}\033[0m")
        
        # 输出动作
        if action:
            print(f"\n\033[93m[动作] {action}\033[0m")


def demo_mode():
    """演示模式"""
    print("\n" + "▶"*20 + " 神经元对话系统演示 " + "◀"*20 + "\n")
    
    chat = NeuronChat(seed=42)
    
    test_inputs = [
        "你好",
        "你是谁？",
        "今天天气怎么样？",
        "讲个笑话吧",
    ]
    
    for user_input in test_inputs:
        print(f"\n{'='*60}")
        print(f"\033[92m用户\033[0m > {user_input}")
        print("="*60)
        
        inner_text, outer_text, action = chat.chat(user_input, ticks=15)
        
        if inner_text:
            print(f"\n\033[91m[思维链]\033[0m {inner_text}")
        
        if outer_text:
            print(f"\n\033[94m[回复]\033[0m {outer_text}")
            
        if action:
            print(f"\n\033[93m[动作]\033[0m {action}")
            
    print("\n\n" + chat.get_network_info())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_mode()
    else:
        interactive_mode()
