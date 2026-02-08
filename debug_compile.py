#!/usr/bin/env python3
"""
Отладочный скрипт для проверки компиляции
"""

import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from assembler.instructions import INSTRUCTIONS
from assembler.parser import Parser
from assembler.compiler import Compiler

def test_compilation():
    """Тестовая функция компиляции"""
    
    # Тестовый код
    test_code = """
    # Простой тест
    addi r1, r0, 42      # x1 = 42
    addi x2, x0, 100     # x2 = 100
    add  x3, x1, x2      # x3 = x1 + x2
    addi x4, x3, 10      # x4 = x3 + 10
    """
    
    print("=" * 60)
    print("ТЕСТ КОМПИЛЯЦИИ RISC-V")
    print("=" * 60)
    
    print(f"Доступно инструкций: {len(INSTRUCTIONS)}")
    for name in sorted(INSTRUCTIONS.keys()):
        print(f"  - {name}")
    
    print("\n" + "=" * 60)
    print("КОД ДЛЯ КОМПИЛЯЦИИ:")
    print("=" * 60)
    print(test_code)
    
    # Создаем парсер и компилятор
    parser = Parser(INSTRUCTIONS)
    compiler = Compiler(parser)
    
    lines = [line.rstrip() for line in test_code.strip().split('\n')]
    machine_code = []
    
    print("=" * 60)
    print("ПАРСИНГ И КОМПИЛЯЦИЯ:")
    print("=" * 60)
    
    # Проходим по всем строкам
    for i, line in enumerate(lines, 1):
        if not line.strip() or line.strip().startswith('#'):
            print(f"Строка {i}: Пропуск (пустая/комментарий)")
            continue
        
        print(f"\nСтрока {i}: '{line}'")
        
        try:
            # Парсим строку
            instr_def, args, errors, warnings = parser.parse_line(line, i)
            
            if errors:
                print(f"  ОШИБКИ: {errors}")
                continue
                
            if warnings:
                print(f"  ПРЕДУПРЕЖДЕНИЯ: {warnings}")
            
            if instr_def:
                print(f"  Инструкция: {instr_def.name}")
                print(f"  Аргументы: {args}")
                print(f"  Формат: {instr_def.format_type}")
                print(f"  Opcode: 0b{instr_def.opcode:07b}")
                
                if instr_def.funct3 is not None:
                    print(f"  Funct3: 0b{instr_def.funct3:03b}")
                
                # Компилируем
                try:
                    instruction = compiler.compile_instruction(instr_def, args)
                    machine_code.append(instruction)
                    
                    print(f"  Машинный код: 0x{instruction:08x}")
                    print(f"  Бинарный: {instruction:032b}")
                    
                    # Декомпозиция для проверки
                    opcode = instruction & 0x7F
                    rd = (instruction >> 7) & 0x1F
                    funct3 = (instruction >> 12) & 0x7
                    rs1 = (instruction >> 15) & 0x1F
                    rs2 = (instruction >> 20) & 0x1F
                    funct7 = (instruction >> 25) & 0x7F
                    
                    print(f"  Декомпозиция:")
                    print(f"    opcode: 0b{opcode:07b} (0x{opcode:02x})")
                    print(f"    rd: x{rd}")
                    print(f"    funct3: 0b{funct3:03b}")
                    print(f"    rs1: x{rs1}")
                    print(f"    rs2: x{rs2}")
                    if instr_def.format_type == 'R':
                        print(f"    funct7: 0b{funct7:07b}")
                    
                except Exception as e:
                    print(f"  ОШИБКА КОМПИЛЯЦИИ: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("  Нет инструкции (только метка)")
                
        except Exception as e:
            print(f"  ОШИБКА ПАРСИНГА: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ:")
    print("=" * 60)
    
    if machine_code:
        print(f"Скомпилировано инструкций: {len(machine_code)}")
        print(f"Размер в байтах: {len(machine_code) * 4}")
        
        print("\nМашинный код (hex):")
        for idx, instr in enumerate(machine_code):
            print(f"  0x{idx*4:08x}: 0x{instr:08x}")
        
        # Сохраняем в файл
        output_file = "debug_output.bin"
        try:
            with open(output_file, 'wb') as f:
                for instruction in machine_code:
                    f.write(instruction.to_bytes(4, byteorder='little'))
            
            # Проверяем размер файла
            file_size = os.path.getsize(output_file)
            print(f"\nСохранено в '{output_file}'")
            print(f"Размер файла: {file_size} байт")
            
            # Читаем файл обратно для проверки
            print("\nПроверка чтения файла:")
            with open(output_file, 'rb') as f:
                data = f.read()
                print(f"Прочитано байт: {len(data)}")
                
                for i in range(0, len(data), 4):
                    if i + 4 <= len(data):
                        instr_bytes = data[i:i+4]
                        instr = int.from_bytes(instr_bytes, 'little')
                        print(f"  Байты {i}-{i+3}: {instr_bytes.hex()} -> 0x{instr:08x}")
                        
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    else:
        print("Ничего не скомпилировано!")

def test_simple():
    """Еще более простой тест"""
    print("\n" + "=" * 60)
    print("ПРОСТОЙ ТЕСТ ОДНОЙ ИНСТРУКЦИИ:")
    print("=" * 60)
    
    parser = Parser(INSTRUCTIONS)
    compiler = Compiler(parser)
    
    # Тестируем addi
    test_line = "addi x1, x0, 42"
    print(f"Тест: '{test_line}'")
    
    try:
        instr_def, args, errors, warnings = parser.parse_line(test_line, 1)
        
        if instr_def:
            print(f"Инструкция: {instr_def.name}")
            print(f"Аргументы: {args}")
            
            instruction = compiler.compile_instruction(instr_def, args)
            print(f"Машинный код: 0x{instruction:08x}")
            
            # Сохраняем
            with open("single_instruction.bin", 'wb') as f:
                f.write(instruction.to_bytes(4, 'little'))
            print("Сохранено в single_instruction.bin")
            
            # Проверяем
            with open("single_instruction.bin", 'rb') as f:
                data = f.read()
                print(f"Файл: {len(data)} байт: {data.hex()}")
        else:
            print("Не распознано как инструкция!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_compilation()
    test_simple()
    
    print("\n" + "=" * 60)
    print("ПРОВЕРКА ФАЙЛОВ:")
    print("=" * 60)
    
    # Проверяем существование файлов
    for filename in ["debug_output.bin", "single_instruction.bin"]:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"{filename}: существует, размер {size} байт")
            
            if size > 0:
                with open(filename, 'rb') as f:
                    content = f.read()
                    print(f"  Содержимое (hex): {content.hex()}")
                    print(f"  Содержимое (raw): {content}")
            else:
                print(f"  ФАЙЛ ПУСТОЙ!")
        else:
            print(f"{filename}: не существует")