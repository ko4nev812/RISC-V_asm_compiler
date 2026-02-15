"""
Графический интерфейс текстового редактора
"""

from PyQt5.QtWidgets import (QMainWindow, QTextEdit, QVBoxLayout, QWidget, 
                            QMenuBar, QMenu, QAction, QFileDialog, QMessageBox,
                            QLabel, QStatusBar, QHBoxLayout, QToolBar, QSplitter, QShortcut, QPlainTextEdit, QApplication)
from PyQt5.QtCore import Qt, QTimer, QSize, QRect
from PyQt5.QtGui import (QFont, QTextCursor, QColor, QPainter, 
                         QTextFormat, QSyntaxHighlighter, QTextCharFormat, QPalette, QColor, QIcon)
from PyQt5.QtCore import QMimeData
from assembler.instructions import INSTRUCTIONS
from gui.documentation_window import DocumentationWindow
from os.path import basename
from gui.errors_and_warning_color import PaintError, PaintWarning
import sys

class LineNumberArea(QWidget):
    """Виджет для отображения номеров строк"""
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor
    
    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)
class CodeEditor(QPlainTextEdit):
    """Улучшенный редактор кода с номерами строк"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Courier New", 10))

        # Для подсветки ошибок
        self.error_lines = set()
        self.warning_lines = set()

        self.setTabStopWidth(40)  # 4 пробела
        
        # Создаем область для номеров строк
        self.line_number_area = LineNumberArea(self)
        
        # Подключаем сигналы
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        
        # Настраиваем начальные параметры
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        
        # Устанавливаем темную тему (опционально)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
            }
        """)
    
    def line_number_area_width(self):
        """Вычисляем ширину области номеров строк"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        
        space = 10 + self.fontMetrics().width('9') * digits
        return space
    
    def update_line_number_area_width(self, _):
        """Обновляем ширину области номеров строк"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect, dy):
        """Обновляем область номеров строк при прокрутке"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), 
                                       self.line_number_area.width(), 
                                       rect.height())
        
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    
    def resizeEvent(self, event):
        """Обработка изменения размера"""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), 
                  self.line_number_area_width(), cr.height())
        )
    
    def line_number_area_paint_event(self, event):
        """Отрисовка номеров строк"""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2d2d30"))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(
            self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        painter.setPen(QColor("#858585"))
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(0, int(top), 
                               self.line_number_area.width() - 5, 
                               self.fontMetrics().height(),
                               Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
    
    def highlight_current_line(self):
        """Подсветка текущей строки"""
        extra_selections = []
        
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#2f2f32")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        
        self.setExtraSelections(extra_selections)
    
    def insertFromMimeData(self, source: QMimeData):
        """Вставка только текста без форматирования"""
        if source.hasText():
            cursor = self.textCursor()
            cursor.insertText(source.text())
        else:
            super().insertFromMimeData(source)
    
    def contextMenuEvent(self, event):
        """Контекстное меню с опцией документации"""
        menu = self.createStandardContextMenu()
        
        # Получаем слово под курсором
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.clearSelection()
        
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText()
        
        # Проверяем, что word - строка и не пустая
        if isinstance(word, str) and word.strip():
            word_lower = word.lower().strip()
            
            # Проверяем, является ли слово инструкцией
            try:
                from assembler.instructions import INSTRUCTIONS
                
                if word_lower in INSTRUCTIONS:
                    menu.addSeparator()
                    doc_action = menu.addAction(f"📖 Documentation for '{word}'")
                    
                    # Находим главное окно
                    main_window = self.find_main_window()
                    
                    if main_window and hasattr(main_window, 'show_documentation'):
                        # Используем partial вместо lambda для избежания проблем с замыканием
                        from functools import partial
                        doc_action.triggered.connect(
                            partial(self.show_instruction_doc, word_lower, main_window)
                        )
                        
            except ImportError:
                pass  # Модуль инструкций не загружен
        
        menu.exec_(event.globalPos())

    def find_main_window(self):
        """Находит главное окно приложения"""
        from PyQt5.QtWidgets import QApplication, QMainWindow
        
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QMainWindow):
                return widget
        return None

    def show_instruction_doc(self, word, main_window):
        """Показ документации для инструкции"""
        if not word or not main_window:
            return
        
        # Показываем окно документации
        main_window.show_documentation()
        
        # Устанавливаем выбранную инструкцию
        if (hasattr(main_window, 'doc_window') and 
            main_window.doc_window and 
            hasattr(main_window.doc_window, 'instruction_combo')):
            
            # Проверяем, что word - строка
            if isinstance(word, str):
                main_window.doc_window.instruction_combo.setCurrentText(word.lower())
    
    def show_instruction_doc(self, word, main_window):
        """Показ документации для инструкции"""
        main_window.show_documentation()
        if hasattr(main_window, 'doc_window'):
            main_window.doc_window.instruction_combo.setCurrentText(word.lower())













class AssemblerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.doc_window = None
        self.setWindowIcon(QIcon("gui\\icon.ico"))
        self.init_ui()
        self.last_machine_code = []
        
    def init_ui(self):
        self.set_dark_theme()
        self.setWindowTitle('RISC-V Assembler compiler v0.1')
        self.setGeometry(100, 100, 900, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        
        # Splitter для разделения редактора и вывода
        splitter = QSplitter(Qt.Vertical)
        
        # Текстовый редактор
        self.editor = CodeEditor()
        splitter.addWidget(self.editor)
        
        # Панель вывода ошибок
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        #self.output_text.setMaximumHeight(300)
        self.output_text.setFont(QFont("Courier", 9))
        splitter.addWidget(self.output_text)
        
        splitter.setSizes([450, 150])
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Создание меню
        self.create_menu()
        
        # Создание тулбара
        self.create_toolbar()
        
        # Таймер для динамической проверки
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_syntax)
        self.check_timer.start(1000)  # Проверка каждую секунду

        docs_shortcut = QShortcut("F1", self)  # F1 для документации
        docs_shortcut.activated.connect(self.show_documentation)
        
    def create_menu(self):
        menubar = self.menuBar()
        
        # Меню File
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As', self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Build
        build_menu = menubar.addMenu('Build')
        
        compile_action = QAction('Compile', self)
        compile_action.triggered.connect(self.compile_code)
        build_menu.addAction(compile_action)
        
        compile_save_action = QAction('Compile and Save', self)
        compile_save_action.triggered.connect(self.compile_and_save)
        build_menu.addAction(compile_save_action)

        # Меню Help
        help_menu = menubar.addMenu('Help')  # <-- Добавляем
        
        docs_action = QAction('Instruction Documentation', self)  # <-- Новая кнопка
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        help_menu.addSeparator()
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        toolbar = self.addToolBar('Main')
        
        # Кнопки тулбара
        toolbar.addAction('New', self.new_file)
        toolbar.addAction('Open', self.open_file)
        toolbar.addAction('Save', self.save_file)
        toolbar.addSeparator()
    
        # Кнопка компиляции
        compile_btn = QAction('▶ Compile', self)
        compile_btn.setToolTip('Compile current code')
        compile_btn.triggered.connect(self.compile_code)
        toolbar.addAction(compile_btn)
        
        # Кнопка компиляции и сохранения
        compile_save_btn = QAction('💾 Compile & Save', self)
        compile_save_btn.setToolTip('Compile and save machine code')
        compile_save_btn.triggered.connect(self.compile_and_save)
        toolbar.addAction(compile_save_btn)
        
        toolbar.addSeparator()
        
        # Кнопка документации
        docs_action = QAction('📚 Docs', self)
        docs_action.setToolTip('Show Instruction Documentation')
        docs_action.triggered.connect(self.show_documentation)
        toolbar.addAction(docs_action)
        
    def new_file(self):
        self.editor.clear()
        self.current_file = None
        self.status_bar.showMessage("New file created")
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Assembly File", "", "Assembly Files (*.asm *.s);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    self.editor.setPlainText(content)
                    self.current_file = file_path
                    self.status_bar.showMessage(f"Opened: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
    
    def save_file(self):
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Assembly File", "", "Assembly Files (*.asm);;All Files (*)"
        )
        
        if file_path:
            self._save_to_file(file_path)
            self.current_file = file_path
    
    def _save_to_file(self, file_path):
        try:
            with open(file_path, 'w') as f:
                f.write(self.editor.toPlainText())
            self.status_bar.showMessage(f"Saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
    
    def check_syntax(self):
        """Динамическая проверка синтаксиса"""
        # Здесь будет вызов парсера для проверки
        # Пока просто очищаем вывод
        pass
    
    def compile_code(self):
        """Компиляция кода из GUI"""
        code = self.editor.toPlainText()
        
        if not code.strip():
            self.output_text.setText("No code to compile")
            self.last_machine_code = []  # Сбрасываем
            return
        
        self.output_text.clear()
        self.output_text.append("Starting compilation...\n")
        
        try:
            from assembler.instructions import INSTRUCTIONS
            from assembler.parser import Parser
            from assembler.compiler import Compiler
            
            parser = Parser(INSTRUCTIONS)
            compiler = Compiler(parser)
            
            lines = code.split('\n')
            machine_code = []
            errors_found = False
            
            # Сбрасываем список меток и адрес перед компиляцией
            parser.labels.clear()
            parser.current_address = 0
            
            # Первый проход: сбор меток
            self.output_text.append("Pass 1: Collecting labels...")
            for i, line in enumerate(lines, 1):
                line_clean = line.strip()
                if not line_clean or line_clean.startswith('#'):
                    continue
                
                try:
                    # Пытаемся распарсить для сбора меток
                    parser.parse_line(line, i)
                except:
                    pass  # Игнорируем ошибки в первом проходе
            
            self.output_text.append(f"Found labels: {list(parser.labels.keys())}")
            
            # Второй проход: компиляция
            self.output_text.append("\nPass 2: Compiling...")
            parser.current_address = 0  # Сбрасываем адрес
            
            for i, line in enumerate(lines, 1):
                line_clean = line.rstrip()
                if not line_clean or line_clean.startswith('#'):
                    continue
                
                try:
                    instr_def, args, errors, warnings = parser.parse_line(line_clean, i)
                    
                    if errors:
                        for err in errors:
                            self.output_text.append(PaintError(f"Line {i}: ERROR: {err}"))
                            errors_found = True
                    
                    if warnings:
                        for warn in warnings:
                            self.output_text.append(PaintWarning(f"Line {i}: WARNING: {warn}"))
                    
                    if instr_def and not errors:
                        try:
                            errors, warnings = instr_def.validate(args)
                            if errors:
                                raise Exception(errors[0])
                            if warnings:
                                for warn in warnings:
                                    self.output_text.append(PaintWarning(f"Line {i}: ❗ WARNING: {warn}"))
                            instruction = compiler.compile_instruction(instr_def, args)
                            machine_code.append(instruction)
                            self.output_text.append(f"Line {i}: ✓ {instr_def.name} {args} -> 0x{instruction:08x}")
                        except Exception as e:
                            self.output_text.append(PaintError(f"Line {i}: ✗ COMPILATION ERROR: {str(e)}"))
                            errors_found = True
                            
                except Exception as e:
                    self.output_text.append(PaintError(f"Line {i}: ✗ PARSE ERROR: {str(e)}"))
                    errors_found = True
            
            # Сохраняем результат для последующего сохранения в файл
            self.last_machine_code = machine_code
            
            if errors_found:
                self.output_text.append("\n❌ Compilation failed with errors!")
                self.status_bar.showMessage("Compilation failed")
            else:
                self.output_text.append(f"\n✅ Compilation successful!")
                self.output_text.append(f"Generated {len(machine_code)} instructions ({len(machine_code) * 4} bytes)")
                self.status_bar.showMessage(f"Compilation successful: {len(machine_code)} instructions")
                
        except Exception as e:
            self.output_text.append(PaintError(f"❌ Fatal error: {str(e)}"))
            import traceback
            self.output_text.append(traceback.format_exc())
            self.last_machine_code = []  # Сбрасываем при ошибке
    
    def compile_and_save(self):
        """Компиляция и сохранение машинного кода"""
        # Сначала компилируем
        self.compile_code()
        
        # Проверяем, есть ли что сохранять
        if not self.last_machine_code:
            self.output_text.append("\n⚠️ No machine code to save. Compilation may have failed or produced no output.")
            return
        
        # Открываем диалог сохранения
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Machine Code", "", 
            "Binary Files (*.bin);;Hex Files (*.hex);;Mem Files (*.mem);;All Files (*)"
        )
        
        if file_path:
            try:
                # Определяем формат по расширению
                if file_path.lower().endswith('.hex'):
                    self._save_hex_file(file_path)
                elif file_path.lower().endswith('.mem'):
                    self._save_mem_file(file_path)
                else:
                    self._save_binary_file(file_path)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
    
    def _save_binary_file(self, file_path):
        """Сохранение в бинарном формате"""
        with open(file_path, 'wb') as f:
            for instruction in self.last_machine_code:
                # Записываем 4 байта little-endian
                f.write(instruction.to_bytes(4, byteorder='little'))
        
        # Проверяем размер файла
        import os
        file_size = os.path.getsize(file_path)
        
        self.output_text.append(f"\n💾 Saved {len(self.last_machine_code)} instructions to: {file_path}")
        self.output_text.append(f"File size: {file_size} bytes")
        self.status_bar.showMessage(f"Saved to {basename(file_path)} ({file_size} bytes)")
        
        # Показываем подтверждение
        '''
        QMessageBox.information(self, "Success", 
                              f"Successfully saved {len(self.last_machine_code)} instructions\n"
                              f"File: {file_path}\n"
                              f"Size: {file_size} bytes")
        '''
    
    def _save_hex_file(self, file_path):
        """Сохранение в текстовом hex формате (для отладки)"""
        with open(file_path, 'w') as f:
            f.write("# RISC-V Machine Code (hex)\n")
            f.write(f"# Generated from: {self.current_file or 'Untitled'}\n")
            f.write(f"# Instructions: {len(self.last_machine_code)}\n\n")
            
            for idx, instruction in enumerate(self.last_machine_code):
                # Формат: address: instruction
                f.write(f"0x{idx*4:08x}: 0x{instruction:08x}\n")
        
        self.output_text.append(f"\n💾 Saved hex file: {file_path}")
        self.status_bar.showMessage(f"Saved hex file: {basename(file_path)}")
    
    def _save_mem_file(self, file_path):
        """Сохранение в текстовом hex формате с расширением .mem"""
        with open(file_path, 'w') as f:
            
            for idx, instruction in enumerate(self.last_machine_code):
                # Формат: instruction
                f.write(f"{instruction:08x}\n")
        
        self.output_text.append(f"\n💾 Saved mem file: {file_path}")
        self.status_bar.showMessage(f"Saved mem file: {basename(file_path)}")
    
    def show_documentation(self):
        """Показ окна документации"""
        if self.doc_window is None:
            self.doc_window = DocumentationWindow(self)
        
        self.doc_window.show()
        self.doc_window.raise_()  # Поднимаем окно на передний план
    
    def show_about(self):
        """Окно 'О программе'"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "About RISC-V Assembler compiler",
                         "RISC-V 32-bit Assembler\n\n"
                         "A simple assembler for RISC-V ISA\n"
                         "with instruction documentation support.\n"
                         "version 0.1")
    
    def set_dark_theme(self):
        """Устанавливает темную тему для всего приложения"""
        
        # Создаем темную палитру
        dark_palette = QPalette()
        
        # Базовые цвета
        dark_color = QColor(45, 45, 48)       # #2d2d30
        darker_color = QColor(30, 30, 30)     # #1e1e1e
        darkest_color = QColor(15, 15, 15)    # #0f0f0f
        
        text_color = QColor(212, 212, 212)    # #d4d4d4
        highlight_color = QColor(42, 130, 218)# #2a82da
        disabled_color = QColor(128, 128, 128)# #808080
        
        button_color = QColor(62, 62, 66)     # #3e3e42
        button_hover = QColor(82, 82, 86)     # #525256
        button_pressed = QColor(42, 42, 46)   # #2a2a2e
        
        # Настраиваем палитру
        dark_palette.setColor(QPalette.Window, dark_color)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, darker_color)
        dark_palette.setColor(QPalette.AlternateBase, dark_color)
        dark_palette.setColor(QPalette.ToolTipBase, darkest_color)
        dark_palette.setColor(QPalette.ToolTipText, text_color)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Button, button_color)
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Link, highlight_color)
        dark_palette.setColor(QPalette.Highlight, highlight_color)
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Disabled colors
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
        dark_palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
        dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText, disabled_color)
        
        # Устанавливаем палитру
        QApplication.setPalette(dark_palette)
        
        # Стили для конкретных виджетов
        self.setStyleSheet("""
            /* Главное окно */
            QMainWindow {
                background-color: #2d2d30;
            }
            
            /* Меню */
            QMenuBar {
                background-color: #3e3e42;
                color: #d4d4d4;
                border-bottom: 1px solid #1e1e1e;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenuBar::item:pressed {
                background-color: #2a2a2e;
            }
            
            /* Выпадающее меню */
            QMenu {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #1e1e1e;
            }
            QMenu::item {
                background-color: transparent;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1e1e1e;
                margin: 5px 10px;
            }
            
            /* Панель инструментов */
            QToolBar {
                background-color: #3e3e42;
                border: none;
                spacing: 5px;
                padding: 2px;
            }
            QToolBar::separator {
                width: 1px;
                background-color: #1e1e1e;
                margin: 0 5px;
            }
            
            /* Кнопки на тулбаре */
            QToolButton {
                background-color: #3e3e42;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 5px;
                min-width: 30px;
            }
            QToolButton:hover {
                background-color: #505050;
                border: 1px solid #505050;
            }
            QToolButton:pressed {
                background-color: #2a2a2e;
                border: 1px solid #2a2a2e;
            }
            QToolButton:checked {
                background-color: #2a2a2e;
                border: 1px solid #505050;
            }
            
            /* Статус бар */
            QStatusBar {
                background-color: #3e3e42;
                color: #d4d4d4;
            }
            QStatusBar::item {
                border: none;
            }
            
            /* Кнопки в диалогах */
            QPushButton {
                background-color: #3e3e42;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 5px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #505050;
                border: 1px solid #505050;
            }
            QPushButton:pressed {
                background-color: #2a2a2e;
                border: 1px solid #2a2a2e;
            }
            QPushButton:disabled {
                background-color: #2d2d30;
                color: #808080;
                border: 1px solid #2d2d30;
            }
            
            /* Текстовые поля */
            QTextEdit, QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                selection-background-color: #264f78;
            }
            
            /* Выпадающие списки */
            QComboBox {
                background-color: #3e3e42;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 3px;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #505050;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #d4d4d4;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d30;
                color: #d4d4d4;
                selection-background-color: #505050;
                border: 1px solid #3e3e42;
            }
            
            /* Сплиттеры */
            QSplitter::handle {
                background-color: #3e3e42;
            }
            QSplitter::handle:hover {
                background-color: #505050;
            }
            
            /* Диалоговые окна */
            QDialog {
                background-color: #2d2d30;
            }
            
            /* Заголовки */
            QLabel {
                color: #d4d4d4;
            }
            
            /* Скроллбары */
            QScrollBar:vertical {
                background-color: #2d2d30;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3e3e42;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
            QScrollBar::handle:vertical:pressed {
                background-color: #2a2a2e;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #2d2d30;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #3e3e42;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #505050;
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: #2a2a2e;
            }
        """)