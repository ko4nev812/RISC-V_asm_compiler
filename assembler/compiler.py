"""
Генератор машинного кода
"""

class Compiler:
    def __init__(self, parser):
        self.parser = parser
    
    def compile_instruction(self, instr_def, args):
        """Компиляция одной инструкции в машинный код"""
        try:
            if instr_def.format_type == 'R':
                return self._compile_r_format(instr_def, args)
            elif instr_def.format_type == 'I':
                return self._compile_i_format(instr_def, args)
            elif instr_def.format_type == 'S':
                return self._compile_s_format(instr_def, args)
            elif instr_def.format_type == 'B':
                return self._compile_b_format(instr_def, args)
            elif instr_def.format_type == 'U':
                return self._compile_u_format(instr_def, args)
            elif instr_def.format_type == 'J':
                return self._compile_j_format(instr_def, args)
            else:
                raise ValueError(f"Unknown format type: {instr_def.format_type}")
        except Exception as e:
            raise ValueError(f"Failed to compile {instr_def.name} {args}: {str(e)}")
    # ПРОВЕРЕНО ✅✅✅
    def _compile_r_format(self, instr_def, args):
        """R-формат: opcode rd rs1 rs2 funct3 funct7"""
        rd = self.parser.parse_register(args[0])
        rs1 = self.parser.parse_register(args[1])
        rs2 = self.parser.parse_register(args[2])
        
        instruction = 0
        instruction |= (instr_def.funct7 & 0x7F) << 25
        instruction |= (rs2 & 0x1F) << 20
        instruction |= (rs1 & 0x1F) << 15
        instruction |= (instr_def.funct3 & 0x7) << 12
        instruction |= (rd & 0x1F) << 7
        instruction |= (instr_def.opcode & 0x7F)
        
        return instruction
    
    # ПРОВЕРЕНО ✅✅✅
    def _compile_i_format(self, instr_def, args):
        """I-формат: opcode rd rs1 imm[11:0]"""
        rd = self.parser.parse_register(args[0])
        rs1 = self.parser.parse_register(args[1])
        imm = self.parser.parse_immediate(args[2])
        
        # Проверка диапазона
        if not (-2048 <= imm <= 2047):
            raise ValueError(f"Immediate value {imm} out of range for I-format")
        
        instruction = 0
        instruction |= (imm & 0xFFF) << 20
        instruction |= (rs1 & 0x1F) << 15
        instruction |= (instr_def.funct3 & 0x7) << 12
        instruction |= (rd & 0x1F) << 7
        instruction |= (instr_def.opcode & 0x7F)
        
        return instruction
    # НЕ ПРОВЕРЕНО! (От DeepSeek)
    def _compile_s_format(self, instr_def, args):
        """S-формат: opcode imm[11:5] rs2 rs1 funct3 imm[4:0]"""
        rs1 = self.parser.parse_register(args[0])
        rs2 = self.parser.parse_register(args[1])
        imm = self.parser.parse_immediate(args[2])
        
        # Проверка диапазона
        if not (-2048 <= imm <= 2047):
            raise ValueError(f"Immediate value {imm} out of range for S-format")
        
        instruction = 0
        instruction |= ((imm >> 5) & 0x7F) << 25
        instruction |= (rs2 & 0x1F) << 20
        instruction |= (rs1 & 0x1F) << 15
        instruction |= (instr_def.funct3 & 0x7) << 12
        instruction |= (imm & 0x1F) << 7
        instruction |= (instr_def.opcode & 0x7F)
        
        return instruction
    # НЕ ПРОВЕРЕНО!!! (От DeepSeek)
    def _compile_b_format(self, instr_def, args):
        """B-формат: opcode imm[12|10:5] rs2 rs1 funct3 imm[4:1|11]"""
        rs1 = self.parser.parse_register(args[0])
        rs2 = self.parser.parse_register(args[1])
        imm = self.parser.parse_immediate(args[2])
        
        # Проверка выравнивания
        if imm % 2 != 0:
            raise ValueError(f"B-format immediate must be 2-byte aligned")
        
        # Проверка диапазона
        if not (-4096 <= imm <= 4094):
            raise ValueError(f"Immediate value {imm} out of range for B-format")
        
        instruction = 0
        instruction |= ((imm >> 12) & 0x1) << 31
        instruction |= ((imm >> 5) & 0x3F) << 25
        instruction |= (rs2 & 0x1F) << 20
        instruction |= (rs1 & 0x1F) << 15
        instruction |= (instr_def.funct3 & 0x7) << 12
        instruction |= ((imm >> 1) & 0xF) << 8
        instruction |= ((imm >> 11) & 0x1) << 7
        instruction |= (instr_def.opcode & 0x7F)
        
        return instruction
    # НЕ ПРОВЕРЕНО!!! (От DeepSeek)
    def _compile_u_format(self, instr_def, args):
        """U-формат: opcode rd imm[31:12]"""
        rd = self.parser.parse_register(args[0])
        imm = self.parser.parse_immediate(args[1])
        
        instruction = 0
        instruction |= (imm & 0xFFFFF000)  # imm[31:12]
        instruction |= (rd & 0x1F) << 7
        instruction |= (instr_def.opcode & 0x7F)
        
        return instruction
    # НЕ ПРОВЕРЕНО!!! (От DeepSeek)
    def _compile_j_format(self, instr_def, args):
        """J-формат: opcode rd imm[20|10:1|11|19:12]"""
        rd = self.parser.parse_register(args[0])
        imm = self.parser.parse_immediate(args[1])
        
        # Проверка выравнивания
        if imm % 2 != 0:
            raise ValueError(f"J-format immediate must be 2-byte aligned")
        
        instruction = 0
        instruction |= ((imm >> 20) & 0x1) << 31
        instruction |= ((imm >> 1) & 0x3FF) << 21
        instruction |= ((imm >> 11) & 0x1) << 20
        instruction |= ((imm >> 12) & 0xFF) << 12
        instruction |= (rd & 0x1F) << 7
        instruction |= (instr_def.opcode & 0x7F)
        
        return instruction