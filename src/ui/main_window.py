import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QLabel, QSizePolicy, QPushButton, QFrame, QSpacerItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCharFormat, QTextCursor, QColor, QPalette

# Importa tus analizadores y detectores
from analizador_lexico.lexer_python import LexerPython
from analizador_lexico.lexer_pascal import LexerPascal
from analizador_lexico.lexer_plsql import LexerPLSQL
from analizador_lexico.lexer_javascript import LexerJavaScript
from analizador_lexico.lexer_cpp import LexerCPP
from analizador_lexico.lexer_tsql import LexerTSQL
from analizador_sintactico.parser_python import ParserPython
from analizador_sintactico.parser_pascal import ParserPascal
from analizador_sintactico.parser_plsql import ParserPLSQL
from analizador_sintactico.parser_javascript import ParserJavaScript
from analizador_sintactico.parser_cpp import ParserCPP
from analizador_sintactico.parser_tsql import ParserTSQL
from detector_lenguaje.detector import detectar_lenguaje

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CompilaSim Pro")
        self.setMinimumSize(950, 540)
        # Tema oscuro, sin transparencia para fondo opaco
        # self.setWindowOpacity(0.9)  # Eliminado para opacidad total
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(30, 32, 38))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(36, 38, 45))
        dark_palette.setColor(QPalette.AlternateBase, QColor(44, 47, 56))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(44, 47, 56))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Highlight, QColor(60, 120, 200))
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(dark_palette)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #23262e, stop:0.5 #3a3a6a, stop:1 #1e3c72);
                color: #f0f0f0;
            }
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #23242b, stop:1 #2c5364);
                color: #f8f8f2;
                border-radius: 8px;
                padding: 8px;
                border: 1.5px solid #5e81ac;
            }
            QLabel {
                color: #f0f0f0;
            }
            /* Etiqueta de lenguaje detectado */
            QLabel#langLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ffb347, stop:1 #ffcc33);
                color: #23262e;
                border-radius: 8px;
                padding: 4px 8px;
                border: 1.5px solid #ffd54f;
                font-weight: bold;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #43cea2, stop:1 #185a9d);
                color: #fff;
                border-radius: 6px;
                padding: 6px 18px;
                font-weight: bold;
                border: none;
                box-shadow: 0 2px 8px rgba(30,60,114,0.2);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ff512f, stop:1 #dd2476);
            }
        """)
        main_layout = QVBoxLayout()

        # Título
        titulo = QLabel("CompilaSim Pro")
        titulo.setFont(QFont("Arial", 18, QFont.Bold))
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("QLabel { color: #fff; background: transparent; }")
        main_layout.addWidget(titulo)

        # Layout horizontal principal
        layout = QHBoxLayout()

        # Panel izquierdo: entrada de código
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Escribe tu código aquí...")
        self.editor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setStyleSheet(
            "QTextEdit { border-radius: 8px; padding: 8px; background: #23242b; color: #f8f8f2; border: 1px solid #444; }"
        )
        layout.addWidget(self.editor, 2)

        # Panel derecho: resultados
        right_panel = QVBoxLayout()

        # Etiqueta de lenguaje detectado
        self.lang_label = QLabel("")
        self.lang_label.setObjectName("langLabel")
        self.lang_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.lang_label.setAlignment(Qt.AlignCenter)
        self.lang_label.setStyleSheet(
            "QLabel { background: #393e4b; border-radius: 8px; padding: 4px 8px; color: #ffd54f; border: 1px solid #555; }"
        )
        right_panel.addWidget(self.lang_label)

        self.result_label = QLabel("Resultados del análisis:")
        self.result_label.setAlignment(Qt.AlignLeft)
        self.result_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.result_label.setStyleSheet("QLabel { color: #fff; background: transparent; }")
        right_panel.addWidget(self.result_label)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setFont(QFont("Consolas", 11))
        self.result_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_area.setStyleSheet(
            "QTextEdit { background: #23242b; color: #f8f8f2; border-radius: 8px; padding: 8px; border: 1px solid #444; }"
        )
        right_panel.addWidget(self.result_area, 10)

        # Botones
        btn_layout = QHBoxLayout()
        # Botón para cargar archivo
        self.load_file_btn = QPushButton("Cargar archivo")
        self.load_file_btn.setStyleSheet(
            "QPushButton { background: #8d6e63; color: white; border-radius: 6px; padding: 6px 18px; font-weight: bold; border: none; } "
            "QPushButton:hover { background: #bcaaa4; }"
        )
        self.load_file_btn.clicked.connect(self.cargar_archivo)
        btn_layout.addWidget(self.load_file_btn)
        self.clear_btn = QPushButton("Limpiar")
        self.clear_btn.setStyleSheet(
            "QPushButton { background: #c62828; color: white; border-radius: 6px; padding: 6px 18px; font-weight: bold; border: none; } "
            "QPushButton:hover { background: #e57373; }"
        )
        self.clear_btn.clicked.connect(self.limpiar)
        self.copy_btn = QPushButton("Copiar resultado")
        self.copy_btn.setStyleSheet(
            "QPushButton { background: #1976d2; color: white; border-radius: 6px; padding: 6px 18px; font-weight: bold; border: none; } "
            "QPushButton:hover { background: #64b5f6; }"
        )
        self.copy_btn.clicked.connect(self.copiar_resultado)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.copy_btn)

        # Nuevos botones para mostrar tokens y AST
        self.show_tokens_btn = QPushButton("Ver Tokens")
        self.show_tokens_btn.setStyleSheet(
            "QPushButton { background: #00bcd4; color: white; border-radius: 6px; padding: 6px 18px; font-weight: bold; border: none; } "
            "QPushButton:hover { background: #4fc3f7; }"
        )
        self.show_tokens_btn.clicked.connect(self.show_tokens_dialog)
        self.show_ast_btn = QPushButton("Ver AST")
        self.show_ast_btn.setStyleSheet(
            "QPushButton { background: #ffb300; color: white; border-radius: 6px; padding: 6px 18px; font-weight: bold, border: none; } "
            "QPushButton:hover { background: #ffd54f; }"
        )
        self.show_ast_btn.clicked.connect(self.show_ast_dialog)
        btn_layout.addWidget(self.show_tokens_btn)
        btn_layout.addWidget(self.show_ast_btn)

        # Botón para mostrar simulación
        self.show_sim_btn = QPushButton("Ver Simulación")
        self.show_sim_btn.setStyleSheet(
            "QPushButton { background: #00bfae; color: white; border-radius: 6px; padding: 6px 18px; font-weight: bold; border: none; } "
            "QPushButton:hover { background: #1de9b6; }"
        )
        self.show_sim_btn.clicked.connect(self.show_simulation_dialog)
        btn_layout.addWidget(self.show_sim_btn)

        right_panel.addLayout(btn_layout)

        layout.addLayout(right_panel, 3)
        main_layout.addLayout(layout)
        self.setLayout(main_layout)
        self.editor.textChanged.connect(self.analizar_codigo)

        # Variables para almacenar tokens y AST
        self.tokens = []
        self.ast = None
        self.sim_output = ""  # Nueva variable para salida de simulación

    def limpiar(self):
        self.editor.clear()
        self.result_area.clear()
        self.lang_label.setText("")

    def copiar_resultado(self):
        self.result_area.selectAll()
        self.result_area.copy()
        self.result_area.moveCursor(QTextCursor.End)

    def show_tokens_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Tokens generados")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout()
        label = QLabel("Lista de tokens generados:")
        layout.addWidget(label)
        text = QTextEdit()
        text.setReadOnly(True)
        if self.tokens:
            lines = [f"{i+1:03d}: {t}" for i, t in enumerate(self.tokens)]
            text.setPlainText("\n".join(lines))
        else:
            text.setPlainText("No hay tokens generados.")
        layout.addWidget(text)
        btn = QPushButton("Cerrar")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def show_ast_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Árbol de Sintaxis Abstracta (AST)")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout()
        label = QLabel("AST generado:")
        layout.addWidget(label)
        text = QTextEdit()
        text.setReadOnly(True)
        if self.ast:
            # Si el AST tiene un método para mostrar como árbol ASCII, úsalo
            ascii_tree = None
            if hasattr(self.ast, 'to_ascii') and callable(getattr(self.ast, 'to_ascii')):
                ascii_tree = self.ast.to_ascii()
            elif hasattr(self.ast, 'to_ascii_tree') and callable(getattr(self.ast, 'to_ascii_tree')):
                ascii_tree = self.ast.to_ascii_tree()
            if ascii_tree:
                text.setPlainText(ascii_tree)
            else:
                text.setPlainText(str(self.ast))
        else:
            text.setPlainText("No se ha generado un AST.")
        layout.addWidget(text)
        btn = QPushButton("Cerrar")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def show_simulation_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QPushButton
        import re
        dlg = QDialog(self)
        dlg.setWindowTitle("Simulación/Ejecución del código")
        dlg.setMinimumSize(600, 400)
        layout = QVBoxLayout()
        label = QLabel("Salida de la simulación/ejecución:")
        layout.addWidget(label)
        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("QTextEdit { background: #23242b; color: #f8f8f2; border-radius: 8px; padding: 8px; border: 1px solid #444; }")
        def format_sim_output_html(sim_output):
            def format_line(line):
                # SQL: inserciones, actualizaciones, eliminaciones
                match = re.match(r"Simulación: (\d+) fila insertada en '([\w_]+)'. Valores: (\{.*\})", line)
                if match:
                    n, tabla, valores = match.groups()
                    return f"<span style='color:#00e676'><b>{n} fila insertada</b> en <b>{tabla}</b>:</span><br><span style='color:#ffd54f;word-break:break-all;margin-left:1em'>→ {valores}</span>"
                match = re.match(r"Simulación: (\d+) filas insertadas en '([\w_]+)'. Valores: (\[.*\])", line)
                if match:
                    n, tabla, valores = match.groups()
                    return f"<span style='color:#00e676'><b>{n} filas insertadas</b> en <b>{tabla}</b>:</span><br><span style='color:#ffd54f;word-break:break-all;margin-left:1em'>→ {valores}</span>"
                match = re.match(r"Simulación: (\d+) fila actualizada en '([\w_]+)'. Valores: (\{.*\})", line)
                if match:
                    n, tabla, valores = match.groups()
                    return f"<span style='color:#2979ff'><b>{n} fila actualizada</b> en <b>{tabla}</b>:</span><br><span style='color:#ffd54f;word-break:break-all;margin-left:1em'>→ {valores}</span>"
                match = re.match(r"Simulación: (\d+) fila eliminada de '([\w_]+)'", line)
                if match:
                    n, tabla = match.groups()
                    return f"<span style='color:#ff1744'><b>{n} fila eliminada</b> de <b>{tabla}</b></span>"
                match = re.match(r"Simulación: (\d+) filas eliminadas de '([\w_]+)'", line)
                if match:
                    n, tabla = match.groups()
                    return f"<span style='color:#ff1744'><b>{n} filas eliminadas</b> de <b>{tabla}</b></span>"
                # Prints y resultados generales
                if re.match(r"\s*print\s*[:=]?", line, re.IGNORECASE) or line.strip().startswith('Salida:'):
                    return f"<span style='color:#ffd54f'>{line}</span>"
                # Errores
                if re.search(r"error|exception|traceback|syntax|NameError|TypeError|ValueError", line, re.IGNORECASE):
                    return f"<span style='color:#ff1744'>{line}</span>"
                # Advertencias
                if re.search(r"warning|advertencia", line, re.IGNORECASE):
                    return f"<span style='color:#ffb300'>{line}</span>"
                # Resultados numéricos o de evaluación
                if re.match(r"Resultado: ", line):
                    return f"<span style='color:#2979ff'>{line}</span>"
                # Mensajes de éxito genéricos
                if re.match(r"Éxito|Success", line, re.IGNORECASE):
                    return f"<span style='color:#00e676'>{line}</span>"
                return f"<span style='color:#fff'>{line}</span>"
            lines = sim_output.splitlines()
            html_lines = [format_line(l) for l in lines]
            # Cambia la fuente aquí:
            return ("<pre style='background:#23242b;border-radius:6px;padding:8px;"
                    "color:#fff;white-space:pre-wrap;word-break:break-all;"
                    "font-family:Consolas, 'Fira Mono', 'JetBrains Mono', 'Menlo', 'Monaco', 'Liberation Mono', 'Courier New', monospace;"
                    "font-size:15px;"
                    "'>" + "<br>".join(html_lines) + "</pre>")
        if self.sim_output and self.sim_output.strip():
            text.setHtml(format_sim_output_html(self.sim_output))
        else:
            text.setHtml("<span style='color:#b0bec5'>No hay salida de simulación disponible.</span>")
        layout.addWidget(text)
        btn = QPushButton("Cerrar")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def analizar_codigo(self):
        codigo = self.editor.toPlainText()
        # Normaliza saltos de línea a LF para evitar errores por CR o CRLF
        codigo = codigo.replace('\r\n', '\n').replace('\r', '\n')
        if not codigo.strip():
            self.result_area.setPlainText("")
            self.lang_label.setText("")
            return
        # 1. Detectar lenguaje
        resultado_lenguaje = detectar_lenguaje(codigo)
        lenguaje = resultado_lenguaje[0]
        confianza = resultado_lenguaje[1]
        # Etiqueta de lenguaje detectado con color
        color_map = {"Python": "#ffd54f", "JavaScript": "#81c784", "C++": "#4fc3f7", "Pascal": "#ba68c8", "PL/SQL": "#ffb74d", "T-SQL": "#90caf9"}
        color = color_map.get(lenguaje, "#ffd54f")
        self.lang_label.setText(f"Lenguaje detectado: {lenguaje} ({confianza:.2f}%)")
        self.lang_label.setStyleSheet(f"QLabel {{ background: #393e4b; border-radius: 8px; padding: 4px 8px; color: {color}; border: 1px solid #555; }}")
        resultado = f"Lenguaje detectado: {lenguaje} (confianza: {confianza:.2f}%)\n"
        # 2. Análisis léxico
        try:
            if lenguaje == "Python":
                lexer = LexerPython(codigo)
                tokens = lexer.tokenizar()
                errores_lex = [t for t in tokens if t.tipo == 'ERROR_LEXICO']
            elif lenguaje == "HTML":
                from analizador_lexico.lexer_html import LexerHTML
                lexer = LexerHTML(codigo)
                tokens = lexer.tokenizar()
                errores_lex = [t for t in tokens if t.tipo == 'ERROR_HTML']
            elif lenguaje == "Pascal":
                lexer = LexerPascal(codigo)
                tokens = lexer.tokenizar()
                errores_lex = [t for t in tokens if t.tipo == 'ERROR_LEXICO']
            elif lenguaje == "PL/SQL":
                lexer = LexerPLSQL(codigo)
                tokens = lexer.tokenizar()
                errores_lex = [t for t in tokens if t.tipo == 'ERROR_LEXICO']
            elif lenguaje == "JavaScript":
                lexer = LexerJavaScript(codigo)
                tokens = lexer.tokenizar()
                errores_lex = [t for t in tokens if t.tipo == 'ERROR_LEXICO']
            elif lenguaje == "C++":
                lexer = LexerCPP(codigo)
                tokens = lexer.tokenizar()
                errores_lex = [t for t in tokens if t.tipo == 'ERROR_LEXICO']
            elif lenguaje == "T-SQL":
                lexer = LexerTSQL(codigo)
                tokens = lexer.tokenizar()
                errores_lex = [t for t in tokens if t.tipo == 'ERROR_LEXICO']
            else:
                self.result_area.setPlainText(resultado + "\nNo se reconoce el lenguaje o no está soportado.")
                return
            self.tokens = tokens  # Guardar tokens para el botón
        except Exception as e:
            # Acumular errores léxicos si ya existen
            if 'errores_lex' in locals() and isinstance(errores_lex, list):
                errores_lex.append(str(e))
            else:
                errores_lex = [str(e)]
            # Mostrar todos los errores léxicos en la interfaz
            resultado += "Errores léxicos encontrados:\n" + "\n".join(str(err) for err in errores_lex) + "\n"
            self.result_area.setPlainText(resultado)
            return
        resultado += f"\nTokens generados: {len(tokens)}\n"
        if errores_lex:
            resultado += "Errores léxicos encontrados:\n" + "\n".join(str(e) for e in errores_lex) + "\n"
        else:
            resultado += "Sin errores léxicos.\n"
        # 3. Análisis sintáctico
        try:
            if lenguaje == "Python":
                parser = ParserPython(tokens)
            elif lenguaje == "HTML":
                from analizador_sintactico.parser_html import ParserHTML
                parser = ParserHTML(tokens)
            elif lenguaje == "Pascal":
                parser = ParserPascal(tokens)
            elif lenguaje == "PL/SQL":
                parser = ParserPLSQL(tokens)
            elif lenguaje == "JavaScript":
                parser = ParserJavaScript(tokens)
            elif lenguaje == "C++":
                parser = ParserCPP(tokens)
            elif lenguaje == "T-SQL":
                parser = ParserTSQL(tokens)
            else:
                parser = None
            if parser:
                ast = parser.parse()
                errores_sint = getattr(parser, 'errores_sintacticos', [])
            else:
                ast = None
                errores_sint = ["No se pudo instanciar el parser para este lenguaje."]
            self.ast = ast  # Guardar AST para el botón
        except Exception as e:
            # Si ya hay errores_sint, los acumulamos, si no, creamos la lista
            if 'errores_sint' in locals() and isinstance(errores_sint, list):
                errores_sint.append(str(e))
            else:
                errores_sint = [str(e)]
            # Mostrar todos los errores sintácticos en la interfaz
            resultado += "Errores sintácticos encontrados:\n" + "\n".join(str(err) for err in errores_sint) + "\n"
            self.result_area.setPlainText(resultado)
            return
        if errores_sint:
            resultado += "Errores sintácticos encontrados:\n" + "\n".join(str(e) for e in errores_sint) + "\n"
        else:
            resultado += "Sin errores sintácticos.\n"
        # 4. Análisis semántico
        errores_sem = []
        semantico_resultado = ""
        # Permitir análisis semántico aunque haya errores sintácticos, si ast no es None
        try:
            if ast is not None:
                if lenguaje == "Python":
                    from analizador_semantico.semantico_python import AnalizadorSemanticoPython
                    sem = AnalizadorSemanticoPython()
                    sem.analizar(ast)
                    errores_sem = getattr(sem, 'errores', [])
                elif lenguaje == "Pascal":
                    from analizador_semantico.semantico_pascal import AnalizadorSemanticoPascal
                    sem = AnalizadorSemanticoPascal()
                    sem.analizar(ast)
                    errores_sem = getattr(sem, 'errores', [])
                elif lenguaje == "JavaScript":
                    from analizador_semantico.semantico_javascript import AnalizadorSemanticoJS
                    sem = AnalizadorSemanticoJS()
                    sem.analizar(ast)
                    errores_sem = getattr(sem, 'errores', [])
                elif lenguaje == "C++":
                    from analizador_semantico.semantico_cpp import AnalizadorSemanticoCPP
                    sem = AnalizadorSemanticoCPP()
                    sem.analizar(ast)
                    errores_sem = getattr(sem, 'errores', [])
                elif lenguaje == "PL/SQL":
                    from analizador_semantico.semantico_plsql import AnalizadorSemanticoPLSQL
                    sem = AnalizadorSemanticoPLSQL()
                    sem.analizar(ast)
                    errores_sem = getattr(sem, 'errores', [])
                elif lenguaje == "T-SQL":
                    from analizador_semantico.semantico_tsql import AnalizadorSemanticoTSQL
                    sem = AnalizadorSemanticoTSQL()
                    sem.analizar(ast)
                    errores_sem = getattr(sem, 'errores', [])
                elif lenguaje == "HTML":
                    from analizador_semantico.semantico_html import AnalizadorSemanticoHTML
                    sem = AnalizadorSemanticoHTML()
                    sem.analizar(ast)
                    errores_sem = getattr(sem, 'errores', [])
                else:
                    errores_sem = ["No se reconoce el lenguaje para análisis semántico."]
        except Exception as e:
            if 'errores_sem' in locals() and isinstance(errores_sem, list):
                errores_sem.append(f"Error en análisis semántico: {e}")
            else:
                errores_sem = [f"Error en análisis semántico: {e}"]
        if errores_sem:
            semantico_resultado = "Errores semánticos encontrados:\n" + "\n".join(str(e) for e in errores_sem) + "\n"
        else:
            semantico_resultado = "Sin errores semánticos.\n"
        resultado += semantico_resultado
        # 5. Ejecución si no hay errores
        mensaje_creacion_tabla = ""
        salida_ejecucion = ""
        if not errores_lex and not errores_sint and ast:
            # Detectar CREATE TABLE en SQL
            if lenguaje in ["PL/SQL", "T-SQL"]:
                import re
                match = re.search(r"CREATE\s+TABLE\s+([a-zA-Z_][a-zA-Z0-9_]*)", codigo, re.IGNORECASE)
                if match:
                    nombre_tabla = match.group(1)
                    mensaje_creacion_tabla = f"\nSe creó la tabla llamada {nombre_tabla}.\n"
            # Ejecutar con el intérprete propio según el lenguaje
            try:
                import io
                import contextlib
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    if lenguaje == "JavaScript":
                        from simulador_ejecucion.interprete_javascript import InterpreteJavaScript
                        interprete = InterpreteJavaScript()
                        interprete.interpretar_script(ast)
                    elif lenguaje == "C++":
                        from simulador_ejecucion.interprete_cpp import InterpreteCPP
                        interprete = InterpreteCPP()
                        interprete.interpretar_unidad_traduccion(ast)
                    elif lenguaje == "Pascal":
                        from simulador_ejecucion.interprete_pascal import InterpretePascal
                        tabla = getattr(parser, 'tabla_simbolos', None)
                        interprete = InterpretePascal(tabla)
                        interprete.interpretar(ast)
                    elif lenguaje == "PL/SQL":
                        from simulador_ejecucion.interprete_plsql import InterpretePLSQL
                        interprete = InterpretePLSQL()
                        interprete.interpretar_script(ast)
                    elif lenguaje == "T-SQL":
                        from simulador_ejecucion.interprete_tsql import InterpreteTSQL
                        interprete = InterpreteTSQL()
                        interprete.interpretar_script(ast)
                    elif lenguaje == "HTML":
                        from simulador_ejecucion.interprete_html import VisualizadorHTML
                        interprete = VisualizadorHTML()
                        salida_ejecucion = interprete.visualizar_documento(ast)
                    elif lenguaje == "Python":
                        from simulador_ejecucion.interprete_python import InterpretePython
                        interprete = InterpretePython()
                        interprete.interpretar_modulo(ast)
                    else:
                        print("(Aquí iría la ejecución real del código si el intérprete está implementado)")
                salida_ejecucion = buffer.getvalue()
            except Exception as e:
                salida_ejecucion = f"[Error en ejecución del intérprete]: {e}\n"
        self.sim_output = salida_ejecucion  # Guardar salida para el botón
        # --- Personalización especial para HTML ---
        if lenguaje == "HTML":
            # Bloque visual especial para HTML
            resultado_html = f"""
            <div style='font-size:15px;background:#23242b;color:#f8f8f2;border-radius:8px;padding:16px 16px 10px 16px;'>
            <div style='font-size:17px;font-weight:bold;color:#4fc3f7;margin-bottom:8px;'>Análisis de HTML</div>
            <hr style='border:1px solid #4fc3f7;'>
            <b style='color:#00bcd4'>Análisis léxico:</b><br>
            <span style='color:{'#ff1744' if errores_lex else '#00e676'};font-weight:bold'>{' ' if errores_lex else 'Sin errores léxicos.'}</span><br>
            """
            if errores_lex:
                resultado_html += "<span style='color:#ff1744'>Errores léxicos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_lex) + "</ol>"
            # Tokens destacados
            def colorear_token_html(token):
                if token.tipo == 'ETIQUETA_APERTURA':
                    return f"<span style='color:#4fc3f7;font-weight:bold'>&lt;{token.valor}&gt;</span>"
                if token.tipo == 'ETIQUETA_CIERRE':
                    return f"<span style='color:#ffb300;font-weight:bold'>&lt;/{token.valor}&gt;</span>"
                if token.tipo == 'ATRIBUTO':
                    return f"<span style='color:#ffd54f'>{token.valor}</span>"
                if token.tipo == 'VALOR':
                    return f"<span style='color:#81c784'>'{token.valor}'</span>"
                if token.tipo == 'TEXTO':
                    return f"<span style='color:#fff'>{token.valor}</span>"
                if token.tipo == 'ERROR_HTML':
                    return f"<span style='color:#ff1744;background:#fff2;border-radius:4px;padding:1px 4px;'>{token.valor}</span>"
                return f"<span style='color:#b0bec5'>{token.valor}</span>"
            tokens_html = " ".join(colorear_token_html(t) for t in tokens)
            resultado_html += f"<span style='color:#b0bec5'>Tokens generados: {len(tokens)}</span><br>"
            resultado_html += f"<div style='background:#e3e6ed;border-radius:8px;padding:8px;margin:8px 0 12px 0;word-break:break-all;color:#23262e;'>{tokens_html}</div>"
            resultado_html += "<hr style='border:1px solid #7c4dff;'><b style='color:#7c4dff'>Análisis sintáctico:</b><br>"
            resultado_html += f"<span style='color:{'#ff1744' if errores_sint else '#00e676'};font-weight:bold'>{' ' if errores_sint else 'Sin errores sintácticos.'}</span><br>"
            if errores_sint:
                resultado_html += "<span style='color:#ff1744'>Errores sintácticos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_sint) + "</ol>"
            resultado_html += "<hr style='border:1px solid #ffb300;'><b style='color:#ffb300'>Análisis semántico:</b><br>"
            if errores_sem:
                resultado_html += "<span style='color:#ff1744'>Errores semánticos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_sem) + "</ol>"
            else:
                resultado_html += "<span style='color:#00e676'>Sin errores semánticos.</span><br>"
            if not errores_lex and not errores_sint and ast:
                resultado_html += "<hr style='border:1px solid #00bfae;'><b style='color:#00bfae'>Visualización HTML:</b><br>"
                if salida_ejecucion:
                    # Vista previa renderizada (fondo claro para mejor legibilidad)
                    resultado_html += "<div style='margin:12px 0 8px 0;padding:8px;background:#fff;border-radius:8px;box-shadow:0 2px 8px #0003;border:1.5px solid #ffd54f;'>"
                    resultado_html += "<b style='color:#ffd54f;'>Vista previa:</b><br>"
                    resultado_html += f"<div style='background:#fff;border-radius:6px;padding:10px;margin:8px 0;box-shadow:0 2px 8px #ffd54f44; color:#23262e; min-height:30px;max-height:200px;overflow:auto;'>{salida_ejecucion}</div>"
                    resultado_html += "</div>"
                    # Mostrar el HTML fuente generado
                    resultado_html += "<b style='color:#b0bec5;'>HTML generado:</b><br>"
                    resultado_html += f"<pre style='background:#23242b;border-radius:6px;padding:8px;color:#ffd54f;white-space:pre-wrap;word-break:break-all;max-height:120px;overflow:auto;'>{self.editor.toPlainText()}</pre>"
                else:
                    resultado_html += "<span style='color:#b0bec5'>(No se generó salida HTML)</span><br>"
            resultado_html += "</div>"
            self.result_area.setHtml(resultado_html)
            self.result_area.moveCursor(QTextCursor.End)
            return
        # --- Fin personalización HTML ---
        # Construcción amigable del resultado con formato HTML
        if lenguaje == "HTML":
            # --- PRESENTACIÓN PERSONALIZADA PARA HTML ---
            resultado_html = f"""
            <div style='font-size:15px; background: linear-gradient(90deg,#23262e 60%,#ffb34722 100%); border-radius: 10px; padding: 12px;'>
            <div style='background: linear-gradient(90deg,#ffb347 0,#ffcc33 100%); color:#23262e; border-radius:7px; padding:6px 12px; font-weight:bold; margin-bottom:10px; border:1.5px solid #ffd54f;'>
                <span style='font-size:16px;'>Análisis HTML</span>
            </div>
            <hr style='border:1px solid #ffb347;'>
            <b style='color:#00bcd4'>Análisis léxico:</b><br>
            <span style='color:{'#ff1744' if errores_lex else '#00e676'};font-weight:bold'>{' ' if errores_lex else 'Sin errores léxicos.'}</span><br>
            """
            if errores_lex:
                resultado_html += "<span style='color:#ff1744'>Errores léxicos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_lex) + "</ol>"
            # Mostrar tokens HTML resaltados
            resultado_html += f"<span style='color:#b0bec5'>Tokens generados: {len(tokens)}</span><br>"
            if tokens:
                resultado_html += "<div style='margin:6px 0 10px 0; padding:6px; background:#23242b; border-radius:6px; border:1px solid #444; max-height:120px; overflow:auto; font-size:13px;'>"
                for t in tokens:
                    if t.tipo == 'TEXTO':
                        resultado_html += f"<span style='color:#ffd54f;'>&lt;TEXTO&gt; '{t.valor}'</span>  "
                    elif t.tipo == 'ETIQUETA_APERTURA':
                        resultado_html += f"<span style='color:#81c784;'>&lt;{t.valor}&gt;</span>  "
                    elif t.tipo == 'ETIQUETA_CIERRE':
                        resultado_html += f"<span style='color:#e57373;'>&lt;/{t.valor}&gt;</span>  "
                    elif t.tipo == 'ATRIBUTO':
                        resultado_html += f"<span style='color:#4fc3f7;'>{t.valor}</span>  "
                    elif t.tipo == 'VALOR_ATRIBUTO':
                        resultado_html += f"<span style='color:#ffd54f;'>'{t.valor}'</span>  "
                    elif t.tipo == 'COMENTARIO':
                        resultado_html += f"<span style='color:#bdbdbd;'>&lt;!--{t.valor}--&gt;</span>  "
                    elif t.tipo == 'ERROR_HTML':
                        resultado_html += f"<span style='color:#ff5252;background:#2d1e1e;padding:2px 6px;border-radius:4px;'>&lt;Error&gt; {t.valor}</span>  "
                    else:
                        resultado_html += f"<span style='color:#b0bec5;'>{t.tipo}: '{t.valor}'</span>  "
                resultado_html += "</div>"
            resultado_html += "<hr style='border:1px solid #7c4dff;'><b style='color:#7c4dff'>Análisis sintáctico:</b><br>"
            resultado_html += f"<span style='color:{'#ff1744' if errores_sint else '#00e676'};font-weight:bold'>{' ' if errores_sint else 'Sin errores sintácticos.'}</span><br>"
            if errores_sint:
                resultado_html += "<span style='color:#ff1744'>Errores sintácticos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_sint) + "</ol>"
            resultado_html += "<hr style='border:1px solid #ffb300;'><b style='color:#ffb300'>Análisis semántico:</b><br>"
            resultado_html += "<span style='color:#b0bec5'>(Análisis semántico no implementado en este ejemplo)</span><br>"
            if not errores_lex and not errores_sint and ast:
                resultado_html += "<hr style='border:1px solid #00bfae;'><b style='color:#00bfae'>Simulación/Visualización HTML:</b><br>"
                if salida_ejecucion.strip():
                    # Vista previa renderizada
                    resultado_html += "<div style='margin:10px 0 16px 0; padding:10px; background:linear-gradient(90deg,#23262e 60%,#ffd54f22 100%); border-radius:8px; border:1.5px solid #ffd54f;'>"
                    resultado_html += "<b style='color:#ffd54f;'>Vista previa:</b><br>"
                    resultado_html += f"<div style='background:#fff;border-radius:6px;padding:10px;margin:8px 0;box-shadow:0 2px 8px #ffd54f44; color:#23262e; min-height:30px;max-height:200px;overflow:auto;'>{salida_ejecucion}</div>"
                    resultado_html += "</div>"
                    # Mostrar el HTML fuente generado
                    resultado_html += "<b style='color:#b0bec5;'>HTML generado:</b><br>"
                    resultado_html += f"<pre style='background:#23242b;border-radius:6px;padding:8px;color:#ffd54f;white-space:pre-wrap;word-break:break-all;max-height:120px;overflow:auto;'>{self.editor.toPlainText()}</pre>"
                else:
                    resultado_html += "<span style='color:#b0bec5'>(No se generó salida HTML)</span><br>"
            resultado_html += "</div>"
            self.result_area.setHtml(resultado_html)
            self.result_area.moveCursor(QTextCursor.End)
            return
        resultado_html = f"""
        <div style='font-size:15px;background:#23242b;color:#f8f8f2;border-radius:8px;padding:16px 16px 10px 16px;'>
        <hr><b style='color:#00bcd4'>Análisis léxico:</b><br>
        <span style='color:{'#ff1744' if errores_lex else '#00e676'};font-weight:bold'>{' ' if errores_lex else 'Sin errores léxicos.'}</span><br>
        """
        if errores_lex:
            resultado_html += "<span style='color:#ff1744'>Errores léxicos encontrados:</span>"
            resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_lex) + "</ol>"
        resultado_html += f"<span style='color:#b0bec5'>Tokens generados: {len(tokens)}</span><br>"
        resultado_html += "<hr><b style='color:#7c4dff'>Análisis sintáctico:</b><br>"
        resultado_html += f"<span style='color:{'#ff1744' if errores_sint else '#00e676'};font-weight:bold'>{' ' if errores_sint else 'Sin errores sintácticos.'}</span><br>"
        if errores_sint:
            resultado_html += "<span style='color:#ff1744'>Errores sintácticos encontrados:</span>"
            resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_sint) + "</ol>"
        resultado_html += "<hr><b style='color:#ffb300'>Análisis semántico:</b><br>"
        if errores_sem:
            resultado_html += "<span style='color:#ff1744'>Errores semánticos encontrados:</span>"
            resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_sem) + "</ol>"
        else:
            resultado_html += "<span style='color:#00e676'>Sin errores semánticos.</span><br>"
        resultado_html += "</div>"
        self.result_area.setHtml(resultado_html)
        self.result_area.moveCursor(QTextCursor.End)
        return
        # Colorear errores
        # --- NUEVO: Mostrar errores con formato HTML amigable para todos los lenguajes ---
        if errores_lex or errores_sint or errores_sem:
            resultado_html = f"""
            <div style='font-size:15px;background:#23242b;color:#f8f8f2;border-radius:8px;padding:16px 16px 10px 16px;'>
            <hr><b style='color:#00bcd4'>Análisis léxico:</b><br>
            <span style='color:{'#ff1744' if errores_lex else '#00e676'};font-weight:bold'>{' ' if errores_lex else 'Sin errores léxicos.'}</span><br>
            """
            if errores_lex:
                resultado_html += "<span style='color:#ff1744'>Errores léxicos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_lex) + "</ol>"
            resultado_html += f"<span style='color:#b0bec5'>Tokens generados: {len(tokens)}</span><br>"
            resultado_html += "<hr><b style='color:#7c4dff'>Análisis sintáctico:</b><br>"
            resultado_html += f"<span style='color:{'#ff1744' if errores_sint else '#00e676'};font-weight:bold'>{' ' if errores_sint else 'Sin errores sintácticos.'}</span><br>"
            if errores_sint:
                resultado_html += "<span style='color:#ff1744'>Errores sintácticos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_sint) + "</ol>"
            resultado_html += "<hr><b style='color:#ffb300'>Análisis semántico:</b><br>"
            if errores_sem:
                resultado_html += "<span style='color:#ff1744'>Errores semánticos encontrados:</span>"
                resultado_html += "<ol style='color:#ff5252'>" + "".join(f"<li>{str(e)}</li>" for e in errores_sem) + "</ol>"
            else:
                resultado_html += "<span style='color:#00e676'>Sin errores semánticos.</span><br>"
            resultado_html += "</div>"
            # Mostrar simulación/ejecución si no hay errores léxicos ni sintácticos y hay AST
            if not errores_lex and not errores_sint and ast:
                resultado_html += "<div style='margin-top:18px;'><hr><b style='color:#00bfae'>Ejecución/Simulación del código:</b><br>"
                if salida_ejecucion:
                    import re
                    def formatear_salida_ejecucion(linea):
                        # SQL: inserciones, actualizaciones, eliminaciones
                        match = re.match(r"Simulación: (\d+) fila insertada en '([\w_]+)'. Valores: (\{.*\})", linea)
                        if match:
                            n, tabla, valores = match.groups()
                            return f"<span style='color:#00e676'><b>{n} fila insertada</b> en <b>{tabla}</b>:</span><br><span style='color:#ffd54f;word-break:break-all;margin-left:1em'>→ {valores}</span>"
                        match = re.match(r"Simulación: (\d+) filas insertadas en '([\w_]+)'. Valores: (\[.*\])", linea)
                        if match:
                            n, tabla, valores = match.groups()
                            return f"<span style='color:#00e676'><b>{n} filas insertadas</b> en <b>{tabla}</b>:</span><br><span style='color:#ffd54f;word-break:break-all;margin-left:1em'>→ {valores}</span>"
                        match = re.match(r"Simulación: (\d+) fila actualizada en '([\w_]+)'. Valores: (\{.*\})", linea)
                        if match:
                            n, tabla, valores = match.groups()
                            return f"<span style='color:#2979ff'><b>{n} fila actualizada</b> en <b>{tabla}</b>:</span><br><span style='color:#ffd54f;word-break:break-all;margin-left:1em'>→ {valores}</span>"
                        match = re.match(r"Simulación: (\d+) fila eliminada de '([\w_]+)'", linea)
                        if match:
                            n, tabla = match.groups()
                            return f"<span style='color:#ff1744'><b>{n} fila eliminada</b> de <b>{tabla}</b></span>"
                        match = re.match(r"Simulación: (\d+) filas eliminadas de '([\w_]+)'", linea)
                        if match:
                            n, tabla = match.groups()
                            return f"<span style='color:#ff1744'><b>{n} filas eliminadas</b> de <b>{tabla}</b></span>"
                        # Prints y resultados generales
                        if re.match(r"\s*print\s*[:=]?", linea, re.IGNORECASE) or linea.strip().startswith('Salida:'):
                            return f"<span style='color:#ffd54f'>{linea}</span>"
                        # Errores
                        if re.search(r"error|exception|traceback|syntax|NameError|TypeError|ValueError", linea, re.IGNORECASE):
                            return f"<span style='color:#ff1744'>{linea}</span>"
                        # Advertencias
                        if re.search(r"warning|advertencia", linea, re.IGNORECASE):
                            return f"<span style='color:#ffb300'>{linea}</span>"
                        # Resultados numéricos o de evaluación
                        if re.match(r"Resultado: ", linea):
                            return f"<span style='color:#2979ff'>{linea}</span>"
                        # Mensajes de éxito genéricos
                        if re.match(r"Éxito|Success", linea, re.IGNORECASE):
                            return f"<span style='color:#00e676'>{linea}</span>"
                        # Encabezados de tablas (SELECT)
                        if re.match(r"\s*-+\s*", linea):
                            return f"<span style='color:#888'>{linea}</span>"
                        if re.match(r"\s*--- Resultado del SELECT ---", linea):
                            return f"<span style='color:#00bfae;font-weight:bold'>{linea}</span>"
                        if re.match(r"\s*\(0 filas afectadas\)", linea):
                            return f"<span style='color:#bdbdbd'>{linea}</span>"
                        # General
                        return f"<span style='color:#fff'>{linea}</span>"
                    salida_html = "<br>".join(formatear_salida_ejecucion(l) for l in salida_ejecucion.splitlines())
                    resultado_html += f"<pre style='background:#23242b;border-radius:6px;padding:8px;color:#fff;white-space:pre-wrap;word-break:break-all'>{salida_html}</pre>"
                else:
                    resultado_html += "<span style='color:#b0bec5'>(Aquí iría la ejecución real del código si el intérprete está implementado)</span><br>"
                resultado_html += "</div>"
            self.result_area.setHtml(resultado_html)
            self.result_area.moveCursor(QTextCursor.End)
            return

    def cargar_archivo(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import os
        opciones = QFileDialog.Options()
        opciones |= QFileDialog.ReadOnly
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de texto", "", "Archivos de texto (*.txt *.sql *.py *.js *.cpp *.pas *.html);;Todos los archivos (*)", options=opciones)
        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                self.editor.setPlainText(contenido)
            except Exception as e:
                QMessageBox.critical(self, "Error al cargar archivo", f"No se pudo leer el archivo:\n{os.path.basename(archivo)}\n\nError: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
