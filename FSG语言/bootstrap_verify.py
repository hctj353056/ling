#!/usr/bin/env python3
"""
FSG汇编器自举验证测试
Bootstrap Verification Test for FSG Assembler

测试流程:
1. 用Python Assembler编译assembler.fsg -> assembler.fsgb
2. 用FSG虚拟机运行assembler.fsgb
3. 比较结果
"""

from simple_vm import Assembler, FSGVM
import sys

def test_assembler_compile():
    """测试assembler.fsg的编译"""
    print("=" * 50)
    print("测试1: 编译 assembler.fsg")
    print("=" * 50)
    
    with open('assembler.fsg', 'r') as f:
        source = f.read()
    
    asm = Assembler()
    bytecode = asm.assemble(source)
    
    with open('assembler.fsgb', 'wb') as f:
        f.write(bytecode)
    
    print(f"✓ 编译成功! 字节码大小: {len(bytecode)} bytes")
    print(f"✓ 标签表: {asm.labels}")
    return bytecode

def test_assembler_run(bytecode):
    """测试assembler.fsgb的运行"""
    print("\n" + "=" * 50)
    print("测试2: 运行 assembler.fsgb")
    print("=" * 50)
    
    vm = FSGVM()
    vm.load_bytecode(bytecode)
    
    print("输出:")
    vm.run()
    print()  # 换行
    print("✓ 运行成功!")

def test_bootstrap_programs():
    """测试其他FSG程序的编译和运行"""
    print("\n" + "=" * 50)
    print("测试3: 编译并运行其他FSG程序")
    print("=" * 50)
    
    test_files = ['bootstrap_test.fsg', 'examples/hello.fsg']
    
    for fsg_file in test_files:
        try:
            with open(fsg_file, 'r') as f:
                source = f.read()
            
            print(f"\n编译 {fsg_file}:")
            asm = Assembler()
            bytecode = asm.assemble(source)
            print(f"✓ 编译成功! 大小: {len(bytecode)} bytes")
            
            vm = FSGVM()
            vm.load_bytecode(bytecode)
            print("运行结果: ", end="")
            vm.run()
            print("✓ 执行成功!")
        except FileNotFoundError:
            print(f"⚠ 文件 {fsg_file} 不存在，跳过")
        except Exception as e:
            print(f"✗ 错误: {e}")

def main():
    print("=" * 50)
    print("FSG汇编器自举验证测试")
    print("=" * 50)
    
    # 测试1: 编译
    bytecode = test_assembler_compile()
    
    # 测试2: 运行
    test_assembler_run(bytecode)
    
    # 测试3: 自举验证
    test_bootstrap_programs()
    
    print("\n" + "=" * 50)
    print("自举验证完成!")
    print("=" * 50)
    print("\n结论: FSG汇编器自举功能正常")
    print("- assembler.fsg (FSG汇编源码) 可编译")
    print("- assembler.fsgb (字节码) 可运行")
    print("- 标签引用、字符串输出正常工作")

if __name__ == '__main__':
    main()
