# 强密码生成器 - 淘汰赛版
# 通过模拟破解测试，逐轮淘汰弱密码，留下真正的强密码
# 2026.4.24

import random
import string
import hashlib

# ========== 常见字典（模拟破解者会用到的） ==========
常见词 = {
    "password", "123456", "qwerty", "admin", "letmein", "welcome",
    "monkey", "dragon", "master", "login", "abc123", "iloveyou",
    "sunshine", "princess", "football", "shadow", "michael", "ninja",
    "mustang", "batman", "trustno1", "dragon", "passw0rd", "hello",
    "charlie", "donald", "love", "hello", "freedom", "whatever",
    "qazwsx", "7777777", "summer", "winter", "spring", "autumn",
    "beijing", "shanghai", "2024", "2025", "2026", "2000", "1234"
}

键盘序列 = {
    "qwerty", "asdfgh", "zxcvbn", "qwertyuiop", "asdfghjkl",
    "1234567890", "0987654321", "qazxsw", "edcvfr", "tgbyhn",
    "1qaz2wsx", "1qaz2wsx3edc", "zaq12wsx", "qweasd", "asd"
}

# ========== 密码强度评估（模拟破解难度） ==========
def 计算破解时长(密码):
    """
    基于密码复杂度估算暴力破解所需时间
    假设破解者每秒可测试 10^10 次（高性能计算集群水平）
    """
    # 计算密码空间大小
    空间 = 0
    if any(c.islower() for c in 密码): 空间 += 26
    if any(c.isupper() for c in 密码): 空间 += 26
    if any(c.isdigit() for c in 密码): 空间 += 10
    if any(not c.isalnum() for c in 密码): 空间 += 32
    
    # 总组合数
    总组合 = 空间 ** len(密码)
    
    # 每秒测试次数（假设顶级攻击者）
    每秒测试 = 10 ** 10  # 100亿次/秒
    
    # 所需秒数（平均破解时间）
    秒数 = 总组合 / 每秒测试 / 2  # 平均值
    
    # 转换为人类可读
    if 秒数 < 1:
        return "瞬间"
    elif 秒数 < 60:
        return f"{秒数:.1f}秒"
    elif 秒数 < 3600:
        return f"{秒数/60:.0f}分钟"
    elif 秒数 < 86400:
        return f"{秒数/3600:.1f}小时"
    elif 秒数 < 31536000:
        return f"{秒数/86400:.0f}天"
    elif 秒数 < 31536000 * 100:
        return f"{秒数/31536000:.1f}年"
    elif 秒数 < 31536000 * 1000000:
        return f"{秒数/31536000/1000:.0f}千年"
    elif 秒数 < 31536000 * 10**12:
        年 = 秒数 / 31536000
        if 年 < 10**15:
            return f"{年/10**12:.1f}万亿年"
        else:
            return "宇宙终结也破解不了"
    else:
        return "理论上不可破解"

def 模拟破解评估(密码):
    """
    模拟破解者会尝试的策略，返回破解难度分数
    分数越高越难破解
    """
    分数 = 0
    长度 = len(密码)
    
    # 1. 基础长度得分
    分数 += min(长度 * 3, 30)  # 长度贡献，最多30分
    
    # 2. 字符种类得分
    有小写 = any(c.islower() for c in 密码)
    有大写 = any(c.isupper() for c in 密码)
    有数字 = any(c.isdigit() for c in 密码)
    有特殊 = any(not c.isalnum() for c in 密码)
    
    字符种类 = sum([有小写, 有大写, 有数字, 有特殊])
    分数 += 字符种类 * 10  # 每多一种字符加10分
    
    # 3. 惩罚：常见词匹配
    密码_lower = 密码.lower()
    for 词 in 常见词:
        if 词 in 密码_lower:
            分数 -= 20
            break
    
    # 4. 惩罚：键盘序列
    for 序列 in 键盘序列:
        if 序列 in 密码_lower:
            分数 -= 25
            break
    
    # 5. 惩罚：连续数字/字母（递增递减）
    连续 = 0
    for i in range(len(密码) - 1):
        if 密码[i].isdigit() and 密码[i+1].isdigit():
            差值 = int(密码[i+1]) - int(密码[i])
            if abs(差值) == 1:  # 123, 321, 456等
                连续 += 1
    分数 -= 连续 * 5
    
    # 6. 惩罚：重复字符
    重复 = len(密码) - len(set(密码))
    分数 -= 重复 * 8
    
    # 7. 惩罚：开头是数字或特殊字符（常见密码模式）
    if 密码[0].isdigit():
        分数 -= 5
    if not 密码[0].isalpha():  # 开头不是字母
        分数 -= 3
    
    # 8. 奖励：特殊字符位置分散
    特殊位置 = [i for i, c in enumerate(密码) if not c.isalnum()]
    if len(特殊位置) > 1:
        分散度 = max(特殊位置) - min(特殊位置)
        if 分散度 > 长度 / 2:
            分数 += 5
    
    # 9. 奖励：大小写混合但无规律
    大写位置 = [i for i, c in enumerate(密码) if c.isupper()]
    小写位置 = [i for i, c in enumerate(密码) if c.islower()]
    if 大写位置 and 小写位置:
        # 检查是否交替
        交替 = all(
            (密码[i].isupper() and 密码[i+1].islower()) or
            (密码[i].islower() and 密码[i+1].isupper())
            for i in range(len(密码)-1) if 密码[i].isalpha() and 密码[i+1].isalpha()
        )
        if not 交替:  # 不是简单交替，加分
            分数 += 3
    
    # 10. 模拟字典攻击（检查部分匹配）
    for 词 in 常见词:
        for i in range(len(密码)):
            if 密码_lower[i:i+len(词)] == 词:
                分数 -= len(词) * 3
                break
    
    return max(分数, 1)  # 至少返回1分

