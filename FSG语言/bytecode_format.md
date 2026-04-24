# FSG 字节码格式定义

> 蜉熵阁 - FSG Bytecode (.fsgb) 文件格式  
> 版本: 1.0

---

## 概述

FSGB (FSG Bytecode) 是一种紧凑的二进制格式，用于存储编译后的FSG汇编程序。

### 设计目标
- 紧凑：最小化文件体积
- 可移植：统一字节序 (大端序)
- 可扩展：支持未来功能扩展
- 易于解析：简单清晰的数据布局

---

## 文件结构

```
+------------------+
|   文件头 (32B)   |
+------------------+
|   段头表         |
+------------------+
|   .text 段       |
+------------------+
|   .data 段       |
+------------------+
|   .rodata 段     |
+------------------+
|   符号表         |
+------------------+
|   调试信息(可选)  |
+------------------+
```

---

## 文件头 (32字节)

| 偏移 | 大小 | 字段 | 说明 |
|------|------|------|------|
| 0x00 | 4 | magic | 魔数: `0x46534742` ("FSGB") |
| 0x04 | 2 | version | 版本号: 1.0 → 0x0100 |
| 0x06 | 2 | flags | 标志位 (见下表) |
| 0x08 | 4 | entry_point | 入口点偏移 |
| 0x0C | 4 | text_size | .text 段大小 |
| 0x10 | 4 | data_size | .data 段大小 |
| 0x14 | 4 | rodata_size | .rodata 段大小 |
| 0x18 | 4 | symbol_count | 符号表条目数 |
| 0x1C | 4 | debug_size | 调试信息大小 (0=无) |
| 0x20 | 4 | checksum | 文件校验和 (CRC32) |

### 标志位 (flags)

| 位 | 名称 | 说明 |
|----|------|------|
| 0 | DEBUG | 包含调试信息 |
| 1 | COMPRESSED | 数据已压缩 |
| 2 | ENDIAN_LITTLE | 小端序 (默认大端) |
| 3-15 | RESERVED | 保留 |

---

## 段格式

### 通用段头 (8字节)

| 偏移 | 大小 | 字段 | 说明 |
|------|------|------|------|
| 0x00 | 4 | offset | 段数据在文件中的偏移 |
| 0x04 | 4 | size | 段数据大小 |

### .text 段

代码段，包含可执行指令。

```
[字节码指令序列...]
```

指令编码见下一节。

### .data 段

可读写数据段。

```
[字节序列...]
```

### .rodata 段

只读数据段，通常存放字符串常量。

```
[字节序列...]
```

字符串以 NULL ('\0') 结尾。

---

## 指令编码

### 通用格式

```
[opcode: 1][operands...]
```

- 指令长度 = 1 + 操作数总字节数
- 操作数连续排列，无分隔符

### 操作数编码

#### 寄存器 (1字节)

```
[reg: 1]  ; 0x00=R0, 0x01=R1, ... 0x07=R7
```

| 值 | 寄存器 |
|----|--------|
| 0x00 | R0 |
| 0x01 | R1 |
| 0x02 | R2 |
| 0x03 | R3 |
| 0x04 | R4 |
| 0x05 | R5 |
| 0x06 | R6 |
| 0x07 | R7 |

#### 立即数 (1-4字节)

```
[imm8: 1]     ; -128 ~ 127
[imm32: 4]    ; 32位整数
```

编码规则：
- 如果值在 [-128, 127] 范围内，使用 imm8
- 否则使用 imm32

#### 内存地址 (4字节)

```
[addr: 4]     ; 32位地址 (大端序)
```

#### 标签偏移 (4字节)

```
[offset: 4]   ; 相对PC的偏移量 (有符号)
```

### 指令编码表

