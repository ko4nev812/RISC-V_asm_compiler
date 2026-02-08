"""
Парсер ассемблерного кода
"""

import re
from .errors import AssemblyError

class Parser:
    def __init__(self, instructions_def):
        self.instructions = instructions_def
        self.labels = {}
        self.current_address = 0  # Текущий адрес для меток
        
    def parse_line(self, line, line_num):
        """Парсинг одной строки ассемблера"""
        # Сохраняем оригинал для сообщений об ошибках
        original_line = line
        
        # Удаляем комментарии (всё после #)
        if '#' in line:
            line = line.split('#')[0]
        
        line = line.strip()
        
        # Пропускаем пустые строки
        if not line:
            return None, [], [], []
        
        # Проверка на метку (метка в начале строки)
        label = None
        if ':' in line:
            parts = line.split(':', 1)
            possible_label = parts[0].strip()
            
            # Проверяем, что это валидная метка (только буквы/цифры/_)
            if possible_label and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', possible_label):
                label = possible_label
                # Сохраняем метку с текущим адресом
                self.labels[label] = self.current_address
                
                # Если после метки ничего нет
                if len(parts) == 1 or not parts[1].strip():
                    return None, [], [], []
                
                # Продолжаем парсинг после метки
                line = parts[1].strip()
        
        # Разбираем оставшуюся часть строки (инструкцию)
        # Разделяем по запятым и пробелам
        parts = re.split(r'[,\s]+', line)
        
        # Убираем пустые элементы
        parts = [p.strip() for p in parts if p.strip()]
        
        if not parts:
            return None, [], [], []
        
        mnemonic = parts[0].lower()
        
        if mnemonic not in self.instructions:
            raise AssemblyError(f"Unknown instruction '{mnemonic}'", line_num)
        
        instr_def = self.instructions[mnemonic]
        args = parts[1:]
        
        # Проверка аргументов
        errors = []
        warnings = []
        
        # Проверка количества аргументов
        expected_args = self._get_expected_args_count(instr_def.format_type)
        if expected_args != len(args):
            errors.append(f"Expected {expected_args} arguments, got {len(args)}: {args}")
        
        # Вызываем проверки из определения инструкции
        if instr_def.checks:
            for check in instr_def.checks:
                try:
                    result = check(args)
                    if result:
                        if "ERROR" in result.upper():
                            errors.append(result)
                except Exception as e:
                    errors.append(f"Check failed: {str(e)}")
        
        # Увеличиваем адрес для следующей инструкции (4 байта на инструкцию RISC-V)
        self.current_address += 4
        
        return instr_def, args, errors, warnings
    
    def _get_expected_args_count(self, format_type):
        """Количество ожидаемых аргументов для формата"""
        counts = {
            'R': 3,  # rd, rs1, rs2
            'I': 3,  # rd, rs1, imm
            'S': 3,  # rs1, rs2, imm (фактически rs2, rs1, imm в коде)
            'B': 3,  # rs1, rs2, imm
            'U': 2,  # rd, imm
            'J': 2,  # rd, imm
        }
        return counts.get(format_type, 0)
    
    def parse_register(self, reg_str):
        """Парсинг регистра (x0-x31)"""
        if not isinstance(reg_str, str):
            raise ValueError(f"Invalid register: {reg_str}")
        
        reg_str = reg_str.strip().lower()
        
        # Поддержка регистров по именам
        reg_aliases = {
            'zero': 'x0', 'ra': 'x1', 'sp': 'x2', 'gp': 'x3',
            'tp': 'x4', 't0': 'x5', 't1': 'x6', 't2': 'x7',
            's0': 'x8', 'fp': 'x8', 's1': 'x9',
            'a0': 'x10', 'a1': 'x11', 'a2': 'x12', 'a3': 'x13',
            'a4': 'x14', 'a5': 'x15', 'a6': 'x16', 'a7': 'x17',
            's2': 'x18', 's3': 'x19', 's4': 'x20', 's5': 'x21',
            's6': 'x22', 's7': 'x23', 's8': 'x24', 's9': 'x25',
            's10': 'x26', 's11': 'x27',
            't3': 'x28', 't4': 'x29', 't5': 'x30', 't6': 'x31'
        }


        
        # Если это алиас, конвертируем
        if reg_str in reg_aliases:
            reg_str = reg_aliases[reg_str]
        
        # Проверяем формат xN or rN
        if reg_str.startswith('r'):
            reg_str = 'x'+reg_str[1:]
        
        # Проверяем формат регистра
        if not reg_str.startswith('x'):
            raise ValueError(f"Invalid register format: '{reg_str}'. Expected x0-x31 or r0-r31")
        
        try:
            reg_num = int(reg_str[1:])
            if not (0 <= reg_num <= 31):
                raise ValueError(f"Register number out of range: {reg_num}. Must be 0-31")
            return reg_num
        except ValueError:
            raise ValueError(f"Invalid register number: '{reg_str[1:]}'")
    
    def parse_immediate(self, imm_str, line_num=0):
        """Парсинг непосредственного значения"""
        if not isinstance(imm_str, str):
            raise ValueError(f"Invalid immediate: {imm_str}")
        
        imm_str = imm_str.strip().lower()
        
        try:
            # Шестнадцатеричное (0x...)
            if imm_str.startswith('0x'):
                return int(imm_str, 16)
            # Двоичное (0b...)
            elif imm_str.startswith('0b'):
                return int(imm_str, 2)
            # Десятичное (может быть отрицательным)
            else:
                # Проверяем на метку
                if imm_str in self.labels:
                    return self.labels[imm_str]
                
                # Пробуем парсить как число
                return int(imm_str)
        except ValueError as e:
            raise ValueError(f"Invalid immediate value '{imm_str}': {str(e)}")