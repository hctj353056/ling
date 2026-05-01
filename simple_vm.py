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
    MOD = 0x25
    CMP = 0x30
    JMP = 0x40
    JE = 0x41
    JNE = 0x42
    JG = 0x43
    JGE = 0x44
    JL = 0x45
    JLE = 0x46
    CALL = 0x47
    RET = 0x48
    PRINT = 0x50
    INPUT = 0x51
    PRINTS = 0x52
    
    SHL = 0x35
    SHR = 0x36

REG_MAP = {
    'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3,
    'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7
}
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

@dataclass
class LoadedProgram:
    """加载的程序"""
    magic: bytes
    version: int
    entry_point: int
    text_size: int
    data_size: int
    rodata_size: int
    bss_size: int
    entry_addr: int
    flags: int
    

# ==================== 汇编器实现 ====================

class Assembler:
    """FSG 汇编器"""
    def __init__(self):
        self.labels: Dict[str, int] = {}
        self.strings: Dict[str, int] = {}
        self.output: List[int] = []
        self.rodata: List[int] = []
        self.rodata_offset: int = 0
        self.symbols: List[Dict[str, Any]] = []
        self.current_address: int = 0
    
    def assemble(self, source: str) -> bytes:
        """汇编源代码为字节码"""
        lines = [line.rstrip('\r\n') for line in source.split('\n')]
        
        # 第一遍扫描：计算地址和标签
        self._first_pass(lines)
        
        # 第二遍扫描：生成字节码
        self._second_pass(lines)
        
        # 生成最终字节码
        return self._generate_bytecode()
    
    def _first_pass(self, lines: List[str]):
        """第一遍扫描：计算地址和标签"""
        self.labels = {}
        address = 0
        rodata_address = 0x1000
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
                    self.labels[label_name] = address
                else:
                    self.labels[label_name] = address
                line = line.split(':', 1)[1].strip()
                if not line:
                    continue
            
            if line.startswith('.STR'):
                content = line[4:].strip().strip('"')
                rodata_address += len(content) + 1  # +1 for null terminator
                continue
            elif line.startswith('.DW'):
                values = self._parse_immediate_list(line[3:])
                if in_rodata:
                    rodata_address += len(values) * 4
                else:
                    address += len(values) * 4
                continue
            else:
                inst = self._parse_instruction(line)
                if inst:
                    address += inst[2]
    
    def _second_pass(self, lines: List[str]):
        """第二遍扫描：生成字节码"""
        self.output = []
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
            
            if ':' in line and not line.startswith('.'):
                label_name = line.split(':')[0].strip()
                if not in_rodata:
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
                name = line.split()[1]
                self.symbols.append({'name': name, 'addr': 0, 'is_function': True, 'is_global': True})
                continue
                
            elif line.startswith('.SECTION') or line.startswith('.ADDR'):
                continue
            
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
                            for arg_str in arg_list:
                                # 检查是否为寄存器名称
                                if arg_str.strip() in REG_MAP:
                                    reg_num = REG_MAP[arg_str.strip()]
                                    # 对于间接寻址，编码寄存器编号作为特殊标记
                                    # VM需要修改以支持这种格式
                                    self.output.append(reg_num)
                                    self.output.append(0)
                                    self.output.append(0)
                                    self.output.append(0)
                                    self.current_address += 4
                                    break
                                if arg_str in self.labels:
                                    addr = self.labels[arg_str]
                                    self.current_address += self._encode_imm(addr, self.output)
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
        struct.pack_into('>I', header, 24, 0)  # bss_size
        struct.pack_into('>I', header, 28, 0)  # flags
        
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
        
        # 无操作数指令
        if mnemonic == 'NOP':
            return (OpCode.NOP, [], 1)
        elif mnemonic == 'HALT':
            return (OpCode.HALT, [], 1)
        elif mnemonic == 'RET':
            return (OpCode.RET, [], 1)
        
        # 单操作数指令
        elif mnemonic == 'PUSH':
            if len(args) == 1 and args[0] in REG_MAP:
                return (OpCode.PUSH, [REG_MAP[args[0]]], 2)
        elif mnemonic == 'POP':
            if len(args) == 1 and args[0] in REG_MAP:
                return (OpCode.POP, [REG_MAP[args[0]]], 2)
        elif mnemonic == 'PRINT':
            if len(args) == 1 and args[0] in REG_MAP:
                return (OpCode.PRINT, [REG_MAP[args[0]]], 2)
        elif mnemonic == 'INPUT':
            if len(args) == 1 and args[0] in REG_MAP:
                return (OpCode.INPUT, [REG_MAP[args[0]]], 2)
        elif mnemonic == 'PRINTS':
            if len(args) == 1:
                addr = self._parse_address(args[0])
                return (OpCode.PRINTS, [addr], 6)
        elif mnemonic == 'JMP':
            if len(args) == 1:
                return (OpCode.JMP, [self._parse_value(args[0])], 2)
        elif mnemonic == 'JE':
            if len(args) == 1:
                return (OpCode.JE, [self._parse_value(args[0])], 2)
        elif mnemonic == 'JNE':
            if len(args) == 1:
                return (OpCode.JNE, [self._parse_value(args[0])], 2)
        elif mnemonic == 'JG':
            if len(args) == 1:
                return (OpCode.JG, [self._parse_value(args[0])], 2)
        elif mnemonic == 'JGE':
            if len(args) == 1:
                return (OpCode.JGE, [self._parse_value(args[0])], 2)
        elif mnemonic == 'JL':
            if len(args) == 1:
                return (OpCode.JL, [self._parse_value(args[0])], 2)
        elif mnemonic == 'JLE':
            if len(args) == 1:
                return (OpCode.JLE, [self._parse_value(args[0])], 2)
        elif mnemonic == 'CALL':
            if len(args) == 1:
                return (OpCode.CALL, [self._parse_value(args[0])], 2)
        
        # 双操作数指令
        elif mnemonic == 'MOV':
            if len(args) == 2 and args[0] in REG_MAP and args[1] in REG_MAP:
                return (OpCode.MOV, [REG_MAP[args[0]], REG_MAP[args[1]]], 3)
        elif mnemonic == 'CMP':
            if len(args) == 2:
                if args[0] in REG_MAP and args[1] in REG_MAP:
                    return (OpCode.CMP, [REG_MAP[args[0]], REG_MAP[args[1]]], 3)
                elif args[0] in REG_MAP:
                    return (OpCode.CMP, [REG_MAP[args[0]], self._parse_value(args[1])], 6)
        elif mnemonic == 'SHL':
            if len(args) == 2 and args[0] in REG_MAP and args[1] in REG_MAP:
                return (OpCode.SHL, [REG_MAP[args[0]], REG_MAP[args[1]]], 3)
        elif mnemonic == 'SHR':
            if len(args) == 2 and args[0] in REG_MAP and args[1] in REG_MAP:
                return (OpCode.SHR, [REG_MAP[args[0]], REG_MAP[args[1]]], 3)
        
        # 三操作数指令
        elif mnemonic == 'ADD':
            if len(args) == 3:
                if args[0] in REG_MAP and args[1] in REG_MAP and args[2] in REG_MAP:
                    return (OpCode.ADD, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
                elif args[0] in REG_MAP and args[1] in REG_MAP:
                    return (OpCode.ADD, [REG_MAP[args[0]], REG_MAP[args[1]], self._parse_value(args[2])], 6)
        elif mnemonic == 'SUB':
            if len(args) == 3:
                if args[0] in REG_MAP and args[1] in REG_MAP and args[2] in REG_MAP:
                    return (OpCode.SUB, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
                elif args[0] in REG_MAP and args[1] in REG_MAP:
                    return (OpCode.SUB, [REG_MAP[args[0]], REG_MAP[args[1]], self._parse_value(args[2])], 6)
        elif mnemonic == 'MUL':
            if len(args) == 3:
                if args[0] in REG_MAP and args[1] in REG_MAP and args[2] in REG_MAP:
                    return (OpCode.MUL, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
        elif mnemonic == 'DIV':
            if len(args) == 3:
                if args[0] in REG_MAP and args[1] in REG_MAP and args[2] in REG_MAP:
                    return (OpCode.DIV, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
        elif mnemonic == 'MOD':
            if len(args) == 3:
                if args[0] in REG_MAP and args[1] in REG_MAP and args[2] in REG_MAP:
                    return (OpCode.MOD, [REG_MAP[args[0]], REG_MAP[args[1]], REG_MAP[args[2]]], 4)
        
        # 内存访问指令
        elif mnemonic == 'LOAD':
            if len(args) == 2:
                if args[0] in REG_MAP:
                    addr = self._parse_address(args[1])
                    return (OpCode.LOAD, [REG_MAP[args[0]], addr], 6)
        elif mnemonic == 'STORE':
            if len(args) == 2:
                if args[1] in REG_MAP:
                    addr = self._parse_address(args[0])
                    return (OpCode.STORE, [addr, REG_MAP[args[1]]], 6)
        elif mnemonic == 'LOADIMM':
            if len(args) == 2 and args[0] in REG_MAP:
                return (OpCode.LOADIMM, [REG_MAP[args[0]], self._parse_value(args[1])], 6)  # 6字节: opcode + reg + 4字节imm
        
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
                # 检查是否是寄存器名称
                if s in REG_MAP:
                    return REG_MAP[s]
                # 标签未定义，标记为待解析
                return -1  # 特殊标记，表示标签
            try:
                return int(s)
            except ValueError:
                return 0
    
    def _parse_address(self, s: str) -> int:
        """解析地址"""
        s = s.strip()
        # 检查是否为寄存器名称（不带括号的间接寻址）
        if s in REG_MAP:
            return -1  # 间接寻址标记
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


# ==================== 虚拟机实现 ====================

class FSGVM:
    """FSG 虚拟机"""
    def __init__(self):
        self.state = VMState()
        self.state.memory = bytearray(MEMORY_SIZE)
        self.state.sp = MEMORY_SIZE - 64  # 预留栈空间
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
        except ValueError:
            return 0
    
    def load_bytecode(self, bytecode: bytes):
        """加载字节码文件"""
        self.program = self._load_bytecode_from_bytes(bytecode)
        self.state.pc = self.program.entry_addr
    
    def _load_bytecode_from_bytes(self, bytecode: bytes) -> LoadedProgram:
        """从字节流加载程序"""
        if len(bytecode) < 32:
            raise ValueError("Invalid bytecode: too short")
        
        # 解析文件头
        magic = bytecode[0:4]
        if magic != FSGB_MAGIC:
            raise ValueError(f"Invalid magic number: {magic}")
        
        version = struct.unpack('>H', bytecode[4:6])[0]
        entry_point = struct.unpack('>I', bytecode[8:12])[0]
        text_size = struct.unpack('>I', bytecode[12:16])[0]
        data_size = struct.unpack('>I', bytecode[16:20])[0]
        rodata_size = struct.unpack('>I', bytecode[20:24])[0]
        bss_size = struct.unpack('>I', bytecode[24:28])[0]
        flags = struct.unpack('>I', bytecode[28:32])[0]
        
        # 校验和验证
        checksum_data = bytecode[32:]
        checksum_data += bytearray(4)  # 校验和字段本身不计入
        expected_checksum = zlib.crc32(checksum_data) & 0xFFFFFFFF
        actual_checksum = struct.unpack('>I', bytecode[28:32])[0]
        if expected_checksum != actual_checksum:
            raise ValueError(f"Checksum mismatch: expected {expected_checksum:08x}, got {actual_checksum:08x}")
        
        # 加载代码段
        self.state.memory[0x20:0x20+text_size] = bytecode[32:32+text_size]
        
        # 加载数据段
        if data_size > 0:
            self.state.memory[0x1000:0x1000+data_size] = bytecode[32+text_size:32+text_size+data_size]
        
        # 加载只读数据段
        if rodata_size > 0:
            self.state.memory[0x2000:0x2000+rodata_size] = bytecode[32+text_size+data_size:32+text_size+data_size+rodata_size]
        
        return LoadedProgram(
            magic=magic,
            version=version,
            entry_point=entry_point,
            text_size=text_size,
            data_size=data_size,
            rodata_size=rodata_size,
            bss_size=bss_size,
            entry_addr=0x20,
            flags=flags
        )
    
    def run(self):
        """执行程序"""
        self.state.running = True
        while self.state.running:
            self._execute_instruction()
    
    def _read_reg(self) -> int:
        """读取寄存器编号"""
        reg = self.state.memory[self.state.pc]
        self.state.pc += 1
        return reg
    
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
    
    def _execute_instruction(self):
        """执行单条指令"""
        if self.state.pc >= len(self.state.memory):
            self.state.running = False
            return
        
        opcode = self.state.memory[self.state.pc]
        self.state.pc += 1
        
        if self.debug:
            print(f"PC={self.state.pc-1:04X} OP={opcode:02X}", end=" ")
        
        # 执行指令
        try:
            if opcode == OpCode.NOP:
                self._op_nop()
            elif opcode == OpCode.HALT:
                self._op_halt()
            elif opcode == OpCode.LOAD:
                self._op_load()
            elif opcode == OpCode.STORE:
                self._op_store()
            elif opcode == OpCode.LOADIMM:
                self._op_loadimm()
            elif opcode == OpCode.PUSH:
                self._op_push()
            elif opcode == OpCode.POP:
                self._op_pop()
            elif opcode == OpCode.MOV:
                self._op_mov()
            elif opcode == OpCode.ADD:
                self._op_add()
            elif opcode == OpCode.SUB:
                self._op_sub()
            elif opcode == OpCode.MUL:
                self._op_mul()
            elif opcode == OpCode.DIV:
                self._op_div()
            elif opcode == OpCode.MOD:
                self._op_mod()
            elif opcode == OpCode.CMP:
                self._op_cmp()
            elif opcode == OpCode.JMP:
                self._op_jmp()
            elif opcode == OpCode.JE:
                self._op_je()
            elif opcode == OpCode.JNE:
                self._op_jne()
            elif opcode == OpCode.JG:
                self._op_jg()
            elif opcode == OpCode.JGE:
                self._op_jge()
            elif opcode == OpCode.JL:
                self._op_jl()
            elif opcode == OpCode.JLE:
                self._op_jle()
            elif opcode == OpCode.CALL:
                self._op_call()
            elif opcode == OpCode.RET:
                self._op_ret()
            elif opcode == OpCode.PRINT:
                self._op_print()
            elif opcode == OpCode.INPUT:
                self._op_input()
            elif opcode == OpCode.PRINTS:
                self._op_prints()
            elif opcode == OpCode.SHL:
                self._op_shl()
            elif opcode == OpCode.SHR:
                self._op_shr()
            elif opcode == 0xF0:  # SYSCALL
                self._op_syscall()
            else:
                if self.debug:
                    print(f"Unknown opcode: {opcode}")
                self.state.running = False
        except Exception as e:
            if self.debug:
                print(f"Error executing opcode {opcode}: {e}")
            raise
    
    def _update_flags(self, value: int):
        """更新标志位"""
        self.state.zf = (value == 0)
        self.state.sf = (value < 0)
        self.state.cf = (value < 0)  # 简化处理
        self.state.of = (value < 0)  # 简化处理
    
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
        """LOAD R, addr/[R]"""
        reg = self._read_reg()
        addr = self._read_addr32()
        
        # 检查是否为间接寻址标记（寄存器编号）
        if 0 <= addr <= 7:
            # 使用寄存器的值作为地址
            addr = self.state.registers[addr]
        
        value = struct.unpack('>i', bytes(self.state.memory[addr:addr+4]))[0]
        self.state.registers[reg] = value
        if self.debug:
            print(f"LOAD R{reg}, [{addr}] = {value}")
    
    def _op_store(self):
        """STORE addr/[R], R"""
        addr = self._read_addr32()
        reg = self._read_reg()
        
        # 检查是否为间接寻址标记（寄存器编号）
        if 0 <= addr <= 7:
            # 使用寄存器的值作为地址
            addr = self.state.registers[addr]
        
        value = self.state.registers[reg]
        struct.pack_into('>i', self.state.memory, addr, value)
        if self.debug:
            print(f"STORE [{addr}], R{reg} = {value}")
    
    def _op_loadimm(self):
        """LOADIMM R, imm"""
        reg = self._read_reg()
        value = self._read_imm32()
        self.state.registers[reg] = value
        if self.debug:
            print(f"LOADIMM R{reg}, {value}")
    
    def _op_push(self):
        """PUSH R"""
        reg = self._read_reg()
        value = self.state.registers[reg]
        self.state.sp -= 4
        struct.pack_into('>i', self.state.memory, self.state.sp, value)
        if self.debug:
            print(f"PUSH R{reg} = {value}")
    
    def _op_pop(self):
        """POP R"""
        reg = self._read_reg()
        value = struct.unpack('>i', bytes(self.state.memory[self.state.sp:self.state.sp+4]))[0]
        self.state.registers[reg] = value
        self.state.sp += 4
        if self.debug:
            print(f"POP R{reg} = {value}")
    
    def _op_mov(self):
        """MOV Rd, Rs"""
        rd = self._read_reg()
        rs = self._read_reg()
        self.state.registers[rd] = self.state.registers[rs]
        if self.debug:
            print(f"MOV R{rd}, R{rs} = {self.state.registers[rs]}")
    
    def _op_add(self):
        """ADD Rd, Rs, Rt/imm"""
        rd = self._read_reg()
        rs = self._read_reg()
        # 检查下一个字节是否为寄存器
        if self.state.pc < len(self.state.memory) and 0 <= self.state.memory[self.state.pc] <= 7:
            rt = self._read_reg()
            result = self.state.registers[rs] + self.state.registers[rt]
            self.state.registers[rd] = result
            if self.debug:
                print(f"ADD R{rd}, R{rs}, R{rt} = {result}")
        else:
            imm = self._read_imm32()
            result = self.state.registers[rs] + imm
            self.state.registers[rd] = result
            if self.debug:
                print(f"ADD R{rd}, R{rs}, {imm} = {result}")
        self._update_flags(result)
    
    def _op_sub(self):
        """SUB Rd, Rs, Rt/imm"""
        rd = self._read_reg()
        rs = self._read_reg()
        if self.state.pc < len(self.state.memory) and 0 <= self.state.memory[self.state.pc] <= 7:
            rt = self._read_reg()
            result = self.state.registers[rs] - self.state.registers[rt]
            self.state.registers[rd] = result
            if self.debug:
                print(f"SUB R{rd}, R{rs}, R{rt} = {result}")
        else:
            imm = self._read_imm32()
            result = self.state.registers[rs] - imm
            self.state.registers[rd] = result
            if self.debug:
                print(f"SUB R{rd}, R{rs}, {imm} = {result}")
        self._update_flags(result)
    
    def _op_mul(self):
        """MUL Rd, Rs, Rt"""
        rd = self._read_reg()
        rs = self._read_reg()
        rt = self._read_reg()
        result = self.state.registers[rs] * self.state.registers[rt]
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"MUL R{rd}, R{rs}, R{rt} = {result}")
    
    def _op_div(self):
        """DIV Rd, Rs, Rt"""
        rd = self._read_reg()
        rs = self._read_reg()
        rt = self._read_reg()
        if self.state.registers[rt] == 0:
            result = 0
        else:
            result = self.state.registers[rs] // self.state.registers[rt]
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"DIV R{rd}, R{rs}, R{rt} = {result}")
    
    def _op_mod(self):
        """MOD Rd, Rs, Rt"""
        rd = self._read_reg()
        rs = self._read_reg()
        rt = self._read_reg()
        if self.state.registers[rt] == 0:
            result = 0
        else:
            result = self.state.registers[rs] % self.state.registers[rt]
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"MOD R{rd}, R{rs}, R{rt} = {result}")
    
    def _op_cmp(self):
        """CMP R1, R2/imm"""
        r1 = self._read_reg()
        if self.state.pc < len(self.state.memory) and 0 <= self.state.memory[self.state.pc] <= 7:
            r2 = self._read_reg()
            result = self.state.registers[r1] - self.state.registers[r2]
            if self.debug:
                print(f"CMP R{r1}, R{r2} = {result}")
        else:
            imm = self._read_imm32()
            result = self.state.registers[r1] - imm
            if self.debug:
                print(f"CMP R{r1}, {imm} = {result}")
        self._update_flags(result)
    
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
                print(f"JE PC+{offset}")
        else:
            if self.debug:
                print(f"JE not taken")
    
    def _op_jne(self):
        """JNE offset"""
        offset = self._read_imm8()
        if not self.state.zf:
            self.state.pc += offset - 1
            if self.debug:
                print(f"JNE PC+{offset}")
        else:
            if self.debug:
                print(f"JNE not taken")
    
    def _op_jg(self):
        """JG offset"""
        offset = self._read_imm8()
        if not self.state.zf and not self.state.sf:
            self.state.pc += offset - 1
            if self.debug:
                print(f"JG PC+{offset}")
        else:
            if self.debug:
                print(f"JG not taken")
    
    def _op_jge(self):
        """JGE offset"""
        offset = self._read_imm8()
        if self.state.zf or not self.state.sf:
            self.state.pc += offset - 1
            if self.debug:
                print(f"JGE PC+{offset}")
        else:
            if self.debug:
                print(f"JGE not taken")
    
    def _op_jl(self):
        """JL offset"""
        offset = self._read_imm8()
        if self.state.sf != self.state.of:
            self.state.pc += offset - 1
            if self.debug:
                print(f"JL PC+{offset}")
        else:
            if self.debug:
                print(f"JL not taken")
    
    def _op_jle(self):
        """JLE offset"""
        offset = self._read_imm8()
        if self.state.zf or (self.state.sf != self.state.of):
            self.state.pc += offset - 1
            if self.debug:
                print(f"JLE PC+{offset}")
        else:
            if self.debug:
                print(f"JLE not taken")
    
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
        print(self.state.registers[reg])
        if self.debug:
            print(f"PRINT R{reg} = {self.state.registers[reg]}")
    
    def _op_input(self):
        """INPUT R"""
        reg = self._read_reg()
        try:
            self.state.registers[reg] = int(input())
        except ValueError:
            self.state.registers[reg] = 0
        if self.debug:
            print(f"INPUT R{reg} = {self.state.registers[reg]}")
    
    def _op_prints(self):
        """PRINTS addr"""
        addr = self._read_addr32()
        s = []
        i = addr
        while i < len(self.state.memory) and self.state.memory[i] != 0:
            s.append(chr(self.state.memory[i]))
            i += 1
        print(''.join(s), end='')
        if self.debug:
            print(f"PRINTS @{addr} = {''.join(s)}")
    
    def _op_shl(self):
        """SHL Rd, Rs"""
        rd = self._read_reg()
        rs = self._read_reg()
        result = self.state.registers[rs] << 1
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"SHL R{rd}, R{rs} = {result}")
    
    def _op_shr(self):
        """SHR Rd, Rs"""
        rd = self._read_reg()
        rs = self._read_reg()
        result = self.state.registers[rs] >> 1
        self.state.registers[rd] = result
        self._update_flags(result)
        if self.debug:
            print(f"SHR R{rd}, R{rs} = {result}")
    
    def _op_syscall(self):
        """SYSCALL"""
        syscall_num = self._read_imm32()
        if syscall_num in self.native_functions:
            args = []
            arg_count = self._read_imm32()
            for _ in range(arg_count):
                args.append(self._read_imm32())
            result = self.native_functions[syscall_num](args)
            self._write_imm32(result)
    
    def _read_imm8(self) -> int:
        """读取8位立即数"""
        val = self.state.memory[self.state.pc]
        self.state.pc += 1
        return val
    
    def _write_imm32(self, value: int):
        """写入32位值"""
        struct.pack_into('>i', self.state.memory, self.state.pc, value)
        self.state.pc += 4


# ==================== 主函数 ====================

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <bytecode.fsgb>")
        sys.exit(1)
    
    try:
        with open(sys.argv[1], 'rb') as f:
            bytecode = f.read()
        
        vm = FSGVM()
        vm.load_bytecode(bytecode)
        vm.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)