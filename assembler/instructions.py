"""
Определения инструкций RISC-V
Каждая инструкция содержит шаблон и правила проверки
"""

class InstructionDef:
    """Определение одной инструкции"""
    
    def __init__(self, name, format_type, opcode, funct3=None, funct7=None, 
                 imm_type=None, checks=None, documentation=None):
        """
        Args:
            name: имя инструкции (add, lw, etc.)
            format_type: тип формата (R, I, S, B, U, J)
            opcode: код операции
            funct3: функция 3 (для R/I/S/B форматов)
            funct7: функция 7 (для R формата)
            imm_type: тип непосредственного значения
            checks: список функций для проверки аргументов
        """
        self.name = name
        self.format_type = format_type
        self.opcode = opcode
        self.funct3 = funct3
        self.funct7 = funct7
        self.imm_type = imm_type
        self.checks = checks or []
        self.documentation = documentation
    
    def validate(self, args):
        """Проверка аргументов инструкции"""
        errors = []
        warnings = []
        
        for check_func in self.checks:
            result = check_func(args)
            if result:
                if result.startswith("ERROR"):
                    errors.append(result)
                else:
                    warnings.append(result)
        
        return errors, warnings

class InstructionDoc:
    """Документация для инструкции"""
    def __init__(self, name, description, syntax, examples=None, notes=None):
        self.name = name
        self.description = description
        self.syntax = syntax
        self.examples = examples or []
        self.notes = notes or []
    
    def format_html(self):
        """Форматирование документации в HTML"""
        html = f"""
        <h2>{self.name}</h2>
        <p><strong>Description:</strong> {self.description}</p>
        <p><strong>Syntax:</strong> <code>{self.syntax}</code></p>
        """
        
        if self.examples:
            html += "<p><strong>Examples:</strong></p><ul>"
            for example in self.examples:
                html += f"<li><code>{example}</code></li>"
            html += "</ul>"
        
        if self.notes:
            html += "<p><strong>Notes:</strong></p><ul>"
            for note in self.notes:
                html += f"<li>{note}</li>"
            html += "</ul>"
        
        return html

# Правила проверки (можно добавлять новые)
def check_register_zero(args):
    """Проверка записи в нулевой регистр"""
    if args and (args[0] == "x0" or args[0] == "r0"):
        return f"Writing to zero register (x0) has no effect"

def check_immediate_range(value, bits, signed=True):
    """Проверка диапазона непосредственного значения"""
    if signed:
        min_val = -(2 ** (bits - 1))
        max_val = (2 ** (bits - 1)) - 1
    else:
        min_val = 0
        max_val = (2 ** bits) - 1
    
    if not (min_val <= value <= max_val):
        return f"ERROR: Immediate value {value} out of range [{min_val}, {max_val}]"
    return None


# Пример определения инструкций (вы будете добавлять свои)
INSTRUCTIONS = {
    'add': InstructionDef(
        name='add',
        format_type='R',
        opcode=0b0110011,
        funct3=0b000,
        funct7=0b0000000,
        checks=[check_register_zero],
        documentation=InstructionDoc(
            name='add',
            description='Add two registers and store the result',
            syntax='add rd, rs1, rs2',
            examples=[
                'add x1, x2, x3  # x1 = x2 + x3',
                'add x5, x6, x7  # x5 = x6 + x7'
            ],
            notes=[
                'Performs signed addition',
                'Overflow is ignored'
            ]
        )
    ),
    
    'addi': InstructionDef(
        name='addi',
        format_type='I',
        opcode=0b0010011,
        funct3=0b000,
        checks=[check_register_zero],
        documentation=InstructionDoc(
            name='addi',
            description='Add immediate value to register',
            syntax='addi rd, rs1, imm',
            examples=[
                'addi x1, x2, 42  # x1 = x2 + 42',
                'addi x3, x0, -10  # x3 = -10'
            ],
            notes=[
                'Immediate is 12-bit signed',
                'Range: -2048 to 2047'
            ]
        )
    ),
}

# Старый тип инструкций (для сохранения примеров)
INSTRUCTIONS_past = {
    'add': InstructionDef(
        name='add',
        format_type='R',
        opcode=0b0110011,
        funct3=0b000,
        funct7=0b0000000,
        checks=[check_register_zero]
    ),
    
    'addi': InstructionDef(
        name='addi',
        format_type='I',
        opcode=0b0010011,
        funct3=0b000,
        checks=[check_register_zero]
    ),
    
    'lw': InstructionDef(
        name='lw',
        format_type='I',
        opcode=0b0000011,
        funct3=0b010
    ),
    
    'sw': InstructionDef(
        name='sw',
        format_type='S',
        opcode=0b0100011,
        funct3=0b010
    ),
    
    'beq': InstructionDef(
        name='beq',
        format_type='B',
        opcode=0b1100011,
        funct3=0b000
    ),
    
    'jal': InstructionDef(
        name='jal',
        format_type='J',
        opcode=0b1101111
    ),
    
    'lui': InstructionDef(
        name='lui',
        format_type='U',
        opcode=0b0110111
    ),
}