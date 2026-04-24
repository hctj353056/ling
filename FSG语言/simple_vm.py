#!/usr/bin/env python3
"""
FSG 虚拟机 - Python 实现
蜉熵阁 - 灵镜(ling)原生脚本执行系统

功能:
- 汇编器: 解析 .fsg 汇编文件
- 虚拟机: 执行 .fsgb 字节码文件
- REPL: 交互式执行
- ling接口: 预留的Python调用接口
"""

import struct
import sys
import os
from typing import Callable, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import IntEnum
import zlib

# ==================== 常量定义 ====================

class OpCode(IntEnum):
    """操作码定义"""
    NOP = 0x00
    HALT = 0x01
    
    LOAD = 0x10
    STORE = 0x11
    LOADIMM = 0x12
    PUSH = 0x13
    POP = 0x14
    MOV = 0x15
    
    ADD = 0x20
    SUB = 0x21
    MUL = 0x22
    DIV = 0x23
    NEG = 0x24
    MOD = 0x25
    
    CMP = 0x30
    AND = 0x31
    OR = 0x32
    XOR = 0x33
    NOT = 0x34
    SHL = 0x35
    SHR = 0x36
    
    JMP = 0x40
    JE = 0x41
    JNE = 0x42
    JG = 0x43
    JGE = 0x44
    JL = 0x45
    JLE = 0x46
    CALL = 0x47
    RET = 0x48
    INT = 0x49
    
    PRINT = 0x50
    INPUT = 0x51
    PRINTS = 0x52
    
    SYSCALL = 0xF0
    DEBUG = 0xF1

