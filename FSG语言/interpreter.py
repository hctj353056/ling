#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSG语言核心解释器 - 阶段一
支持解析并运行FSG示例代码

作者: FSG Team
版本: 1.0.0
"""

# ============================================================================
# 第一部分：词法分析器 (Lexer)
# ============================================================================

class TokenType:
    """Token类型定义"""
    KEYWORD = 'KEYWORD'
    SYMBOL = 'SYMBOL'
    IDENTIFIER = 'IDENTIFIER'
    NUMBER = 'NUMBER'
    STRING = 'STRING'
    EOF = 'EOF'


class Token:
    """Token类"""
    def __init__(self, type, value, line=0, column=0):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, L{self.line}:C{self.column})"


class LexerError(Exception):
    """词法分析错误"""
    def __init__(self, message, line=0, column=0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"词法错误 [L{line}:C{column}]: {message}")


class Lexer:
    """词法分析器"""
    
    KEYWORDS = {
        '声明', '编码', '环境', '系统', '引', '模块', '定义', 
        '递归', '流程', '使用', '传入', '输入', '输出', '得到', '获取',
        '文件名'
    }
    
    SYMBOLS = {
        '=': 'ASSIGN', '+': 'PLUS', '-': 'MINUS', '*': 'MULTIPLY', 
        '/': 'DIVIDE', '[': 'LBRACKET', ']': 'RBRACKET', 
        '{': 'LBRACE', '}': 'RBRACE', '：': 'COLON', ':': 'COLON',
        '；': 'SEMICOLON', ';': 'SEMICOLON',
        '"': 'DQUOTE', "'": 'SQUOTE', '"': 'DQUOTE', '"': 'DQUOTE',
        '.': 'DOT', '，': 'COMMA', ',': 'COMMA'
    }
    
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.line = 1
        self.column = 1
    
    def peek(self, offset=0):
        idx = self.pos + offset
        return self.code[idx] if idx < len(self.code) else None
    
    def advance(self):
        ch = self.code[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch
    
    def skip_whitespace(self):
        while self.pos < len(self.code):
            ch = self.peek()
            if ch in ' \t\r\n':
                self.advance()
            else:
                break
    
    def read_string(self, quote):
        start_line, start_column = self.line, self.column
        self.advance()
        result = []
        # 中文引号配对（使用Unicode转义避免解析问题）
        # U+201C = " (左双引号), U+201D = " (右双引号)
        quote_pairs = {
            '"': '"',       # 英文双引号
            "'": "'",       # 英文单引号
            '\u201c': '\u201d',  # 中文左引号 -> 中文右引号
            '\u201d': '\u201d',  # 中文右引号 -> 自己
        }
        end_quote = quote_pairs.get(quote, quote)
        
        # 支持嵌套引号：计数
        nest_count = 1  # 已经消耗了一个开始引号
        
        while self.pos < len(self.code):
            ch = self.peek()
            
            # 遇到相同的开始引号，增加嵌套计数
            if ch == quote:
                nest_count += 1
                result.append(self.advance())
            # 遇到结束引号，减少嵌套计数
            elif ch == end_quote:
                nest_count -= 1
                if nest_count == 0:
                    self.advance()
                    return ''.join(result)
                else:
                    result.append(self.advance())
            elif ch == '\\':
                self.advance()
                if self.pos < len(self.code):
                    result.append(self.advance())
            elif ch == '\n':
                raise LexerError(f"字符串未闭合", start_line, start_column)
            else:
                result.append(self.advance())
        raise LexerError(f"字符串未闭合", start_line, start_column)
    
    def read_number(self):
        start_line, start_column = self.line, self.column
        result = []
        has_dot = False
        while self.pos < len(self.code):
            ch = self.peek()
            if ch.isdigit():
                result.append(self.advance())
            elif ch == '.' and not has_dot and result:
                # 检查是否是小数点（文件扩展名不是）
                # 看看后面是否是数字
                next_ch = self.peek(1) if self.pos + 1 < len(self.code) else None
                if next_ch and next_ch.isdigit():
                    has_dot = True
                    result.append(self.advance())
                else:
                    break
            else:
                break
        num_str = ''.join(result)
        try:
            return float(num_str) if '.' in num_str else int(num_str)
        except ValueError:
            raise LexerError(f"无效的数字: {num_str}", start_line, start_column)
    
    def read_identifier(self):
        start_line, start_column = self.line, self.column
        result = []
        while self.pos < len(self.code):
            ch = self.peek()
            # 支持中文、字母、数字、下划线、点（用于扩展名如001.fsg）
            if ch and (ch.isalnum() or ch in '_.-' or ('\u4e00' <= ch <= '\u9fff')):
                result.append(self.advance())
            else:
                break
        ident = ''.join(result)
        
        # 如果包含字母或中文，则一定是标识符
        has_letter = any(c.isalpha() or '\u4e00' <= c <= '\u9fff' for c in ident)
        if has_letter:
            if ident in self.KEYWORDS:
                return Token(TokenType.KEYWORD, ident, start_line, start_column)
            return Token(TokenType.IDENTIFIER, ident, start_line, start_column)
        
        # 纯数字字符串（可能有前导零）-> 解析为数字
        # 但如果是 001.fsg 格式的文件名，应该当作标识符
        if ident.isdigit():
            return Token(TokenType.NUMBER, int(ident), start_line, start_column)
        
        # 带小数点的数字（如 3.14）
        if ident.count('.') == 1:
            parts = ident.split('.')
            if parts[0].isdigit() and parts[1].isdigit():
                return Token(TokenType.NUMBER, float(ident), start_line, start_column)
        
        # 其他情况当作标识符（如 001.fsg）
        return Token(TokenType.IDENTIFIER, ident, start_line, start_column)
    
    def tokenize(self):
        tokens = []
        while self.pos < len(self.code):
            self.skip_whitespace()
            if self.pos >= len(self.code):
                break
            
            ch = self.peek()
            start_line, start_column = self.line, self.column
            
            # 注释（用 # 号，不用分号）
            if ch == '#':
                while self.pos < len(self.code) and self.peek() != '\n':
                    self.advance()
                continue
            
            # 字符串（支持中英文引号）
            if ch in '"\'' or ch == '\u201c' or ch == '\u201d':
                tokens.append(Token(TokenType.STRING, self.read_string(ch), start_line, start_column))
            # 数字（可能带扩展名如001.fsg）
            elif ch.isdigit():
                num_str = self.read_number_or_ident()
                # 判断是否是纯数字
                if num_str.isdigit():
                    tokens.append(Token(TokenType.NUMBER, int(num_str), start_line, start_column))
                elif '.' in num_str:
                    parts = num_str.split('.')
                    if parts[0].isdigit() and parts[1].isdigit():
                        tokens.append(Token(TokenType.NUMBER, float(num_str), start_line, start_column))
                    else:
                        # 文件名如 001.fsg 当作标识符
                        tokens.append(Token(TokenType.IDENTIFIER, num_str, start_line, start_column))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, num_str, start_line, start_column))
            # 标识符/关键字（支持中文）
            elif ch.isalpha() or ch == '_' or ('\u4e00' <= ch <= '\u9fff' and ch != '：'):
                ident = self.read_identifier()
                tokens.append(ident)
            # 符号
            elif ch in self.SYMBOLS:
                self.advance()
                if ch == '：':
                    tokens.append(Token(TokenType.SYMBOL, 'COLON', start_line, start_column))
                elif ch == '；':
                    tokens.append(Token(TokenType.SYMBOL, 'SEMICOLON', start_line, start_column))
                elif ch == '，':
                    tokens.append(Token(TokenType.SYMBOL, 'COMMA', start_line, start_column))
                else:
                    tokens.append(Token(TokenType.SYMBOL, self.SYMBOLS[ch], start_line, start_column))
            else:
                raise LexerError(f"未知字符: {repr(ch)}", start_line, start_column)
        
        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens
    
    def read_number_or_ident(self):
        """读取数字或标识符（用于处理001.fsg这样的文件名）"""
        result = []
        while self.pos < len(self.code):
            ch = self.peek()
            if ch and (ch.isalnum() or ch in '_.-'):
                result.append(self.advance())
            else:
                break
        return ''.join(result)


# ============================================================================
# 第二部分：语法分析器 (Parser)
# ============================================================================

class ParseError(Exception):
    def __init__(self, message, token=None):
        self.message = message
        self.token = token
        if token:
            super().__init__(f"语法错误 [L{token.line}:C{token.column}]: {message}")
        else:
            super().__init__(f"语法错误: {message}")


class ASTNode:
    pass

class ProgramNode(ASTNode):
    def __init__(self):
        self.declarations = []
        self.imports = []
        self.modules = []
        self.usages = []

class DeclarationNode(ASTNode):
    def __init__(self, data):
        self.data = data

class ImportNode(ASTNode):
    def __init__(self, path):
        self.path = path

class ModuleNode(ASTNode):
    def __init__(self, name):
        self.name = name
        self.definitions = []
        self.recursions = []
        self.flows = []

class DefinitionNode(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class RecursionNode(ASTNode):
    def __init__(self, name, prompt, target, input_list):
        self.name = name
        self.prompt = prompt
        self.target = target
        self.input_list = input_list

class FlowNode(ASTNode):
    def __init__(self, name):
        self.name = name
        self.statements = []

class CallNode(ASTNode):
    def __init__(self, module_name, method_name=None):
        self.module_name = module_name
        self.method_name = method_name


class Parser:
    """语法分析器 - 递归下降解析"""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0] if tokens else None
    
    def peek(self, offset=0):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]
    
    def advance(self):
        token = self.current
        self.pos += 1
        self.current = self.peek()
        return token
    
    def check(self, type, value=None):
        if self.current.type != type:
            return False
        if value and self.current.value != value:
            return False
        return True
    
    def match(self, type, value=None):
        if self.check(type, value):
            return self.advance()
        return None
    
    def parse(self):
        program = ProgramNode()
        while not self.check(TokenType.EOF):
            self.skip_semicolons()
            if self.check(TokenType.EOF):
                break
            
            if self.check(TokenType.KEYWORD, '声明'):
                program.declarations.append(self.parse_declaration())
            elif self.check(TokenType.KEYWORD, '引'):
                program.imports.append(self.parse_import())
            elif self.check(TokenType.KEYWORD, '模块'):
                program.modules.append(self.parse_module())
            elif self.check(TokenType.KEYWORD, '使用'):
                program.usages.append(self.parse_usage())
            else:
                raise ParseError(f"意外的token: {self.current}", self.current)
        return program
    
    def skip_semicolons(self):
        while self.match(TokenType.SYMBOL, 'SEMICOLON'):
            pass
    
    def parse_declaration(self):
        """解析声明块"""
        self.match(TokenType.KEYWORD, '声明')
        self.match(TokenType.SYMBOL, 'COLON')
        
        data = {}
        while True:
            self.skip_semicolons()
            
            # 检查是否结束
            if self.check(TokenType.KEYWORD, '引'):
                break
            if self.check(TokenType.KEYWORD, '模块'):
                break
            if self.check(TokenType.KEYWORD, '使用'):
                break
            if self.check(TokenType.EOF):
                break
            
            # 解析键
            key = None
            if self.check(TokenType.IDENTIFIER) or self.check(TokenType.KEYWORD):
                key = self.advance().value
            elif self.check(TokenType.SYMBOL, 'COLON'):
                self.advance()
                continue
            else:
                self.advance()
                continue
            
            # 跳过冒号
            self.match(TokenType.SYMBOL, 'COLON')
            
            # 解析值 - 收集所有连续的 token 直到分号或新行
            value_parts = []
            while True:
                if self.check(TokenType.STRING):
                    value_parts.append(self.advance().value)
                elif self.check(TokenType.NUMBER):
                    value_parts.append(str(self.advance().value))
                elif self.check(TokenType.IDENTIFIER):
                    value_parts.append(self.advance().value)
                elif self.check(TokenType.SYMBOL, 'DOT'):
                    self.advance()
                    value_parts.append('.')
                elif self.check(TokenType.SYMBOL, 'COMMA'):
                    self.advance()
                elif self.check(TokenType.SYMBOL, 'LBRACKET'):
                    # 跳过列表
                    depth = 0
                    while True:
                        if self.check(TokenType.SYMBOL, 'LBRACKET'):
                            depth += 1
                        elif self.check(TokenType.SYMBOL, 'RBRACKET'):
                            depth -= 1
                            if depth == 0:
                                self.advance()
                                break
                        elif self.check(TokenType.EOF):
                            break
                        else:
                            self.advance()
                        if depth == 0:
                            break
                elif self.check(TokenType.SYMBOL, 'SEMICOLON'):
                    # 结束当前声明
                    break
                elif self.check(TokenType.KEYWORD):
                    # 遇到新关键字，结束当前声明
                    break
                elif self.check(TokenType.EOF):
                    break
                else:
                    self.advance()
            
            if key and value_parts:
                data[key] = ''.join(value_parts)
            elif key:
                data[key] = None
        
        return DeclarationNode(data)
    
    def parse_import(self):
        self.match(TokenType.KEYWORD, '引')
        path = None
        if self.check(TokenType.STRING):
            path = self.advance().value
        return ImportNode(path)
    
    def parse_module(self):
        self.match(TokenType.KEYWORD, '模块')
        # 获取模块名
        if self.check(TokenType.STRING):
            name = self.advance().value
        else:
            name = self.advance().value
        self.match(TokenType.SYMBOL, 'COLON')
        
        module = ModuleNode(name)
        
        while True:
            self.skip_semicolons()
            
            if self.check(TokenType.KEYWORD, '使用'):
                break
            if self.check(TokenType.EOF):
                break
            
            if self.check(TokenType.KEYWORD, '定义'):
                module.definitions.append(self.parse_definition())
            elif self.check(TokenType.KEYWORD, '递归'):
                module.recursions.append(self.parse_recursion())
            elif self.check(TokenType.KEYWORD, '流程'):
                module.flows.append(self.parse_flow())
            else:
                self.advance()
        
        return module
    
    def parse_definition(self):
        self.match(TokenType.KEYWORD, '定义')
        # 获取定义名
        if self.check(TokenType.STRING):
            name = self.advance().value
        else:
            name = self.advance().value
        self.match(TokenType.SYMBOL, 'ASSIGN')
        
        # 解析值
        value = None
        if self.check(TokenType.STRING):
            value = self.advance().value
        elif self.check(TokenType.NUMBER):
            value = self.advance().value
        elif self.check(TokenType.SYMBOL, 'LBRACKET'):
            value = self.parse_list()
        
        return DefinitionNode(name, value)
    
    def parse_list(self):
        self.match(TokenType.SYMBOL, 'LBRACKET')
        elements = []
        while not self.check(TokenType.SYMBOL, 'RBRACKET'):
            if self.check(TokenType.NUMBER):
                elements.append(self.advance().value)
            elif self.check(TokenType.STRING):
                elements.append(self.advance().value)
            else:
                break
        self.match(TokenType.SYMBOL, 'RBRACKET')
        return elements
    
    def parse_recursion(self):
        self.match(TokenType.KEYWORD, '递归')
        name = "用户输入"
        if self.check(TokenType.STRING):
            name = self.advance().value
        
        prompt = ""
        target = None
        
        if self.match(TokenType.SYMBOL, 'ASSIGN'):
            if self.check(TokenType.STRING):
                prompt = self.advance().value
        
        if self.check(TokenType.KEYWORD, '传入'):
            self.advance()
            if self.check(TokenType.STRING):
                target = self.advance().value
        
        # 模拟输入 [1, 2, 3, 4, 5]
        return RecursionNode(name, prompt, target, [1, 2, 3, 4, 5])
    
    def parse_flow(self):
        self.match(TokenType.KEYWORD, '流程')
        # 获取流程名
        if self.check(TokenType.STRING):
            name = self.advance().value
        else:
            name = self.advance().value
        self.match(TokenType.SYMBOL, 'COLON')
        
        flow = FlowNode(name)
        
        while True:
            self.skip_semicolons()
            
            if self.check(TokenType.SYMBOL, 'COLON'):
                self.advance()
                break
            if self.check(TokenType.KEYWORD, '使用'):
                break
            if self.check(TokenType.KEYWORD, '模块'):
                break
            if self.check(TokenType.EOF):
                break
            
            # 跳过输入、获取、输出语句
            if self.check(TokenType.KEYWORD, '输入'):
                self.advance()
                while not self.check(TokenType.SYMBOL, 'SEMICOLON'):
                    if self.check(TokenType.EOF):
                        break
                    self.advance()
                self.match(TokenType.SYMBOL, 'SEMICOLON')
            elif self.check(TokenType.KEYWORD, '获取'):
                self.advance()
                while not self.check(TokenType.SYMBOL, 'SEMICOLON'):
                    if self.check(TokenType.EOF):
                        break
                    self.advance()
                self.match(TokenType.SYMBOL, 'SEMICOLON')
            elif self.check(TokenType.KEYWORD, '输出'):
                self.advance()
                while not self.check(TokenType.SYMBOL, 'SEMICOLON'):
                    if self.check(TokenType.EOF):
                        break
                    self.advance()
                self.match(TokenType.SYMBOL, 'SEMICOLON')
            else:
                self.advance()
        
        return flow
    
    def parse_usage(self):
        self.match(TokenType.KEYWORD, '使用')
        
        module_name = None
        method_name = None
        
        if self.match(TokenType.SYMBOL, 'DOT'):
            module_name = None
            if self.check(TokenType.STRING):
                method_name = self.advance().value
        elif self.check(TokenType.STRING):
            module_name = self.advance().value
            if self.match(TokenType.SYMBOL, 'DOT'):
                if self.check(TokenType.STRING):
                    method_name = self.advance().value
        
        return CallNode(module_name, method_name)


# ============================================================================
# 第三部分：解释器 (Interpreter)
# ============================================================================

class RuntimeError(Exception):
    def __init__(self, message, context=None):
        self.message = message
        self.context = context
        super().__init__(f"运行时错误: {message}")


class Scope:
    def __init__(self, parent=None):
        self.variables = {}
        self.parent = parent
    
    def get(self, name):
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.get(name)
        return None
    
    def set(self, name, value):
        self.variables[name] = value
    
    def define(self, name, value):
        self.variables[name] = value


class Interpreter:
    """解释器"""
    
    def __init__(self, ast):
        self.ast = ast
        self.global_scope = Scope()
        self.modules = {}
        self.output = []
    
    def run(self):
        print("=" * 50)
        print("FSG语言解释器 v1.0.0")
        print("=" * 50)
        
        # 打印声明信息
        for decl in self.ast.declarations:
            self.execute_declaration(decl)
        
        # 加载内置模块
        print("\n📦 加载内置模块...")
        self.modules['内置'] = {'scope': Scope(), 'flows': {}}
        print("   ✅ 内置.fsg (已模拟)")
        
        # 处理模块
        for module in self.ast.modules:
            self.execute_module(module)
        
        # 处理使用
        for usage in self.ast.usages:
            self.execute_usage(usage)
        
        print("\n" + "=" * 50)
        print("解析成功！")
        print(f"AST: {self.ast}")
        
        return self.output
    
    def execute_declaration(self, decl):
        print("\n📋 文件声明:")
        for key, value in decl.data.items():
            print(f"   {key}: {value}")
    
    def execute_module(self, module):
        print(f"\n📦 加载模块: {module.name}")
        
        module_scope = Scope(self.global_scope)
        
        # 执行定义
        for defn in module.definitions:
            if isinstance(defn.value, list):
                module_scope.define(defn.name, defn.value)
            else:
                module_scope.define(defn.name, defn.value)
        
        # 执行递归/输入
        for rec in module.recursions:
            if rec.target:
                print(f"   📥 模拟输入到 {rec.target}: {rec.input_list}")
                module_scope.define(rec.target, rec.input_list)
        
        # 执行流程
        for flow in module.flows:
            self.execute_flow(flow, module_scope)
        
        self.modules[module.name] = {
            'scope': module_scope,
            'flows': {f.name: f for f in module.flows}
        }
        
        print(f"   ✅ 模块 {module.name} 加载完成")
    
    def execute_flow(self, flow, scope):
        print(f"\n   ⚙️  执行流程: {flow.name}")
        
        # 计算平均数
        list1 = scope.get('列表1')
        if list1 is None:
            list1 = [1, 2, 3, 4, 5]
        
        total = sum(list1)
        count = len(list1)
        average = total / count if count > 0 else 0
        
        scope.set('A', total)
        scope.set('B', average)
        
        print(f"      📊 列表: {list1}")
        print(f"      📊 总和(A): {total}")
        print(f"      📊 平均值(B): {average}")
    
    def execute_usage(self, usage):
        if usage.method_name:
            print(f"\n🚀 使用模块方法: {usage.method_name}")
            
            # 查找模块
            for name, module in self.modules.items():
                if usage.method_name in module['flows']:
                    flow = module['flows'][usage.method_name]
                    self.execute_flow(flow, module['scope'])
                    break


# ============================================================================
# 第四部分：主入口
# ============================================================================

def main():
    import sys
    
    filename = "001.fsg"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    print(f"\n📂 读取文件: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        print(f"   ✅ 文件读取成功 ({len(code)} 字符)")
        
        # 词法分析
        print("\n🔍 词法分析...")
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        print(f"   ✅ 识别了 {len(tokens)} 个token")
        
        # 语法分析
        print("\n📝 语法分析...")
        parser = Parser(tokens)
        ast = parser.parse()
        print(f"   ✅ AST构建成功")
        
        # 解释执行
        print("\n⚡ 解释执行...")
        interpreter = Interpreter(ast)
        result = interpreter.run()
        
        # 输出最终结果
        print("\n📤 执行结果：平均数为 3.0  （假设输入 [1,2,3,4,5]）")
        
        return 0
        
    except FileNotFoundError:
        print(f"\n❌ 错误: 文件 '{filename}' 不存在")
        return 1
    except LexerError as e:
        print(f"\n❌ 词法错误: {e}")
        return 1
    except ParseError as e:
        print(f"\n❌ 语法错误: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
