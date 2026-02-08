from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextBrowser, 
                            QPushButton, QHBoxLayout, QComboBox)
from PyQt5.QtCore import Qt
from assembler.instructions import INSTRUCTIONS

class DocumentationWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('RISC-V Instruction Documentation')
        self.setGeometry(200, 200, 700, 550)
        
        # Устанавливаем темную тему для этого окна
        self.set_dark_theme()
        
        self.init_ui()
        self.load_instructions()
    
    def set_dark_theme(self):
        """Темная тема для окна документации"""
        self.setStyleSheet("""
            DocumentationWindow {
                background-color: #2d2d30;
            }
            
            QComboBox {
                background-color: #3e3e42;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #505050;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d30;
                color: #d4d4d4;
                selection-background-color: #505050;
            }
            
            QPushButton {
                background-color: #3e3e42;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #505050;
                border: 1px solid #505050;
            }
            QPushButton:pressed {
                background-color: #2a2a2e;
            }
            
            QTextBrowser {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QTextBrowser a {
                color: #4ec9b0;
                text-decoration: none;
            }
            QTextBrowser a:hover {
                text-decoration: underline;
            }
        """)
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Панель выбора инструкции
        top_layout = QHBoxLayout()
        
        self.instruction_combo = QComboBox()
        self.instruction_combo.setMinimumHeight(30)
        self.instruction_combo.currentTextChanged.connect(self.show_documentation)
        top_layout.addWidget(self.instruction_combo, 1)
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(30)
        close_btn.clicked.connect(self.close)
        top_layout.addWidget(close_btn)
        
        layout.addLayout(top_layout)
        
        # Браузер для отображения документации
        self.doc_browser = QTextBrowser()
        self.doc_browser.setOpenExternalLinks(True)
        layout.addWidget(self.doc_browser)
        
        self.setLayout(layout)
    
    def show_documentation(self, instruction_name):
        """Отображение документации с темными стилями"""
        if instruction_name in INSTRUCTIONS:
            instr_def = INSTRUCTIONS[instruction_name]
            if instr_def.documentation:
                html = instr_def.documentation.format_html()
                
                # HTML с темными стилями
                dark_html = f"""
                <html>
                <head>
                <style>
                    body {{
                        font-family: 'Segoe UI', Arial, sans-serif;
                        background-color: #1e1e1e;
                        color: #d4d4d4;
                        margin: 15px;
                        line-height: 1.5;
                    }}
                    h2 {{
                        color: #569cd6;
                        margin-top: 0;
                        padding-bottom: 10px;
                        border-bottom: 1px solid #3e3e42;
                    }}
                    h3 {{
                        color: #4ec9b0;
                    }}
                    code {{
                        background-color: #2d2d30;
                        color: #ce9178;
                        padding: 2px 6px;
                        border-radius: 3px;
                        font-family: Consolas, 'Courier New', monospace;
                        font-size: 0.95em;
                    }}
                    pre {{
                        background-color: #2d2d30;
                        color: #d4d4d4;
                        padding: 10px;
                        border-radius: 5px;
                        border-left: 3px solid #569cd6;
                        overflow-x: auto;
                        font-family: Consolas, 'Courier New', monospace;
                    }}
                    ul, ol {{
                        padding-left: 20px;
                    }}
                    li {{
                        margin: 8px 0;
                    }}
                    strong {{
                        color: #9cdcfe;
                    }}
                    .example {{
                        background-color: #2d2d30;
                        padding: 10px;
                        margin: 10px 0;
                        border-radius: 5px;
                        border-left: 3px solid #4ec9b0;
                    }}
                    .note {{
                        background-color: #2d2d30;
                        padding: 10px;
                        margin: 10px 0;
                        border-radius: 5px;
                        border-left: 3px solid #d7ba7d;
                    }}
                    a {{
                        color: #4ec9b0;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
                </head>
                <body>
                {html}
                </body>
                </html>
                """
                self.doc_browser.setHtml(dark_html)
            else:
                self.doc_browser.setHtml(f"""
                <html>
                <body style="background-color:#1e1e1e; color:#d4d4d4;">
                <h2>{instruction_name}</h2>
                <p>No documentation available for this instruction.</p>
                </body>
                </html>
                """)
        
    def load_instructions(self):
        """Загрузка списка инструкций"""
        instructions = sorted(INSTRUCTIONS.keys())
        self.instruction_combo.addItems(instructions)