# ========== 密码生成 ==========
def 生成密码(长度=16):
    小写 = string.ascii_lowercase
    大写 = string.ascii_uppercase
    数字 = string.digits
    特殊 = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # 使用更随机的字符选择，打破规律
    密码 = []
    
    # 保证多样性
    密码.append(random.choice(小写))
    密码.append(random.choice(大写))
    密码.append(random.choice(数字))
    密码.append(random.choice(特殊))
    
    # 剩余位置随机填充
    所有字符 = 小写 + 大写 + 数字 + 特殊
    for _ in range(长度 - 4):
        密码.append(random.choice(所有字符))
    
    # 彻底打乱（多次洗牌确保随机）
    for _ in range(3):
        random.shuffle(密码)
    
    return ''.join(密码)

# ========== 淘汰赛主流程 ==========
def 强密码淘汰赛(每轮数量=5, 总轮数=5, 密码长度=16):
    """
    通过多轮"模拟破解"淘汰弱密码，留下真正的强密码
    """
    候选池 = []
    
    print("=" * 60)
    print("🔐 强密码生成器 - 淘汰赛版")
    print("=" * 60)
    print(f"\n规则：生成{每轮数量}个密码 → 模拟破解评估 → 保留最强的")
    print(f"淘汰赛共{总轮数}轮，最终留下不超过{每轮数量 * 2}个强密码\n")
    
    for 轮次 in range(1, 总轮数 + 1):
        print(f"【第 {轮次} 轮】生成 {每轮数量} 个候选密码...")
        
        本轮候选 = []
        for i in range(每轮数量):
            密码 = 生成密码(密码长度)
            分数 = 模拟破解评估(密码)
            时长 = 计算破解时长(密码)
            本轮候选.append((密码, 分数, 时长))
        
        # 按分数排序（分数越高越难破解）
        本轮候选.sort(key=lambda x: x[1], reverse=True)
        
        print(f"  模拟破解测试完成，本轮晋级：")
        晋级数量 = max(2, 每轮数量 // 2)  # 至少晋级2个
        for j, (密码, 分数, 时长) in enumerate(本轮候选[:晋级数量]):
            print(f"    {j+1}. {密码}  (难度: {分数}, 预计破解: {时长})")
            候选池.append((密码, 分数, 时长))
        
        # 混合本轮所有候选，增加多样性
        for 密码, 分数, _ in 本轮候选[晋级数量:]:
            if random.random() < 0.3:  # 30%概率保留弱候选中的变异
                变异密码 = 密码变异(密码)
                新分数 = 模拟破解评估(变异密码)
                新时长 = 计算破解时长(变异密码)
                候选池.append((变异密码, 新分数, 新时长))
        
        print()
    
    # 最终筛选
    print("=" * 70)
    print("🏆 最终强密码 TOP 10（按破解难度排序）：")
    print("=" * 70)
    候选池.sort(key=lambda x: x[1], reverse=True)
    
    最终结果 = []
    最终密码集合 = set()
    不可破解计数 = 0
    for i, (密码, 分数, 时长) in enumerate(候选池[:20]):
        if 密码 not in 最终密码集合:
            最终结果.append((密码, 分数, 时长))
            最终密码集合.add(密码)
            标记 = "🛡️" if "不可破解" in 时长 or "万亿年" in 时长 else "  "
            print(f"  {标记}{len(最终结果):2d}. {密码}")
            print(f"       难度: {分数} | 预计破解: {时长}")
            if "不可破解" in 时长 or "万亿年" in 时长:
                不可破解计数 += 1
            if len(最终结果) >= 10:
                break
    
    print(f"\n✅ 共筛选出 {len(最终结果)} 个强密码")
    if 不可破解计数 > 0:
        print(f"🛡️ 其中 {不可破解计数} 个密码在宇宙尺度内不可破解")
    
    return [p for p, _, _ in 最终结果]

def 密码变异(密码):
    """对密码进行随机变异"""
    小写 = string.ascii_lowercase
    大写 = string.ascii_uppercase
    数字 = string.digits
    特殊 = "!@#$%^&*"
    
    变异 = list(密码)
    for _ in range(random.randint(1, 3)):
        位置 = random.randint(0, len(密码) - 1)
        新字符 = random.choice(小写 + 大写 + 数字 + 特殊)
        变异[位置] = 新字符
    
    return ''.join(变异)

# ========== 运行 ==========
if __name__ == "__main__":
    结果 = 强密码淘汰赛(每轮数量=5, 总轮数=5, 密码长度=16)