| 助记符 | opcode | 参数格式 | 长度 |
|--------|--------|----------|------|
| NOP | 0x00 | - | 1B |
| HALT | 0x01 | - | 1B |
| LOAD | 0x10 | reg, addr32 | 6B |
| STORE | 0x11 | addr32, reg | 6B |
| LOADIMM | 0x12 | reg, imm8/imm32 | 2-5B |
| PUSH | 0x13 | reg | 2B |
| POP | 0x14 | reg | 2B |
| MOV | 0x15 | reg_dest, reg_src | 3B |
| ADD | 0x20 | reg_d, reg_a, reg_b | 4B |
| ADD | 0x20 | reg_d, reg_a, imm | 2-5B |
| SUB | 0x21 | reg_d, reg_a, reg_b | 4B |
| MUL | 0x22 | reg_d, reg_a, reg_b | 4B |
| DIV | 0x23 | reg_d, reg_a, reg_b | 4B |
| NEG | 0x24 | reg | 2B |
| MOD | 0x25 | reg_d, reg_a, reg_b | 4B |
| CMP | 0x30 | reg_a, reg_b | 3B |
| AND | 0x31 | reg_d, reg_a, reg_b | 4B |
| OR | 0x32 | reg_d, reg_a, reg_b | 4B |
| XOR | 0x33 | reg_d, reg_a, reg_b | 4B |
| NOT | 0x34 | reg | 2B |
| SHL | 0x35 | reg_d, reg_s, count | 3B |
| SHR | 0x36 | reg_d, reg_s, count | 3B |
| JMP | 0x40 | offset32 | 5B |
| JE | 0x41 | offset32 | 5B |
| JNE | 0x42 | offset32 | 5B |
| JG | 0x43 | offset32 | 5B |
| JGE | 0x44 | offset32 | 5B |
| JL | 0x45 | offset32 | 5B |
| JLE | 0x46 | offset32 | 5B |
| CALL | 0x47 | offset32 | 5B |
| RET | 0x48 | - | 1B |
| INT | 0x49 | num8 | 2B |
| PRINT | 0x50 | reg/imm | 1-5B |
| INPUT | 0x51 | reg | 2B |
| PRINTS | 0x52 | addr32 | 5B |
| SYSCALL | 0xF0 | id8 | 2B |
| DEBUG | 0xF1 | level8 | 2B |

---

## 符号表格式

用于调试和动态链接。

### 条目结构 (变长)

| 字段 | 大小 | 说明 |
|------|------|------|
| flags | 1 | 符号类型和属性 |
| name_len | 1 | 名称长度 |
| name | name_len | 符号名称 |
| value | 4 | 符号值 (地址或偏移) |

### 标志位 (flags)

| 值 | 类型 | 说明 |
|----|------|------|
| 0x01 | FUNCTION | 函数符号 |
| 0x02 | GLOBAL | 全局可见 |
| 0x04 | LOCAL | 局部符号 |
| 0x08 | IMPORTED | 外部导入 |
| 0x10 | EXPORTED | 导出符号 |

---

## 示例编码

### 源程序
```
LOADIMM R0, 42
ADD R1, R0, 1
PRINT R1
HALT
```

### 字节码 (十六进制)

```
; 文件头 (简化)
46 53 47 42    ; Magic "FSGB"
01 00          ; Version 1.0
00 00          ; Flags
00 00 00 24    ; Entry = 0x24
10 00 00 00    ; Text size = 16 bytes
00 00 00 00    ; Data size = 0
00 00 00 00    ; Rodata size = 0
00 00 00 00    ; Symbol count = 0
00 00 00 00    ; Debug size = 0
XX XX XX XX    ; Checksum

; 代码段 (从偏移 0x24 开始)
12 00 2A      ; LOADIMM R0, 42 (2A = 42)
20 01 00 01   ; ADD R1, R0, R1 (R1=0)
50 01         ; PRINT R1
01            ; HALT
```

---

## 加载流程

### 1. 文件验证

```python
def validate_header(f):
    magic = read_bytes(f, 4)
    if magic != b'FSGB':
        raise InvalidMagicError()
    
    version = read_uint16(f)
    if version > MAX_SUPPORTED_VERSION:
        raise UnsupportedVersionError()
    
    checksum = read_uint32(f, offset=0x1C)
    data = read_all(f)
    if crc32(data) != checksum:
        raise ChecksumError()
```

### 2. 内存布局

```python
def load_bytecode(f):
    # 分配内存
    memory = bytearray(64 * 1024)  # 64KB 默认
    
    # 加载数据段
    data_offset = read_uint32(header, 0x10)
    data_size = read_uint32(header, 0x14)
    memory[DATA_BASE:data_size] = read_bytes(f, data_size)
    
    # 加载代码段
    text_offset = 0x24  # 固定偏移
    text_size = read_uint32(header, 0x0C)
    memory[TEXT_BASE:text_size] = read_bytes(f, text_size)
    
    # 解析符号表
    symbols = parse_symbol_table(f)
    
    return LoadedProgram(memory, symbols)
```

---

## 校验和计算

使用 CRC32 算法：

```python
import zlib

def calculate_checksum(data: bytes) -> int:
    """计算文件的 CRC32 校验和"""
    return zlib.crc32(data) & 0xFFFFFFFF
```

注意：校验和计算时，该字段位置填0。

---

## 扩展机制

### 版本兼容性

- 主版本号不兼容
- 次版本号向前兼容

### 自定义指令

操作码 0x60-0xEF 保留给用户自定义。

### 段类型扩展

新的段类型可通过扩展标志位实现。

---

*文档版本: 1.0*  
*最后更新: 2024*
