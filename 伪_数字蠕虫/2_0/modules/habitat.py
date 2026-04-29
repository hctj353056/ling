import random
import math
from typing import Dict, List, Tuple, Optional, NamedTuple
from enum import IntEnum

class Action(IntEnum):
    STAY = 0
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4
    EAT = 5

class CellType(IntEnum):
    EMPTY = 0
    FOOD = 1
    POISON = 2
    WALL = 3
    AGENT = 4

class Position(NamedTuple):
    x: int
    y: int

class Observation(NamedTuple):
    energy: float
    position: Position
    local_view: List[List[int]]
    nearest_food_direction: Optional[Position]
    nearest_poison_direction: Optional[Position]

class ActionResult(NamedTuple):
    observation: Observation
    reward: float
    done: bool
    info: dict

class World:
    def __init__(self, width: int = 20, height: int = 10, seed: int = None):
        self.width = width
        self.height = height
        self.grid = [[CellType.EMPTY for _ in range(width)] for _ in range(height)]
        self.food_positions: set = set()
        self.poison_positions: set = set()
        self.agent_pos = Position(width // 2, height // 2)
        if seed is not None:
            random.seed(seed)
        self._spawn_items(initial=True)
    
    def _spawn_items(self, initial: bool = False, food_count: int = 5, poison_count: int = 2):
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
        candidates = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == CellType.EMPTY and Position(x, y) != self.agent_pos:
                    candidates.append(Position(x, y))
        return random.choice(candidates) if candidates else None
    
    def move_agent(self, action: Action) -> Tuple[Position, bool, Optional[CellType]]:
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
        cell_type = self.grid[new_y][new_x]
        return new_pos, moved, (cell_type if cell_type != CellType.EMPTY else None)
    
    def consume_at(self, pos: Position) -> Optional[CellType]:
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
        view = []
        for dy in range(-radius, radius + 1):
            row = []
            for dx in range(-radius, radius + 1):
                nx, ny = pos.x + dx, pos.y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    row.append(int(self.grid[ny][nx]))
                else:
                    row.append(int(CellType.WALL))
            view.append(row)
        return view
    
    def find_nearest(self, pos: Position, target_type: CellType) -> Optional[Position]:
        positions = self.food_positions if target_type == CellType.FOOD else self.poison_positions
        if not positions:
            return None
        nearest = min(positions, key=lambda p: abs(p.x - pos.x) + abs(p.y - pos.y))
        return Position(nearest.x - pos.x, nearest.y - pos.y)

class Worm:
    def __init__(self, initial_energy: float = 100.0):
        self.energy = initial_energy
        self.max_energy = 200.0
        self.alive = True
        self.age = 0
        self.total_food_eaten = 0
    
    def metabolize(self, action: Action) -> float:
        costs = {Action.STAY: 0.5, Action.NORTH: 1.0, Action.SOUTH: 1.0, Action.WEST: 1.0, Action.EAST: 1.0, Action.EAT: 2.0}
        cost = costs.get(action, 1.0)
        self.energy -= cost
        return -cost
    
    def eat(self, food_type: Optional[CellType]) -> float:
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
        if self.energy <= 0:
            self.alive = False
        if self.energy > self.max_energy:
            self.energy = self.max_energy
        return self.alive
    
    def step(self):
        self.age += 1

class Habitat:
    def __init__(self, world_width: int = 20, world_height: int = 10, seed: int = None):
        self.world = World(world_width, world_height, seed)
        self.worm = Worm(initial_energy=100.0)
        self.tick_count = 0
        self.total_reward = 0.0
        self.history: List[dict] = []
        self.food_spawn_timer = 0
        self.food_spawn_interval = 20
    
    def step(self, action: Action) -> ActionResult:
        self.tick_count += 1
        self.worm.step()
        base_reward = self.worm.metabolize(action)
        new_pos, moved, cell_under = self.world.move_agent(action)
        food_reward = 0.0
        if action == Action.EAT:
            consumed = self.world.consume_at(new_pos)
            food_reward = self.worm.eat(consumed)
        total_reward = base_reward + food_reward
        self.total_reward += total_reward
        self.food_spawn_timer += 1
        if self.food_spawn_timer >= self.food_spawn_interval:
            self.world._spawn_items(initial=False)
            self.food_spawn_timer = 0
        obs = self._make_observation()
        alive = self.worm.check_alive()
        self.history.append({'tick': self.tick_count, 'action': int(action), 'reward': total_reward, 'energy': self.worm.energy, 'pos': (new_pos.x, new_pos.y), 'alive': alive})
        return ActionResult(observation=obs, reward=total_reward, done=not alive, info={'tick': self.tick_count, 'action': action.name, 'energy': self.worm.energy, 'pos': (new_pos.x, new_pos.y), 'food_eaten': self.worm.total_food_eaten})
    
    def _make_observation(self) -> Observation:
        pos = self.world.agent_pos
        local = self.world.get_local_view(pos, radius=1)
        food_dir = self.world.find_nearest(pos, CellType.FOOD)
        poison_dir = self.world.find_nearest(pos, CellType.POISON)
        return Observation(energy=self.worm.energy, position=pos, local_view=local, nearest_food_direction=food_dir, nearest_poison_direction=poison_dir)
    
    def reset(self):
        self.world = World(self.world.width, self.world.height)
        self.worm = Worm(initial_energy=100.0)
        self.tick_count = 0
        self.total_reward = 0.0
        self.history = []
        self.food_spawn_timer = 0
    
    def render(self):
        print("\n" + "=" * (self.world.width + 2))
        print(f"  Tick: {self.tick_count:4d} | Energy: {self.worm.energy:6.1f} | Food: {self.worm.total_food_eaten:3d}")
        print("=" * (self.world.width + 2))
        for y in range(self.world.height):
            row = "|"
            for x in range(self.world.width):
                if Position(x, y) == self.world.agent_pos:
                    row += "🐛"
                else:
                    cell = self.world.grid[y][x]
                    symbols = {CellType.EMPTY: "·", CellType.FOOD: "🍎", CellType.POISON: "☠️", CellType.WALL: "█"}
                    row += symbols.get(cell, "?")
            row += "|"
            print(row)
        print("=" * (self.world.width + 2))
        print(f"  Reward: {self.total_reward:.1f}")
