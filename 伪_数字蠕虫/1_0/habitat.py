#!/usr/bin/env python3
"""
数字蠕虫中枢 - Habitat v1.0
蜉蝣阁 | ling 数字生命框架

设计原则:
- 环境与“脑”完全解耦，通过标准接口交互
- 支持网格世界模拟、能量系统、多感官输入
- 内置简单渲染器（终端字符画）
- 预留复数神经网络编码接口
"""

import random
import math
from typing import Dict, List, Tuple, Optional, NamedTuple
from enum import IntEnum


# ==================== 基本类型定义 ====================

class Action(IntEnum):
    """动作空间"""
    STAY = 0    # 原地等待
    NORTH = 1   # 上
    SOUTH = 2   # 下
    WEST = 3    # 左
    EAST = 4    # 右
    EAT = 5     # 进食(如果脚下有食物)


class CellType(IntEnum):
    """单元格类型"""
    EMPTY = 0
    FOOD = 1
    POISON = 2
    WALL = 3
    AGENT = 4


class Position(NamedTuple):
    x: int
    y: int


class Observation(NamedTuple):
    """标准化观测"""
    # 自身状态
    energy: float
    position: Position
    
    # 周围视野 (3x3 邻域，中心是自己)
    local_view: List[List[int]]  # 3×3 整数矩阵，每个值是 CellType
    
    # 食物方向信号 (如果视野内有食物)
    nearest_food_direction: Optional[Position]  # 相对坐标
    nearest_poison_direction: Optional[Position]


class ActionResult(NamedTuple):
    """每步动作的结果"""
    observation: Observation     # 新观测
    reward: float                # 奖励值 (能量变化)
    done: bool                   # 是否死亡
    info: dict                   # 额外信息 (诊断用)


# ==================== 世界模拟器 ====================

