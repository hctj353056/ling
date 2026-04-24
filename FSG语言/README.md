# FSG 语言与虚拟机

> 蜉熵阁 - 灵镜(ling)原生脚本执行系统

---

## 概述

FSG (Fuyang Scripting & virtual machine, Generic) 是一种极简的类汇编脚本语言和虚拟机，设计用于让 AI agent (ling/灵镜) 能够原生生成和执行脚本。

### 设计目标

1. **极简性**: ~30条核心指令，易于学习和实现
2. **可读性**: 类汇编语法，人类可写可读
3. **通用性**: Python/C/FSG 皆可实现
4. **ling适配**: 预留 Python 调用接口

### 当前状态

✅ 核心功能已完成：
- 指令集定义（34条指令）
- 汇编语法规范（BNF描述）
- 字节码格式定义（FSGB文件格式）
- Python虚拟机实现
- 示例程序
- 自举支持
- CLI命令行界面

---

## 目录结构

```
FSG语言/
├── simple_vm.py              # Python虚拟机（含CLI）
├── assembler.fsg              # 自举汇编器源码
├── assembler.fsgb            # 自举汇编器字节码
├── bootstrap_test.fsg        # 自举验证测试
├── bootstrap_verify.py       # 自举验证脚本
├── vm_instruction_set.md     # 指令集完整设计
├── assembler_spec.md        # 汇编语法规范
├── bytecode_format.md        # 字节码格式定义
├── README.md                 # 本文件
├── 001.fsg                   # 旧版FSG示例（兼容中）
└── examples/                 # 示例程序
    ├── hello.fsg             # Hello World
    ├── fib.fsg               # 斐波那契数列
    ├── factorial.fsg         # 阶乘计算
    ├── bubblesort.fsg        # 冒泡排序
    └── gcd.fsg               # 最大公约数
```

---

## 命令行用法

```bash
# 帮助信息
python simple_vm.py --help

# 版本信息
python simple_vm.py --version

# REPL交互模式
python simple_vm.py

# 编译并执行
python simple_vm.py program.fsg

# 仅编译
python simple_vm.py -c program.fsg

# 显示反汇编
python simple_vm.py -d program.fsg

# 指定输出文件
python simple_vm.py -o out.fsgb program.fsg

# 执行字节码
python simple_vm.py program.fsgb

# 快捷运行（fsg{...}语法）
python simple_vm.py "fsg{examples/hello.fsg}"
python simple_vm.py "fsg{assembler.fsg}"
```

---

## Python API

```python
from simple_vm import FSGVM, Assembler

# 方式1: 从汇编源码生成并执行
asm = """
LOADIMM R0, 42
PRINT R0
HALT
"""
vm = FSGVM()
vm.load_bytecode(vm.generate_bytecode(asm))
vm.run()  # 输出: 42

# 方式2: 注册原生函数
def my_func(args):
    print("Native function called!")
    return 100

vm.register_native_function("my_func", my_func)

# 方式3: ling专用 - 直接执行字节码
bytecode = vm.generate_bytecode(asm_source)
vm.load_bytecode(bytecode)
vm.run()
```

---

## 自举验证

```bash
# 运行自举验证测试
python bootstrap_verify.py
```

输出应显示：
- assembler.fsg 编译成功 -> assembler.fsgb
- assembler.fsgb 运行成功
- bootstrap_test.fsg 编译+运行成功

---

## 指令集速查

| 类别 | 指令 | 说明 |
|------|------|------|
| **数据传输** | LOAD, STORE, LOADIMM, PUSH, POP, MOV | 寄存器/内存数据交换 |
| **算术运算** | ADD, SUB, MUL, DIV, NEG, MOD | 整数算术运算 |
| **比较逻辑** | CMP, AND, OR, XOR, NOT, SHL, SHR | 比较和位操作 |
| **控制流** | JMP, JE, JNE, JG, JGE, JL, JLE, CALL, RET | 跳转和函数调用 |
| **I/O** | PRINT, INPUT, PRINTS | 输入输出 |
| **系统** | HALT, NOP, SYSCALL, DEBUG | 程序控制 |

---

## 扩展计划

- [x] 基本指令集 (34条)
- [x] Python 实现原型
- [x] 标签和跳转的完整支持
- [x] 字符串操作 (PRINTS)
- [x] 自举支持
- [x] CLI命令行界面
- [ ] 函数调用机制
- [ ] 浮点运算支持
- [ ] C 语言实现
- [ ] 在线汇编/执行器

---

*蜉熵阁 - 灵镜原生脚本系统*
