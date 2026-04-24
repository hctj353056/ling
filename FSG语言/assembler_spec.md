# FSG 汇编语法规范

> 蜉熵阁 - 类汇编语法定义  
> 版本: 1.0

---

## 概述

FSG汇编语言是一种类汇编的低级语言，设计目标：
- 人类可读、可写
- 机器可直接解析执行
- 便于ling生成

---

## 词法规则

### 1. 标识符

```
identifier ::= [a-zA-Z_][a-zA-Z0-9_]*
label      ::= identifier ':'
```

- 标识符由字母、数字、下划线组成
- 首字符不能是数字
- 区分大小写
- 保留字不能用作标识符

### 2. 注释

```
comment ::= ';' [^\n]*
```

- 单行注释，以 `;` 开始到行尾
- 支持行内注释

```
; 这是整行注释
LOAD R1, [0x100] ; 这是行尾注释
```

### 3. 数字常量

```
integer  ::= ('+'|'-')?[0-9]+              ; 十进制
hex      ::= '0x'[0-9a-fA-F]+              ; 十六进制
octal    ::= '0'[0-7]+                     ; 八进制
binary   ::= '0b'[01]+                     ; 二进制
char     ::= "'" [^'] "'"                  ; 字符常量
string   ::= '"' [^"]* '"'                 ; 字符串常量
```

示例：
```
42          ; 十进制
-128        ; 负数
0xFF        ; 十六进制
0o755       ; 八进制
0b1010      ; 二进制
'A'         ; 字符
"Hello"     ; 字符串
```

### 4. 寄存器

```
register ::= 'R'[0-7]                      ; 通用寄存器 R0-R7
           | 'PC'                           ; 程序计数器
           | 'SP'                           ; 栈指针
           | 'BP'                           ; 基址指针
```

### 5. 操作数类型

```
operand ::= register                        ; 寄存器操作数
         | integer                          ; 立即数
         | hex                              ; 十六进制立即数
         | '[' register ']'                 ; 间接寻址
         | '[' integer ']'                  ; 直接内存地址
         | label                            ; 标签引用
         | string                           ; 字符串常量
```

---

## 语法规则 (BNF)

### 1. 程序结构

```
program        ::= statement*
statement      ::= instruction
                 | label
                 | directive
                 | comment
                 | empty

instruction    ::= mnemonic [operand (',' operand)*]

directive      ::= '.' identifier [argument*]
                 | string_label ':' 'STRING' string
```

### 2. 标签

```
label_def      ::= identifier ':'
label_ref      ::= identifier
```

### 3. 指令格式

```
; 数据传输
LOAD    reg, operand
STORE   operand, reg
LOADIMM reg, imm
PUSH    reg
POP     reg
MOV     reg, reg

; 算术运算
ADD     reg, reg, reg
ADD     reg, reg, imm
SUB     reg, reg, reg
MUL     reg, reg, reg
DIV     reg, reg, reg
NEG     reg
MOD     reg, reg, reg

; 比较与逻辑
CMP     reg, reg
AND     reg, reg, reg
OR      reg, reg, reg
XOR     reg, reg, reg
NOT     reg
SHL     reg, reg, imm
SHR     reg, reg, imm

; 控制流
JMP     label
JE      label
JNE     label
JG      label
JGE     label
JL      label
JLE     label
CALL    label
RET

; I/O
PRINT   operand
INPUT   reg
PRINTS  label

; 特殊
HALT
NOP
SYSCALL imm
DEBUG   imm
INT     imm
```

---

## 汇编器指令 (Directives)

### 1. 数据定义

```
.DATA   addr, value,...    ; 定义数据
.DB     value,...          ; 定义字节
.DW     value,...          ; 定义字(4字节)
.STR    "string"           ; 定义字符串
.ADDR   value              ; 设置地址计数器
.ALIGN  n                  ; 2^n对齐
```

### 2. 代码组织

```
.SECTION .text             ; 代码段
.SECTION .data             ; 数据段
.SECTION .rodata           ; 只读数据段
```

### 3. 外部引用