class World:
    """网格世界"""
    
    def __init__(self, width: int = 20, height: int = 10, seed: int = None):
        self.width = width
        self.height = height
        self.grid = [[CellType.EMPTY for _ in range(width)] for _ in range(height)]
        self.food_positions: set = set()
        self.poison_positions: set = set()
        self.agent_pos = Position(width // 2, height // 2)
        
        if seed is not None:
            random.seed(seed)
        
        # 初始放置食物和毒物
        self._spawn_items(initial=True)
    
    def _spawn_items(self, initial: bool = False, food_count: int = 5, poison_count: int = 2):
        """生成食物和毒物"""
        count_f = food_count * 2 if initial else food_count
        count_p = poison_count * 2 if initial else poison_count
        
        for _ in range(count_f):
            if len(self.food_positions) < self.width * self.height // 4:
                pos = self._random_empty_position()
                if pos:
                    self.grid[pos.y][pos.x] = CellType.FOOD
                    self.food_positions.add(pos)
        
        for _ in range(count_p):
            if len(self.poison_positions) < self.width * self.height // 8:
                pos = self._random_empty_position()
                if pos:
                    self.grid[pos.y][pos.x] = CellType.POISON
                    self.poison_positions.add(pos)
    
    def _random_empty_position(self) -> Optional[Position]:
        """随机空位置"""
        candidates = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == CellType.EMPTY and Position(x, y) != self.agent_pos:
                    candidates.append(Position(x, y))
        return random.choice(candidates) if candidates else None
    
    def move_agent(self, action: Action) -> Tuple[Position, bool, Optional[CellType]]:
        """
        移动代理，返回 (新位置, 是否成功移动, 脚下物品类型)
        """
        x, y = self.agent_pos
        new_x, new_y = x, y
        
        if action == Action.NORTH and y > 0:
            new_y -= 1
        elif action == Action.SOUTH and y < self.height - 1:
            new_y += 1
        elif action == Action.WEST and x > 0:
            new_x -= 1
        elif action == Action.EAST and x < self.width - 1:
            new_x += 1
        
        moved = (new_x != x or new_y != y)
        new_pos = Position(new_x, new_y)
        self.agent_pos = new_pos
        
        # 检查脚下
        cell_type = self.grid[new_y][new_x]
        return new_pos, moved, (cell_type if cell_type != CellType.EMPTY else None)
    
    def consume_at(self, pos: Position) -> Optional[CellType]:
        """吃掉当前位置的物品"""
        cell = self.grid[pos.y][pos.x]
        if cell == CellType.FOOD:
            self.grid[pos.y][pos.x] = CellType.EMPTY
            self.food_positions.discard(pos)
            return CellType.FOOD
        elif cell == CellType.POISON:
            self.grid[pos.y][pos.x] = CellType.EMPTY
            self.poison_positions.discard(pos)
            return CellType.POISON
        return None
    
    def get_local_view(self, pos: Position, radius: int = 1) -> List[List[int]]:
        """获取以pos为中心的局部视野"""
        view = []
        for dy in range(-radius, radius + 1):
            row = []
            for dx in range(-radius, radius + 1):
                nx, ny = pos.x + dx, pos.y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    row.append(int(self.grid[ny][nx]))
                else:
                    row.append(int(CellType.WALL))  # 边界视作墙
            view.append(row)
        return view
    
    def find_nearest(self, pos: Position, target_type: CellType) -> Optional[Position]:
        """寻找最近的目标类型 (曼哈顿距离)"""
        positions = self.food_positions if target_type == CellType.FOOD else self.poison_positions
        if not positions:
            return None
        
        nearest = min(positions, 
                     key=lambda p: abs(p.x - pos.x) + abs(p.y - pos.y))
        return Position(nearest.x - pos.x, nearest.y - pos.y)  # 相对坐标


# ==================== 蠕虫实体 ====================

class Worm:
    """数字蠕虫 - 能量和生命状态"""
    
    def __init__(self, initial_energy: float = 100.0):
        self.energy = initial_energy
        self.max_energy = 200.0
        self.alive = True
        self.age = 0
        self.total_food_eaten = 0
    
    def metabolize(self, action: Action) -> float:
        """代谢消耗，返回消耗的能量的负值"""
        costs = {
            Action.STAY: 0.5,
            Action.NORTH: 1.0,
            Action.SOUTH: 1.0,
            Action.WEST: 1.0,
            Action.EAST: 1.0,
            Action.EAT: 2.0,  # 进食更耗能
        }
        cost = costs.get(action, 1.0)
        self.energy -= cost
        return -cost
    
    def eat(self, food_type: Optional[CellType]) -> float:
        """进食，返回能量变化"""
        if food_type == CellType.FOOD:
            gain = random.randint(20, 40)
            self.energy = min(self.energy + gain, self.max_energy)
            self.total_food_eaten += 1
            return gain
        elif food_type == CellType.POISON:
            damage = random.randint(15, 30)
            self.energy -= damage
            return -damage
        return 0.0
    
    def check_alive(self) -> bool:
        """检查是否还活着"""
        if self.energy <= 0:
            self.alive = False
        if self.energy > self.max_energy:
            self.energy = self.max_energy
        return self.alive
    
    def step(self):
        """每个tick的生命维护"""
        self.age += 1


# ==================== 中枢主控 ====================

class Habitat:
    """
    数字蠕虫中枢
    负责：
    - 管理世界和蠕虫
    - 接收动作、执行物理、计算奖励
    - 生成标准化观测
    """
    
    def __init__(self, world_width: int = 20, world_height: int = 10, seed: int = None):
        self.world = World(world_width, world_height, seed)
        self.worm = Worm(initial_energy=100.0)
        self.tick_count = 0
        self.total_reward = 0.0
        self.history: List[dict] = []
        
        # 食物补充计时器
        self.food_spawn_timer = 0
        self.food_spawn_interval = 20  # 每20步补充一次食物
    
    def step(self, action: Action) -> ActionResult:
        """
        执行一个动作，返回结果
        这是中枢的核心接口
        """
        self.tick_count += 1
        self.worm.step()
        
        # 1. 代谢消耗 (生存成本)
        base_reward = self.worm.metabolize(action)
        
        # 2. 移动与交互
        new_pos, moved, cell_under = self.world.move_agent(action)
        
        # 3. 进食动作
        food_reward = 0.0
        if action == Action.EAT:
            consumed = self.world.consume_at(new_pos)
            food_reward = self.worm.eat(consumed)
        
        total_reward = base_reward + food_reward
        self.total_reward += total_reward
        
        # 4. 食物再生
        self.food_spawn_timer += 1
        if self.food_spawn_timer >= self.food_spawn_interval:
            self.world._spawn_items(initial=False)
            self.food_spawn_timer = 0
        
        # 5. 生成观测
        obs = self._make_observation()
        
        # 6. 检查存活
        alive = self.worm.check_alive()
        
        # 7. 记录历史
        self.history.append({
            'tick': self.tick_count,
            'action': int(action),
            'reward': total_reward,
            'energy': self.worm.energy,
            'pos': (new_pos.x, new_pos.y),
            'alive': alive,
        })
        
        return ActionResult(
            observation=obs,
            reward=total_reward,
            done=not alive,
            info={
                'tick': self.tick_count,
                'action': action.name,
                'energy': self.worm.energy,
                'pos': (new_pos.x, new_pos.y),
                'food_eaten': self.worm.total_food_eaten,
            }
        )
    
    def _make_observation(self) -> Observation:
        """生成标准化观测"""
        pos = self.world.agent_pos
        local = self.world.get_local_view(pos, radius=1)
        food_dir = self.world.find_nearest(pos, CellType.FOOD)
        poison_dir = self.world.find_nearest(pos, CellType.POISON)
        
        return Observation(
            energy=self.worm.energy,
            position=pos,
            local_view=local,
            nearest_food_direction=food_dir,
            nearest_poison_direction=poison_dir,
        )
    
    def reset(self):
        """重置环境"""
        self.world = World(self.world.width, self.world.height)
        self.worm = Worm(initial_energy=100.0)
        self.tick_count = 0
        self.total_reward = 0.0
        self.history = []
        self.food_spawn_timer = 0
    
    def render(self):
        """终端渲染"""
        print("\n" + "=" * (self.world.width + 2))
        print(f"  Tick: {self.tick_count:4d} | Energy: {self.worm.energy:6.1f} | Food: {self.worm.total_food_eaten:3d}")
        print("=" * (self.world.width + 2))
        
        for y in range(self.world.height):
            row = "|"
            for x in range(self.world.width):
                if Position(x, y) == self.world.agent_pos:
                    row += "🐛"  # 蠕虫
                else:
                    cell = self.world.grid[y][x]
                    symbols = {
                        CellType.EMPTY: "·",
                        CellType.FOOD: "🍎",
                        CellType.POISON: "☠️",
                        CellType.WALL: "█",
                    }
                    row += symbols.get(cell, "?")
            row += "|"
            print(row)
        
        print("=" * (self.world.width + 2))
        print(f"  Reward: {self.total_reward:.1f}")
    
    # ==================== 观测 → 复数编码 (供ling网络使用) ====================
    
    def encode_observation_to_complex(self, obs: Observation) -> List[complex]:
        """
        将观测编码为复数向量，供复数神经网络使用
        这是中枢与ling内置网络的桥梁
        
        返回: 复数列表，每个复数 = 实部(有益) + i*虚部(有害)
        """
        encoded = []
        
        # 自身能量 (归一化)
        energy_norm = obs.energy / 200.0
        encoded.append(complex(energy_norm, 0))
        
        # 局部视野编码 (3×3)
        for row in obs.local_view:
            for cell in row:
                if cell == CellType.FOOD:
                    encoded.append(complex(1.0, 0))       # 纯实部 = 好
                elif cell == CellType.POISON:
                    encoded.append(complex(0, 1.0))       # 纯虚部 = 坏
                elif cell == CellType.AGENT:
                    encoded.append(complex(0.5, 0))
                else:
                    encoded.append(complex(0, 0))
        
        # 食物方向
        if obs.nearest_food_direction:
            dx, dy = obs.nearest_food_direction
            encoded.append(complex(dx * 0.3, 0))
            encoded.append(complex(dy * 0.3, 0))
        else:
            encoded.append(complex(0, 0))
            encoded.append(complex(0, 0))
        
        # 毒物方向 (用虚部表示)
        if obs.nearest_poison_direction:
            dx, dy = obs.nearest_poison_direction
            encoded.append(complex(0, abs(dx) * 0.3))
            encoded.append(complex(0, abs(dy) * 0.3))
        else:
            encoded.append(complex(0, 0))
            encoded.append(complex(0, 0))
        
        return encoded


# ==================== 基础“脑”示例 (可替换为ling网络) ====================

class RandomBrain:
    """随机策略 - 基准测试用"""
    def decide(self, obs: Observation) -> Action:
        return random.choice(list(Action))


class KeyboardBrain:
    """键盘控制 - 调试用"""
    def decide(self, obs: Observation) -> Action:
        key_map = {
            'w': Action.NORTH, 's': Action.SOUTH,
            'a': Action.WEST,  'd': Action.EAST,
            'e': Action.EAT,   'q': Action.STAY,
        }
        import sys
        # 简化：这里需要非阻塞输入，实际调试时建议用 curses
        char = input("Action (wasd/e/q): ").strip().lower()
        return key_map.get(char, Action.STAY)


# ==================== 主循环 ====================

def main_loop(brain, max_ticks: int = 500, render: bool = True):
    """
    主事件循环
    这是数字生命的核心脉搏
    
    Args:
        brain: 任何有 decide(observation) -> Action 的对象
        max_ticks: 最大运行步数
        render: 是否渲染
    """
    habitat = Habitat(world_width=20, world_height=10, seed=42)
    
    for _ in range(max_ticks):
        # 获取观测
        obs = habitat._make_observation()
        
        # 脑做决策
        action = brain.decide(obs)
        
        # 中枢执行动作
        result = habitat.step(action)
        
        if render:
            habitat.render()
        
        if result.done:
            print(f"\n💀 蠕虫在第 {habitat.tick_count} 步死亡")
            print(f"   总食物: {habitat.worm.total_food_eaten}")
            print(f"   总奖励: {habitat.total_reward:.1f}")
            break
    
    return habitat.history


# ==================== 启动入口 ====================

if __name__ == "__main__":
    print("=" * 50)
    print("🐛 数字蠕虫中枢 v1.0")
    print("=" * 50)
    print("\n运行随机策略演示...")
    print("按 Ctrl+C 停止\n")
    
    try:
        brain = RandomBrain()
        history = main_loop(brain, max_ticks=200, render=True)
    except KeyboardInterrupt:
        print("\n\n手动停止。")
    
    print("\n中枢已就绪。下一步接入复数神经网络...")