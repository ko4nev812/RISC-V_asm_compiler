"""
Главный файл с поддержкой GUI и CLI режимов
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from assembler.instructions import INSTRUCTIONS
from assembler.parser import Parser
from assembler.compiler import Compiler
from gui.editor import AssemblerGUI

def compile_file(input_file, output_file=None):
    """Компиляция файла в CLI режиме"""
    print(f"Compiling {input_file}...")
    
    try:
        with open(input_file, 'r') as f:
            code = f.read()
        
        print(f"Code length: {len(code)} characters")
        print("Code content:")
        print("=" * 50)
        print(code)
        print("=" * 50)
        
        # Создаем парсер и компилятор
        from assembler.instructions import INSTRUCTIONS
        parser = Parser(INSTRUCTIONS)
        compiler = Compiler(parser)
        
        lines = code.split('\n')
        machine_code = []
        
        print(f"\nParsing {len(lines)} lines...")
        
        # Первый проход: сбор меток
        parser.current_address = 0
        for i, line in enumerate(lines, 1):
            line_clean = line.strip()
            if not line_clean or line_clean.startswith('#'):
                continue
            
            # Парсим для сбора меток
            try:
                instr_def, args, errors, warnings = parser.parse_line(line, i)
                if errors:
                    print(f"Line {i}: Errors: {errors}")
            except Exception as e:
                # Игнорируем ошибки парсинга в первом проходе
                pass
        
        print(f"Labels found: {parser.labels}")
        
        # Второй проход: компиляция
        parser.current_address = 0  # Сбрасываем адрес
        for i, line in enumerate(lines, 1):
            line_clean = line.rstrip()
            if not line_clean or line_clean.startswith('#'):
                print(f"Line {i}: Skipped (empty or comment)")
                continue
            
            print(f"\nLine {i}: '{line_clean}'")
            
            try:
                instr_def, args, errors, warnings = parser.parse_line(line_clean, i)
                
                if errors:
                    for err in errors:
                        print(f"  ERROR: {err}")
                    return False
                
                if warnings:
                    for warn in warnings:
                        print(f"  WARNING: {warn}")
                
                if instr_def:
                    print(f"  Instruction: {instr_def.name}")
                    print(f"  Arguments: {args}")
                    print(f"  Format: {instr_def.format_type}")
                    
                    try:
                        errors, warnings = instr_def.validate(args)
                        if errors:
                            raise Exception(errors[0])
                        for warn in warnings:
                            if warn:
                                print(f"  WARNING: {warn}")
                        instruction = compiler.compile_instruction(instr_def, args)
                        machine_code.append(instruction)
                        print(f"  Machine code: 0x{instruction:08x}")
                        print(f"  Binary: {instruction:032b}")
                    except Exception as e:
                        print(f"  COMPILATION ERROR: {str(e)}")
                        return False
                else:
                    print(f"  No instruction (label only)")
                    
            except Exception as e:
                print(f"  PARSE ERROR: {str(e)}")
                return False
        
        print(f"\nCompilation completed successfully!")
        print(f"Generated {len(machine_code)} instructions")
        
        if output_file:
            with open(output_file, 'wb') as f:
                for instruction in machine_code:
                    # Запись 32-битной инструкции как 4 байта (little-endian)
                    f.write(instruction.to_bytes(4, byteorder='little'))
            print(f"Saved to {output_file}")
            print(f"File size: {len(machine_code) * 4} bytes")
        else:
            # Вывод в hex
            print("\nMachine code:")
            for i, instr in enumerate(machine_code):
                print(f"  0x{i*4:08x}: 0x{instr:08x}")
        
        return True
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Точка входа программы"""
    
    # Проверка аргументов командной строки
    if len(sys.argv) > 1:
        # CLI режим
        input_file = sys.argv[1]
        
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        else:
            # Генерация имени выходного файла
            base_name = os.path.splitext(input_file)[0]
            output_file = base_name + ".bin"
        
        success = compile_file(input_file, output_file)
        sys.exit(0 if success else 1)
    
    else:
        # GUI режим
        app = QApplication(sys.argv)
        
        # Настройка темной темы (опционально)
        app.setStyle('Fusion')
        
        window = AssemblerGUI()
        window.show()
        
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()