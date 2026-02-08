"""
Классы ошибок ассемблера
"""

class AssemblyError(Exception):
    """Ошибка ассемблера"""
    def __init__(self, message, line_num=0):
        self.message = message
        self.line_num = line_num
        super().__init__(f"Line {line_num}: {message}")

class AssemblyWarning:
    """Предупреждение ассемблера"""
    def __init__(self, message, line_num=0):
        self.message = message
        self.line_num = line_num
    
    def __str__(self):
        return f"Line {self.line_num}: {self.message}"