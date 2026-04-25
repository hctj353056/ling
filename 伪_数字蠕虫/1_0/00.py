#!/usr/bin/env python3
"""
数字蠕虫启动脚本 v1.1 - 带日志记录
"""
#!/usr/bin/env python3
import os
import sys

# 确保工作目录切换到脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from habitat import Habitat
from brainstem import Brainstem
from logger import WormLogger
import time

# 初始化
habitat = Habitat(world_width=20, world_height=10, seed=42)
brain = Brainstem(input_features=9, cache_length=4, network_nodes=20, background_noise=0.1)
logger = WormLogger(log_dir="logs")
logger.open("worm_run_01.csv")

max_ticks = 500
render_every = 5  # 每5步渲染一次

for tick in range(max_ticks):
    if not habitat.worm.alive:
        break
    
    obs = habitat._make_observation()
    action = brain.decide(obs)
    result = habitat.step(action)
    brain.give_reward(result.reward)
    
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
    
    # 渲染
    if tick % render_every == 0 or result.done:
        habitat.render()
        print(f"  动作: {action.name}, 奖励: {result.reward:.1f}, 日志已记录 {tick+1} 行")

logger.close()
print(f"\n✅ 运行结束，日志保存在 logs/worm_run_01.csv")