# 寄存器映射
REG_MAP = {'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7}
REG_NAMES = {v: k for k, v in REG_MAP.items()}

# 内存配置
MEMORY_SIZE = 64 * 1024  # 64KB
STACK_BASE = 0xF000
HEAP_BASE = 0x8000

# 文件魔数
FSGB_MAGIC = b'FSGB'
FSGB_VERSION = 0x0100


# ==================== 数据结构 ====================

@dataclass
class VMState:
    """虚拟机状态"""
    registers: List[int] = field(default_factory=lambda: [0] * 8)
    pc: int = 0
    sp: int = STACK_BASE
    bp: int = STACK_BASE
    memory: bytearray = field(default_factory=lambda: bytearray(MEMORY_SIZE))
    
    # 标志位
    zf: bool = False  # 零标志
    sf: bool = False  # 符号标志
    cf: bool = False  # 进位标志
    of: bool = False  # 溢出标志
    
    # 执行控制
    running: bool = True
    exit_code: int = 0


@dataclass
class Symbol:
    """符号表条目"""
    name: str
    value: int
    is_function: bool = False
    is_global: bool = False


@dataclass 
class LoadedProgram:
    """加载的程序"""
    state: VMState
    entry_point: int = 0
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    native_functions: Dict[str, Callable] = field(default_factory=dict)
    rodata_offset: int = 0


# ==================== 汇编器 ====================

class Assembler:
    """FSG汇编器"""
    
    def __init__(self):
        self.labels: Dict[str, int] = {}
        self.pending_labels: Dict[str, List[Tuple[int, int]]] = {}  # 标签 -> [(地址, 位置)]
        self.current_address = 0
        self.output: List[int] = []
        self.symbols: List[Symbol] = []
        
        # 字符串常量
        self.strings: Dict[str, int] = {}
        self.rodata: List[int] = []
        
    def assemble(self, source: str) -> bytes:
        """将汇编源码编译为字节码"""
        lines = source.strip().split('\n')
        
        # 第一遍：收集标签
        self._first_pass(lines)
        
        # 第二遍：生成代码
        self._second_pass(lines)
        
        # 生成字节码文件
        return self._generate_bytecode()
    
    def _first_pass(self, lines: List[str]):
        """第一遍：收集标签定义"""
        address = 0
        rodata_address = 0x1000  # rodata 起始地址
        in_rodata = False
        in_data = False
        
        for line in lines:
            line = self._clean_line(line)
            if not line:
                continue
            
            # 检测段切换
            if line == '.SECTION .RODATA' or line == '.SECTION .rodata':
                in_rodata = True
                in_data = False
                continue
            elif line == '.SECTION .DATA' or line == '.SECTION .data':
                in_rodata = False
                in_data = True
                continue
            elif line == '.SECTION .TEXT' or line == '.SECTION .text':
                in_rodata = False
                in_data = False
                continue
            
            # 处理标签定义
            if ':' in line and not line.startswith('.'):
                label_name = line.split(':')[0].strip()
                if in_rodata:
                    self.labels[label_name] = rodata_address
                elif in_data:
                    self.labels[label_name] = address  # TODO: data段处理
                else:
                    self.labels[label_name] = address
                line = line.split(':', 1)[1].strip()
                if not line:
                    continue
            
            # 计算指令/数据长度
            if line.startswith('.STR'):
                content = line[4:].strip().strip('"')
                rodata_address += len(content) + 1
            elif line.startswith('.DW'):
                values = self._parse_immediate_list(line[3:])
                if in_rodata:
                    rodata_address += len(values) * 4
                else:
                    address += len(values) * 4
            else:
                inst = self._parse_instruction(line)
                if inst:
                    address += inst[2]  # 指令长度
    
    def _second_pass(self, lines: List[str]):
        """第二遍：生成字节码"""
        self.current_address = 0
        rodata_addr = 0x1000  # rodata 起始地址
        in_rodata = False
        in_data = False
        
        for line in lines:
            line = self._clean_line(line)
            if not line:
                continue
            
            # 检测段切换
            if line == '.SECTION .RODATA' or line == '.SECTION .rodata':
                in_rodata = True
                in_data = False
                continue
            elif line == '.SECTION .DATA' or line == '.SECTION .data':
                in_rodata = False
                in_data = True
                continue
            elif line == '.SECTION .TEXT' or line == '.SECTION .text':
                in_rodata = False
                in_data = False
                continue
            
            # 处理标签 - 只更新代码段的标签，rodata标签已在第一遍设置
            if ':' in line and not line.startswith('.'):
                label_name = line.split(':')[0].strip()
                if not in_rodata:
                    # 只有非rodata段的标签需要更新位置
                    self.labels[label_name] = self.current_address
                line = line.split(':', 1)[1].strip()
                if not line:
                    continue
            
            # 处理汇编指令
            if line.startswith('.STR'):
                # 字符串定义
                content = line[4:].strip().strip('"')
                self.strings[content] = rodata_addr
                for ch in content + '\0':
                    self.rodata.append(ord(ch))
                rodata_addr += len(content) + 1
                continue
                
            elif line.startswith('.DW'):
                # 字定义
                values = self._parse_immediate_list(line[3:])
                for val in values:
                    self.output.append(val & 0xFF)
                    self.output.append((val >> 8) & 0xFF)
                    self.output.append((val >> 16) & 0xFF)
                    self.output.append((val >> 24) & 0xFF)
                if in_rodata:
                    rodata_addr += len(values) * 4
                else:
                    self.current_address += len(values) * 4
                continue
                
            elif line.startswith('.GLOBAL'):
                # 全局符号
                name = line.split()[1]
                self.symbols.append(Symbol(name, 0, is_function=True, is_global=True))
                continue
                
            elif line.startswith('.SECTION') or line.startswith('.ADDR'):
                continue
            
            # 处理普通指令
            inst = self._parse_instruction(line)
            if inst:
                opcode, operands, length = inst
                self.output.append(opcode)
                # 提取原始参数用于标签解析
                parts = [p.strip() for p in line.replace(',', ' ').split()]
                arg_list = parts[1:] if len(parts) > 1 else []
                
                # 分离寄存器操作数和立即数操作数
                # operands格式：[reg1, reg2, ...] 或 [reg, imm] 或 [imm, ...]
                # 第一个操作数通常是寄存器（0-7），后面的可能是立即数
                imm_count = 0
                for i, op in enumerate(operands):
                    if isinstance(op, int):
                        # 检查是否是标签引用（-1）
                        if op == -1:
                            # 查找标签名
                            for arg_str in arg_list:
                                if arg_str in self.labels:
                                    addr = self.labels[arg_str]
                                    self.current_address += self._encode_imm(addr, self.output)
                                    imm_count += 1
                                    break
                            else:
                                # 标签未定义，使用当前地址
                                self.current_address += self._encode_imm(self.current_address, self.output)
                                imm_count += 1
                        elif 0 <= op <= 7 and i == 0:
                            # 这是一个寄存器编码
                            self.output.append(op)
                            self.current_address += 1
                        else:
                            # 这是一个立即数
                            self.current_address += self._encode_imm(op, self.output)
                            imm_count += 1
                self.current_address += 1  # opcode byte
    
    def _generate_bytecode(self) -> bytes:
        """生成 FSGB 格式字节码"""
        # 合并 rodata 到输出
        rodata_offset = len(self.output)
        self.output.extend(self.rodata)
        
        # 构建文件头
        header = bytearray(32)
        header[0:4] = FSGB_MAGIC
        struct.pack_into('>H', header, 4, FSGB_VERSION)
        struct.pack_into('>I', header, 8, 0x20)  # 入口点
        struct.pack_into('>I', header, 12, len(self.output) - len(self.rodata))  # text_size
        struct.pack_into('>I', header, 16, 0)  # data_size
        struct.pack_into('>I', header, 20, len(self.rodata))  # rodata_size
        
        # 计算校验和
        checksum_data = bytearray(self.output)
        checksum_data[0x1C:0x20] = b'\x00\x00\x00\x00'
        checksum = zlib.crc32(checksum_data) & 0xFFFFFFFF
        struct.pack_into('>I', header, 28, checksum)
        
        return bytes(header) + bytes(self.output)
    
    def _clean_line(self, line: str) -> str:
        """清理一行代码"""
        # 移除注释
        if ';' in line:
            line = line.split(';')[0]
        return line.strip()
    
    def _parse_instruction(self, line: str) -> Optional[Tuple[int, List, int]]:
        """解析指令，返回 (opcode, operands, length)"""
        parts = [p.strip() for p in line.replace(',', ' ').split()]
        if not parts:
            return None
        
        mnemonic = parts[0].upper()
        args = parts[1:]
        
        handlers = {
            'NOP': (OpCode.NOP, [], 1),
            'HALT': (OpCode.HALT, [], 1),
            'RET': (OpCode.RET, [], 1),
        }
        
        if mnemonic in handlers:
            return handlers[mnemonic]
        
        if mnemonic == 'MOV':
            if len(args) == 2:
                return (OpCode.MOV, [REG_MAP[args[0]], REG_MAP[args[1]]], 3)
        
        elif mnemonic == 'LOADIMM':
            if len(args) == 2:
                return (OpCode.LOADIMM, [REG_MAP[args[0]], self._parse_value(args[1])], 5)  # 5字节: opcode + reg + 4字节imm
        
        elif mnemonic == 'LOAD':
            if len(args) == 2:
                reg = REG_MAP[args[0]]
                addr = self._parse_address(args[1])
                return (OpCode.LOAD, [reg, addr], 6)
        
        elif mnemonic == 'STORE':
            if len(args) == 2:
                addr = self._parse_address(args[0])
                reg = REG_MAP[args[1]]
                return (OpCode.STORE, [addr, reg], 6)
        
        elif mnemonic == 'PUSH':
            if len(args) == 1:
                return (OpCode.PUSH, [REG_MAP[args[0]]], 2)
        
        elif mnemonic == 'POP':
            if len(args) == 1:
                return (OpCode.POP, [REG_MAP[args[0]]], 2)
        
        elif mnemonic == 'ADD':
            if len(args) == 3:
                if args[2] in REG_MAP:
                    return (OpCode.ADD, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
                else:
                    # 支持 ADD Rd, Rs, imm
                    return (OpCode.ADD, [REG_MAP[args[0]], REG_MAP[args[1]], self._parse_value(args[2])], 6)
        
        elif mnemonic == 'SUB':
            if len(args) == 3:
                if args[2] in REG_MAP:
                    return (OpCode.SUB, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
                else:
                    # 支持 SUB Rd, Rs, imm
                    return (OpCode.SUB, [REG_MAP[args[0]], REG_MAP[args[1]], self._parse_value(args[2])], 6)
        
        elif mnemonic == 'MUL':
            if len(args) == 3:
                return (OpCode.MUL, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
        
        elif mnemonic == 'DIV':
            if len(args) == 3:
                return (OpCode.DIV, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
        
        elif mnemonic == 'NEG':
            if len(args) == 1:
                return (OpCode.NEG, [REG_MAP[args[0]]], 2)
        
        elif mnemonic == 'MOD':
            if len(args) == 3:
                return (OpCode.MOD, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
        
        elif mnemonic == 'CMP':
            if len(args) == 2:
                if args[1] in REG_MAP:
                    return (OpCode.CMP, [REG_MAP[args[0]], REG_MAP[args[1]]], 3)
                else:
                    # 支持 CMP R, imm
                    return (OpCode.CMP, [REG_MAP[args[0]], self._parse_value(args[1])], 6)
        
        elif mnemonic in ('JMP', 'JE', 'JNE', 'JG', 'JGE', 'JL', 'JLE'):
            opcode_map = {'JMP': OpCode.JMP, 'JE': OpCode.JE, 'JNE': OpCode.JNE,
                         'JG': OpCode.JG, 'JGE': OpCode.JGE, 'JL': OpCode.JL, 'JLE': OpCode.JLE}
            if len(args) == 1:
                return (opcode_map[mnemonic], [args[0]], 2)
        
        elif mnemonic == 'CALL':
            if len(args) == 1:
                return (OpCode.CALL, [args[0]], 2)
        
        elif mnemonic == 'PRINT':
            if len(args) == 1:
                return (OpCode.PRINT, [REG_MAP[args[0]]], 2)
        
        elif mnemonic == 'INPUT':
            if len(args) == 1:
                return (OpCode.INPUT, [REG_MAP[args[0]]], 2)
        
        elif mnemonic == 'PRINTS':
            if len(args) == 1:
                # PRINTS 接受标签或地址
                addr = self._parse_address(args[0])
                return (OpCode.PRINTS, [addr], 6)
        
        return None
    
    def _parse_value(self, s: str) -> int:
        """解析数值"""
        s = s.strip()
        if s.startswith('0x'):
            return int(s, 16)
        elif s.startswith('0b'):
            return int(s, 2)
        elif s.startswith('0o'):
            return int(s, 8)
        else:
            # 可能是标签引用 - 返回特殊标记，在第二遍解析
            if s.isidentifier():
                # 检查是否是已知标签
                if s in self.labels:
                    return self.labels[s]
                # 标签未定义，标记为待解析
                return -1  # 特殊标记，表示标签
            return int(s)
    
    def _parse_address(self, s: str) -> int:
        """解析地址"""
        s = s.strip()
        if s.startswith('[') and s.endswith(']'):
            inner = s[1:-1].strip()
            if inner in REG_MAP:
                return -1  # 间接寻址标记
            return self._parse_value(inner)
        return self._parse_value(s)
    
    def _encode_imm(self, value: int, output: List[int]) -> int:
        """编码立即数，返回编码的字节数
        统一使用4字节大端序编码，确保与虚拟机指令长度一致
        """
        output.append((value >> 24) & 0xFF)
        output.append((value >> 16) & 0xFF)
        output.append((value >> 8) & 0xFF)
        output.append(value & 0xFF)
        return 4
    
    def _parse_immediate_list(self, s: str) -> List[int]:
        """解析立即数列表（如 .DW 1, 2, 3）"""
        values = []
        for part in s.split(','):
            part = part.strip()
            if part:
                values.append(self._parse_value(part))
        return values


# ==================== 虚拟机 ====================

class FSGVM:
    """
    FSG 虚拟机
    
    预留的 ling 适配接口:
    - load_bytecode(): 加载字节码
    - register_native_function(): 注册原生函数
    - run(): 执行
    - generate_bytecode(): 从汇编生成字节码
    """
    
    def __init__(self, memory_size: int = MEMORY_SIZE):
        self.state = VMState()
        self.state.memory = bytearray(memory_size)
        self.state.sp = memory_size - 64  # 预留栈空间
        self.state.bp = self.state.sp
        
        self.program: Optional[LoadedProgram] = None
        self.native_functions: Dict[int, Callable] = {}
        self.labels: Dict[str, int] = {}
        
        # 调试模式
        self.debug = False
        
        # 注册内置函数
        self._register_builtins()
    
    def _register_builtins(self):
        """注册内置函数"""
        self.native_functions[0x01] = self._builtin_print
        self.native_functions[0x02] = self._builtin_input
    
    def _builtin_print(self, args: List[int]) -> int:
        """内置打印函数"""
        print(args[0] if args else 0)
        return 0
    
    def _builtin_input(self, args: List[int]) -> int:
        """内置输入函数"""
        try:
            return int(input())
        except:
            return 0
    
    # ==================== ling 适配接口 ====================
    
    def load_bytecode(self, bytecode: bytes):
        """加载字节码 - ling 可调用"""
        self.program = self._load_bytecode_from_bytes(bytecode)
        self.state = self.program.state
        self.labels = {s.name: s.value for s in self.program.symbols}
        for name, func in self.program.native_functions.items():
            self.native_functions[hash(name) & 0xFF] = func
    
    def load_bytecode_file(self, filepath: str):
        """从文件加载字节码"""
        with open(filepath, 'rb') as f:
            self.load_bytecode(f.read())
    
    def register_native_function(self, name: str, func: Callable):
        """注册原生函数供脚本调用 - ling 可调用"""
        func_id = hash(name) & 0xFF
        self.native_functions[func_id] = func
        if self.program:
            self.program.native_functions[name] = func
    
    def generate_bytecode(self, asm_source: str) -> bytes:
        """从汇编源码生成字节码 - ling 可调用"""
        assembler = Assembler()
        return assembler.assemble(asm_source)
    
    def run(self, entry: Optional[int] = None) -> int:
        """执行虚拟机 - ling 可调用"""
        if not self.program:
            raise RuntimeError("No program loaded")
        
        # 使用程序入口点或指定的入口
        start_pc = entry if entry is not None else self.program.entry_point
        self.state.pc = start_pc
        self.state.running = True
        
        while self.state.running and self.state.pc < len(self.state.memory):
            try:
                self._execute_instruction()
            except Exception as e:
                if self.debug:
                    print(f"Error at PC={self.state.pc}: {e}")
                raise
        
        return self.state.exit_code
    
    def reset(self):
        """重置虚拟机状态"""
        self.state = VMState()
        self.state.memory = bytearray(MEMORY_SIZE)
        self.state.sp = MEMORY_SIZE - 64
        self.state.bp = self.state.sp
    
    # ==================== 内部方法 ====================
    
    def _load_bytecode_from_bytes(self, bytecode: bytes) -> LoadedProgram:
        """从字节数组加载程序"""
        # 验证魔数
        if bytecode[:4] != FSGB_MAGIC:
            raise ValueError(f"Invalid magic number: {bytecode[:4]}")
        
        # 解析文件头
        version = struct.unpack('>H', bytecode[4:6])[0]
        text_size = struct.unpack('>I', bytecode[12:16])[0]
        rodata_size = struct.unpack('>I', bytecode[20:24])[0]
        
        # 加载内存
        state = VMState()
        state.memory = bytearray(MEMORY_SIZE)
        state.sp = MEMORY_SIZE - 64
        state.bp = state.sp
        
        # 复制代码到内存
        text_offset = 0x20
        state.memory[0:text_size] = bytecode[text_offset:text_offset + text_size]
        
        # 复制 rodata
        rodata_offset = text_offset + text_size
        state.memory[0x1000:0x1000 + rodata_size] = bytecode[rodata_offset:rodata_offset + rodata_size]
        
        program = LoadedProgram(state=state, entry_point=0)  # 入口点 = 0
        
        return program
    
    def _execute_instruction(self):
        """执行单条指令"""
        opcode = self.state.memory[self.state.pc]
        self.state.pc += 1
        
        if self.debug:
            print(f"PC={self.state.pc-1:04X} OP={opcode:02X}", end=' ')
        
        # 指令分派
        handlers = {
            OpCode.NOP: self._op_nop,
            OpCode.HALT: self._op_halt,
            OpCode.LOAD: self._op_load,
            OpCode.STORE: self._op_store,
            OpCode.LOADIMM: self._op_loadimm,
            OpCode.PUSH: self._op_push,
            OpCode.POP: self._op_pop,
            OpCode.MOV: self._op_mov,
            OpCode.ADD: self._op_add,
            OpCode.SUB: self._op_sub,
            OpCode.MUL: self._op_mul,
            OpCode.DIV: self._op_div,
            OpCode.NEG: self._op_neg,
            OpCode.MOD: self._op_mod,
            OpCode.CMP: self._op_cmp,
            OpCode.JMP: self._op_jmp,
            OpCode.JE: self._op_je,
            OpCode.JNE: self._op_jne,
            OpCode.JG: self._op_jg,
            OpCode.JGE: self._op_jge,
            OpCode.JL: self._op_jl,
            OpCode.JLE: self._op_jle,
            OpCode.CALL: self._op_call,
            OpCode.RET: self._op_ret,
            OpCode.PRINT: self._op_print,
            OpCode.INPUT: self._op_input,
            OpCode.PRINTS: self._op_prints,
            OpCode.SYSCALL: self._op_syscall,
        }
        
        handler = handlers.get(opcode)
        if handler:
            handler()
        else:
            if self.debug:
                print(f"Unknown opcode: {opcode}")
    
    # ==================== 指令实现 ====================
    
    def _read_reg(self) -> int:
        """读取寄存器"""
        reg = self.state.memory[self.state.pc]
        self.state.pc += 1
        return reg
    
    def _read_imm8(self) -> int:
        """读取8位立即数"""
        val = self.state.memory[self.state.pc]
        self.state.pc += 1
        if val & 0x80:
            val = val - 256
        return val
    
    def _read_imm32(self) -> int:
        """读取32位立即数"""
        val = struct.unpack('>i', bytes(self.state.memory[self.state.pc:self.state.pc+4]))[0]
        self.state.pc += 4
        return val
    
    def _read_addr32(self) -> int:
        """读取32位地址"""
        val = struct.unpack('>I', bytes(self.state.memory[self.state.pc:self.state.pc+4]))[0]
        self.state.pc += 4
        return val
    
    def _op_nop(self):
        """空操作"""
        if self.debug:
            print("NOP")
    
    def _op_halt(self):
        """终止"""
        if self.debug:
            print("HALT")
        self.state.running = False
    
    def _op_load(self):
        """LOAD R, [addr]"""
        reg = self._read_reg()
        addr = self._read_addr32()
        value = struct.unpack('>i', bytes(self.state.memory[addr:addr+4]))[0]
        self.state.registers[reg] = value
        if self.debug:
            print(f"LOAD R{reg}, [{addr:04X}] = {value}")
    
    def _op_store(self):
        """STORE [addr], R"""
        addr = self._read_addr32()
        reg = self._read_reg()
        value = self.state.registers[reg]
        struct.pack_into('>i', self.state.memory, addr, value)
        if self.debug:
            print(f"STORE [{addr:04X}], R{reg} = {value}")
    
    def _op_loadimm(self):
        """LOADIMM R, imm"""
        reg = self._read_reg()
        # 读取4字节立即数（大端序）
        value = self._read_imm32()
        self.state.registers[reg] = value
        if self.debug:
            print(f"LOADIMM R{reg}, {value}")
    
    def _op_push(self):
        """PUSH R"""
        reg = self._read_reg()
        self.state.sp -= 4
        struct.pack_into('>i', self.state.memory, self.state.sp, self.state.registers[reg])
        if self.debug:
            print(f"PUSH R{reg} = {self.state.registers[reg]}")
    
    def _op_pop(self):
        """POP R"""
        reg = self._read_reg()
        value = struct.unpack('>i', bytes(self.state.memory[self.state.sp:self.state.sp+4]))[0]
        self.state.sp += 4
        self.state.registers[reg] = value
        if self.debug:
            print(f"POP R{reg} = {value}")
    
    def _op_mov(self):
        """MOV Rdest, Rsrc"""
        dest = self._read_reg()
        src = self._read_reg()
        self.state.registers[dest] = self.state.registers[src]
        if self.debug:
            print(f"MOV R{dest}, R{src} = {self.state.registers[src]}")
    
    def _op_add(self):
        """ADD Rd, Ra, Rb"""
        rd = self._read_reg()
        ra = self._read_reg()
        rb = self._read_reg()
        result = self.state.registers[ra] + self.state.registers[rb]
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"ADD R{rd}, R{ra}, R{rb} = {result}")
    
    def _op_sub(self):
        """SUB Rd, Ra, Rb"""
        rd = self._read_reg()
        ra = self._read_reg()
        rb = self._read_reg()
        result = self.state.registers[ra] - self.state.registers[rb]
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"SUB R{rd}, R{ra}, R{rb} = {result}")
    
    def _op_mul(self):
        """MUL Rd, Ra, Rb"""
        rd = self._read_reg()
        ra = self._read_reg()
        rb = self._read_reg()
        result = self.state.registers[ra] * self.state.registers[rb]
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"MUL R{rd}, R{ra}, R{rb} = {result}")
    
    def _op_div(self):
        """DIV Rd, Ra, Rb"""
        rd = self._read_reg()
        ra = self._read_reg()
        rb = self._read_reg()
        if self.state.registers[rb] == 0:
            self.state.cf = True
            if self.debug:
                print(f"DIV R{rd}, R{ra}, R{rb} - DIV BY ZERO")
            return
        result = self.state.registers[ra] // self.state.registers[rb]
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"DIV R{rd}, R{ra}, R{rb} = {result}")
    
    def _op_neg(self):
        """NEG R"""
        reg = self._read_reg()
        self.state.registers[reg] = -self.state.registers[reg]
        self._update_flags(self.state.registers[reg])
        if self.debug:
            print(f"NEG R{reg} = {self.state.registers[reg]}")
    
    def _op_mod(self):
        """MOD Rd, Ra, Rb"""
        rd = self._read_reg()
        ra = self._read_reg()
        rb = self._read_reg()
        if self.state.registers[rb] != 0:
            result = self.state.registers[ra] % self.state.registers[rb]
            self.state.registers[rd] = result
            self._update_flags(result)
            if self.debug:
                print(f"MOD R{rd}, R{ra}, R{rb} = {result}")
    
    def _op_cmp(self):
        """CMP Ra, Rb"""
        ra = self._read_reg()
        rb = self._read_reg()
        result = self.state.registers[ra] - self.state.registers[rb]
        self._update_flags(result)
        if self.debug:
            print(f"CMP R{ra}, R{rb} -> ZF={self.state.zf}, SF={self.state.sf}")
    
    def _resolve_label(self, label: str) -> int:
        """解析标签"""
        if label in self.labels:
            return self.labels[label]
        # 尝试在内存中查找
        addr = 0x20
        # 简化解析：返回标签的哈希值作为地址
        return hash(label) % (len(self.state.memory) - 0x100)
    
    def _op_jmp(self):
        """JMP offset"""
        offset = self._read_imm8()  # 简化为8位偏移
        self.state.pc += offset - 1
        if self.debug:
            print(f"JMP PC+{offset}")
    
    def _op_je(self):
        """JE offset"""
        offset = self._read_imm8()
        if self.state.zf:
            self.state.pc += offset - 1
        if self.debug:
            print(f"JE PC+{offset} (ZF={self.state.zf})")
    
    def _op_jne(self):
        """JNE offset"""
        offset = self._read_imm8()
        if not self.state.zf:
            self.state.pc += offset - 1
        if self.debug:
            print(f"JNE PC+{offset} (ZF={self.state.zf})")
    
    def _op_jg(self):
        """JG offset"""
        offset = self._read_imm8()
        if not self.state.zf and self.state.sf == self.state.of:
            self.state.pc += offset - 1
        if self.debug:
            print(f"JG PC+{offset}")
    
    def _op_jge(self):
        """JGE offset"""
        offset = self._read_imm8()
        if self.state.sf == self.state.of:
            self.state.pc += offset - 1
        if self.debug:
            print(f"JGE PC+{offset}")
    
    def _op_jl(self):
        """JL offset"""
        offset = self._read_imm8()
        if self.state.sf != self.state.of:
            self.state.pc += offset - 1
        if self.debug:
            print(f"JL PC+{offset}")
    
    def _op_jle(self):
        """JLE offset"""
        offset = self._read_imm8()
        if self.state.zf or self.state.sf != self.state.of:
            self.state.pc += offset - 1
        if self.debug:
            print(f"JLE PC+{offset}")
    
    def _op_call(self):
        """CALL offset"""
        offset = self._read_imm8()
        self.state.sp -= 4
        struct.pack_into('>i', self.state.memory, self.state.sp, self.state.pc)
        self.state.pc += offset - 1
        if self.debug:
            print(f"CALL PC+{offset}")
    
    def _op_ret(self):
        """RET"""
        addr = struct.unpack('>i', bytes(self.state.memory[self.state.sp:self.state.sp+4]))[0]
        self.state.sp += 4
        self.state.pc = addr
        if self.debug:
            print(f"RET to {addr:04X}")
    
    def _op_print(self):
        """PRINT R"""
        reg = self._read_reg()
        value = self.state.registers[reg]
        print(value)
        if self.debug:
            print(f"PRINT R{reg} = {value}")
    
    def _op_input(self):
        """INPUT R"""
        reg = self._read_reg()
        try:
            self.state.registers[reg] = int(input())
        except:
            self.state.registers[reg] = 0
        if self.debug:
            print(f"INPUT R{reg}")
    
    def _op_prints(self):
        """PRINTS addr - 输出字符串"""
        addr = self._read_addr32()
        # 从内存地址读取并输出字符串
        output = []
        i = 0
        while True:
            ch = self.state.memory[addr + i]
            if ch == 0:  # null终止
                break
            output.append(chr(ch))
            i += 1
            if i > 1000:  # 防止无限循环
                break
        print(''.join(output), end='')
        if self.debug:
            print(f"PRINTS @{addr:04X} = {''.join(output)}")
    
    def _op_syscall(self):
        """SYSCALL id"""
        func_id = self.state.memory[self.state.pc]
        self.state.pc += 1
        if func_id in self.native_functions:
            self.state.registers[0] = self.native_functions[func_id](
                self.state.registers[1:]
            )
        if self.debug:
            print(f"SYSCALL {func_id:02X}")
    
    def _update_flags(self, result: int):
        """更新标志位"""
        self.state.zf = (result == 0)
        self.state.sf = (result < 0)
        self.state.of = (result > 2**31 - 1 or result < -2**31)


# ==================== REPL ====================

class REPL:
    """交互式解释器"""
    
    def __init__(self):
        self.vm = FSGVM()
        self.assembler = Assembler()
    
    def run(self):
        """运行REPL"""
        print("FSG VM REPL v1.0 - 蜉熵阁")
        print("Commands: .asm, .run, .debug, .reset, .quit")
        print("-" * 40)
        
        buffer = []
        
        while True:
            try:
                line = input(">>> ")
                
                if line.strip() == '.quit':
                    break
                
                elif line.strip() == '.reset':
                    self.vm.reset()
                    buffer = []
                    print("VM reset.")
                
                elif line.strip() == '.debug':
                    self.vm.debug = not self.vm.debug
                    print(f"Debug mode: {'ON' if self.vm.debug else 'OFF'}")
                
                elif line.strip() == '.run':
                    if buffer:
                        bytecode = self.assembler.assemble('\n'.join(buffer))
                        self.vm.load_bytecode(bytecode)
                        self.vm.run()
                        buffer = []
                
                elif line.startswith('.asm'):
                    print(".asm - Enter assembly code (end with .end)")
                    while True:
                        code = input("... ")
                        if code.strip() == '.end':
                            break
                        buffer.append(code)
                
                elif line.strip():
                    buffer.append(line)
                    
            except KeyboardInterrupt:
                print("\nInterrupted.")
                break
            except Exception as e:
                print(f"Error: {e}")


# ==================== 工具函数 ====================

def disassemble(bytecode: bytes, count: int = 20) -> List[str]:
    """反汇编字节码"""
    instructions = []
    pc = 0x20  # 跳过文件头
    
    while pc < len(bytecode) and len(instructions) < count:
        opcode = bytecode[pc]
        pc += 1
        
        mnemonics = {
            0x00: "NOP", 0x01: "HALT",
            0x10: "LOAD", 0x11: "STORE", 0x12: "LOADIMM",
            0x13: "PUSH", 0x14: "POP", 0x15: "MOV",
            0x20: "ADD", 0x21: "SUB", 0x22: "MUL",
            0x23: "DIV", 0x24: "NEG", 0x25: "MOD",
            0x30: "CMP",
            0x40: "JMP", 0x41: "JE", 0x42: "JNE",
            0x47: "CALL", 0x48: "RET",
            0x50: "PRINT", 0x51: "INPUT",
        }
        
        if opcode in mnemonics:
            instructions.append(f"0x{pc-1:04X}: {mnemonics[opcode]}")
        else:
            instructions.append(f"0x{pc-1:04X}: DB 0x{opcode:02X}")
    
    return instructions


# ==================== FSG CLI ====================
FSG_VERSION = "1.0.0"
FSG_NAME = "fsg"

def fsg_help():
    """显示帮助信息"""
    print(f"""
FSG - Fuyang Scripting & virtual machine, Generic
版本 {FSG_VERSION}

用法:
    {FSG_NAME} [选项] [文件]

选项:
    -h, --help      显示此帮助信息
    -v, --version   显示版本信息
    -r, --repl      进入交互式REPL模式
    -d, --disasm    显示反汇编
    -o <文件>       指定输出文件
    -c, --compile   仅编译，不运行

示例:
    {FSG_NAME}                  # 进入REPL模式
    {FSG_NAME} program.fsg       # 编译并执行
    {FSG_NAME} program.fsgb     # 执行字节码
    {FSG_NAME} -d program.fsg   # 编译并显示反汇编
    {FSG_NAME} -o out.fsgb program.fsg  # 编译到指定输出

文件包含语法:
    在.fsg文件中使用: fsg{{file.fsg}} 来包含另一个文件
    示例: 引"/path/to/lib.fsg"

快捷命令:
    fsg{{001.fsg}}               # 运行FSG语言示例
    fsg{{examples/hello.fsg}}    # 运行Hello World示例
""")

def fsg_version():
    """显示版本信息"""
    print(f"FSG 版本 {FSG_VERSION}")
    print("蜉蝣阁 - 灵镜原生脚本系统")

def resolve_fsg_template(path: str, base_dir: str = ".") -> str:
    """解析 fsg{path} 模板语法，返回文件内容"""
    # 移除 fsg{ 和 }
    path = path.strip()
    if path.startswith("fsg{") and path.endswith("}"):
        path = path[4:-1]
    
    # 尝试多种路径
    search_paths = [
        path,
        os.path.join(base_dir, path),
        os.path.join("FSG语言", path),
        os.path.join("FSG语言", "examples", path),
    ]
    
    for try_path in search_paths:
        if os.path.exists(try_path):
            with open(try_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    raise FileNotFoundError(f"找不到文件: {path}")

def preprocess_source(source: str, base_dir: str = ".") -> str:
    """预处理源码，处理 fsg{file} 和 引"file" 语法"""
    lines = source.split('\n')
    result = []
    
    for line in lines:
        # 处理 fsg{file.fsg} 语法
        if 'fsg{' in line:
            import re
            matches = re.findall(r'fsg\{([^}]+)\}', line)
            for match in matches:
                try:
                    content = resolve_fsg_template(match, base_dir)
                    result.append(f"; === 包含文件: {match} ===")
                    result.extend(content.split('\n'))
                    result.append(f"; === 包含结束 ===")
                except FileNotFoundError as e:
                    result.append(f"; 错误: {e}")
            continue
        
        # 处理 引"path" 语法
        if '引"' in line or "引'" in line:
            import re
            # 匹配 引"..." 或 引'...'
            match = re.search(r'引["\']([^"\']+)["\']', line)
            if match:
                path = match.group(1)
                try:
                    content = resolve_fsg_template(path, base_dir)
                    result.append(f"; === 引文件: {path} ===")
                    result.extend(content.split('\n'))
                    result.append(f"; === 引结束 ===")
                    continue  # 不添加原始行
                except FileNotFoundError as e:
                    result.append(f"; 错误: {e}")
        
        result.append(line)
    
    return '\n'.join(result)


# ==================== 主函数 ====================

def main():
    """主函数"""
    import os
    
    # 处理参数
    args = sys.argv[1:]
    
    # 无参数 -> REPL
    if not args:
        repl = REPL()
        repl.run()
        return
    
    # 帮助和版本
    if args[0] in ('-h', '--help', 'help'):
        fsg_help()
        return
    
    if args[0] in ('-v', '--version', 'version'):
        fsg_version()
        return
    
    if args[0] in ('-r', '--repl'):
        repl = REPL()
        repl.run()
        return
    
    # 确定输出目录
    base_dir = os.path.dirname(os.path.abspath(args[-1])) if os.path.exists(args[-1]) else "."
    
    # 处理 fsg{file.fsg} 语法
    filepath = args[-1]
    if filepath.startswith("fsg{") and filepath.endswith("}"):
        filepath = filepath[4:-1]
        # 搜索文件
        for try_path in [filepath, os.path.join("FSG语言", filepath), os.path.join("FSG语言", "examples", filepath)]:
            if os.path.exists(try_path):
                filepath = try_path
                break
        else:
            print(f"错误: 找不到文件 {filepath}")
            return
    
    # 选项处理
    compile_only = '-c' in args or '--compile' in args
    show_disasm = '-d' in args or '--disasm' in args
    output_file = None
    
    if '-o' in args:
        idx = args.index('-o')
        if idx + 1 < len(args):
            output_file = args[idx + 1]
    
    # 确定文件类型并处理
    if os.path.exists(filepath):
        # 检查文件内容来判断类型
        with open(filepath, 'rb') as f:
            header = f.read(32)
        
        # FSGB文件以 "FSGB" 魔数开头
        if header[:4] == b'FSGB':
            # 执行字节码
            vm = FSGVM()
            vm.load_bytecode_file(filepath)
            
            if show_disasm:
                with open(filepath, 'rb') as f:
                    bytecode = f.read()
                print("\n反汇编:")
                for inst in disassemble(bytecode):
                    print(inst)
                print("-" * 40)
            
            vm.run()
            return
        else:
            # 尝试作为源码处理
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    source = f.read()
            except UnicodeDecodeError:
                print(f"错误: 无法解码文件 {filepath}")
                return
            
            # 预处理
            source = preprocess_source(source, os.path.dirname(os.path.abspath(filepath)))
            
            # 汇编
            assembler = Assembler()
            bytecode = assembler.assemble(source)
            
            # 确定输出文件
            if output_file:
                output_path = output_file
            else:
                output_path = filepath.replace('.fsg', '.fsgb')
            
            with open(output_path, 'wb') as f:
                f.write(bytecode)
            
            print(f"✓ 编译成功: {filepath} -> {output_path} ({len(bytecode)} bytes)")
            
            if compile_only:
                return
            
            # 执行字节码
            vm = FSGVM()
            vm.load_bytecode(bytecode)
            
            if show_disasm:
                print("\n反汇编:")
                for inst in disassemble(bytecode):
                    print(inst)
                print("-" * 40)
            
            vm.run()
            return
    
    # 未知参数
    print(f"错误: 未知参数或文件不存在: {filepath}")
    print("使用 'fsg --help' 查看帮助")


if __name__ == '__main__':
    main()