```
.EXTERN  name              ; 声明外部符号
.GLOBAL  name              ; 导出符号
```

### 4. 条件汇编

```
.IF     condition
...     
.ELSE   
...
.ENDIF  
```

---

## 完整语法示例

```
; ==========================================
; 示例: 计算 1+2+3+...+10
; ==========================================

.SECTION .data
result: .DW 0
fmt:    .STR "Sum = %d\n"

.SECTION .text
.GLOBAL _start

_start:
    LOADIMM R0, 0          ; sum = 0
    LOADIMM R1, 1          ; i = 1
    LOADIMM R2, 10         ; n = 10

loop:
    ADD   R0, R0, R1        ; sum += i
    ADD   R1, R1, 1        ; i++
    CMP   R1, R2           ; compare i, n
    JLE   loop             ; if i <= n, loop

    STORE [result], R0      ; save result
    PRINTS fmt             ; print format
    PRINT  R0              ; print result
    HALT

; ==========================================
; 示例: 求最大公约数 (欧几里得算法)
; ==========================================

.SECTION .text
.GLOBAL gcd

gcd:
    ; 参数: R0=a, R1=b
    ; 返回: R0=gcd(a,b)
gcd_loop:
    CMP   R1, R0           ; compare b, a
    JE    gcd_done         ; if b == a, done
    JG    gcd_swap         ; if b > a, swap
    MOD   R0, R0, R1        ; a = a % b
    JMP   gcd_loop
gcd_swap:
    MOV   R2, R0           ; temp = a
    MOV   R0, R1           ; a = b
    MOV   R1, R2           ; b = temp
    JMP   gcd_loop
gcd_done:
    RET
```

---

## 语义规则

### 1. 表达式求值顺序

- 所有表达式从左到右求值
- 立即数在汇编时计算
- 标签地址在链接时解析

### 2. 作用域规则

- 标签在整个程序中可见（全局）
- 局部标签以 `.L` 开头，作用域限于最近的全局标签

### 3. 类型系统

- 整数：32位有符号
- 地址：32位无符号
- 字符：8位ASCII
- 字符串：字节序列，以0结尾

### 4. 内存布局

```
+------------------+ 高地址
|    命令行参数     |
+------------------+
|    环境变量       |
+------------------+
|      栈          | 向下增长
+------------------+
|       ↓          |
|                  |
|       ↑          |
|                  |
+------------------+ 
|     堆           | 向上增长
+------------------+
|     数据段        |
+------------------+
|     代码段        |
+------------------+ 低地址
```

---

## 错误处理

### 语法错误

| 错误码 | 描述 | 示例 |
|--------|------|------|
| E001 | 未知指令 | `LOADX R1, R2` |
| E002 | 参数数量错误 | `ADD R1` |
| E003 | 无效操作数类型 | `LOAD R1, "abc"` |
| E004 | 无效寄存器 | `LOAD R8, R1` |
| E005 | 未定义的标签 | `JMP undefined_label` |
| E006 | 重复定义的标签 | `label: ... label:` |

### 语义错误

| 错误码 | 描述 | 示例 |
|--------|------|------|
| W001 | 除数为零 | `DIV R0, R1, 0` |
| W002 | 立即数溢出 | `LOADIMM R0, 0xFFFFFFFF1` |
| W003 | 未使用的标签 | `unused_label:` |

---

## 附录：关键字列表

```
; 指令
NOP HALT LOAD STORE LOADIMM PUSH POP MOV
ADD SUB MUL DIV NEG MOD
CMP AND OR XOR NOT SHL SHR
JMP JE JNE JG JGE JL JLE CALL RET INT
PRINT INPUT PRINTS SYSCALL DEBUG

; 寄存器
R0 R1 R2 R3 R4 R5 R6 R7 PC SP BP

; 汇编指令
.DATA .DB .DW .STR .ADDR .ALIGN
.SECTION .TEXT .DATA .RODATA
.EXTERN .GLOBAL .IF .ELSE .ENDIF
```

---

*文档版本: 1.0*  
*最后更新: 2024*
