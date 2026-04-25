#!/usr/bin/env python3
"""
数字蠕虫启动脚本 v2.3 - 指数爆炸修复 + DNA机制
蜉蝣阁 | ling 数字生命框架
"""
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, os.path.join(script_dir, 'modules'))

from habitat import Habitat
from brainstem import Brainstem
from logger import WormLogger
from snapshot import save_snapshot

# 配置
max_ticks = 500
render_every = 10
snapshot_interval = 25
enable_dna = True  # v2.3: 启用DNA机制

# 初始化
habitat = Habitat(world_width=20, world_height=10, seed=42)
brain = Brainstem(
    input_features=9, 
    cache_length=4, 
    network_nodes=20, 
    background_noise=0.05,
    enable_dna=enable_dna
)
logger = WormLogger(log_dir="logs")
logger.open("worm_run_02.csv")  # v2.3 新日志

print("=" * 50)
print("🪱 数字蠕虫 v2.3 - 指数爆炸修复 + DNA机制")
print("=" * 50)

action_counts = {}

for tick in range(max_ticks):
    if not habitat.worm.alive:
        print(f"\n💀 蠕虫在第 {tick} 步死亡")
        break
    
    obs = habitat._make_observation()
    action = brain.decide(obs)
    result = habitat.step(action)
    brain.give_reward(result.reward)
    
    action_counts[action.name] = action_counts.get(action.name, 0) + 1
    
    # 记录日志
    logger.log(
        tick=tick,
        action=action,
        reward=result.reward,
        total_reward=habitat.total_reward,
        obs=obs,
        habitat=habitat,
        brainstem=brain
    )
    
    # 保存快照
    if tick % snapshot_interval == 0:
        snapshot_file = save_snapshot(
            brain, tick,
            habitat.worm.total_food_eaten,
            habitat.worm.energy
        )
        print(f"  📸 快照已保存: {snapshot_file}")
    
    # 渲染和状态
    if tick % render_every == 0 or result.done:
        habitat.render()
        stats = brain.get_network_stats()
        print(f"  动作: {action.name}, 奖励: {result.reward:+.1f}, "
              f"食物: {habitat.worm.total_food_eaten}, 能量: {habitat.worm.energy:.1f}")
        print(f"  网络: 活跃={stats['活跃节点数']}, 连接={stats['连接数']}, "
              f"阈值={stats['平均阈值']:.2f}, 能量={stats['总能量']:.4f}")

log_path = logger.close()

# 回合结束处理
print("\n" + "=" * 50)
print("📊 最终统计")
print("=" * 50)
print(f"  存活步数: {habitat.tick_count}")
print(f"  累计食物: {habitat.worm.total_food_eaten}")
print(f"  最终能量: {habitat.worm.energy:.1f}")
print(f"  动作分布:")
for k, v in sorted(action_counts.items(), key=lambda x: -x[1]):
    print(f"    {k}: {v}")

# v2.3: DNA评估
if enable_dna:
    print("\n🧬 DNA机制:")
    brain.episode结束(
        habitat.worm.total_food_eaten,
        habitat.tick_count,
        habitat.worm.energy
    )
    dna_stats = brain.获取DNA统计()
    for k, v in dna_stats.items():
        print(f"    {k}: {v}")

print(f"\n✅ 日志保存: {log_path}")
print(f"✅ 快照保存: snapshots/ 目录")
if enable_dna:
    print(f"✅ DNA保存: {brain.DNA保存路径}/ 目录")
