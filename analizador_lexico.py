# analizador_lexico.py
import re

class AnalizadorLexico:
    def __init__(self, tabla_simbolos=None):
        self.tabla_simbolos = tabla_simbolos
        self.tokens_validos = []
        self.errores_lexicos = []
        self.ambito = "Global"

        # Map de palabras reservadas -> token tipo (aprovechamos la versión del compañero)
        self.reservadas = {
            "entero": "TIPO_ENTERO",
            "flotante": "TIPO_FLOTANTE",
            "booleano": "TIPO_BOOLEANO",
            "caracter": "TIPO_CARACTER",
            "cadena": "TIPO_CADENA",
            "arreglo": "ARREGLO",
            "clase": "CLASE",
            "interfaz": "INTERFAZ",
            "enumeracion": "ENUMERACION",
            "si": "SI",
            "sino": "SINO",
            "segun": "SEGUN",
            "defecto": "DEFECTO",
            "caso": "CASO",
            "mientras": "MIENTRAS",
            "para": "PARA",
            "hacer": "HACER",
            "romper": "ROMPER",
            "continuar": "CONTINUAR",
            "retornar": "RETORNAR",
            "intentar": "INTENTAR",
            "capturar": "CAPTURAR",
            "importar": "IMPORTAR",
            "exportar": "EXPORTAR",
            "hereda": "HEREDA",
            "nuevo": "NUEVO",
            "usar": "USAR",
            "constante": "CONSTANTE",
            "imprimir": "IMPRIMIR",
            "verdadero": "BOOLEANO_LIT",
            "falso": "BOOLEANO_LIT",
            "vacio" : "TIPO_VACIO"
        }

        # Patrón principal: loada operadores compuestos primero
        # Usamos (?P<NAME>...) para saber qué match fue
                # Patrón principal: operadores compuestos primero, y soporte para char entre comillas simples
        # Usamos (?P<NAME>...) para saber qué match fue
        self.token_regex = re.compile(r'''
            (?P<COMMENT_LINE>//[^\n]*) |
            (?P<COMMENT_BLOCK>/\*[\s\S]*?\*/) |
            (?P<OP_COMP>==|!=|<=|>=|&&|\|\||\+=|-=|\*=|/=|%=|\+\+|--) |
            (?P<NUMBER_FLOAT>\d+\.\d+) |
            (?P<NUMBER_INT>\d+) |
            (?P<STRING>"(?:[^"\\]|\\.)*") |
            (?P<CHAR>'(?:[^'\\]|\\.)') |
            (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*) |
            (?P<BAD_IDENT>\d+[A-Za-z_][A-Za-z0-9_]*) |
            (?P<OP>[+\-*/%!=<>]) |
            (?P<SYM>[(){}\[\],;:.]) |
            (?P<WHITESPACE>\s+)
        ''', re.VERBOSE)


        # Map de operadores/símbolos a tokens (estilo compañero)
        self.mapping_ops = {
            "+": "MAS", "-": "MENOS", "*": "MULT", "/": "DIV", "%": "MOD",
            "++": "INCREMENTO", "--": "DECREMENTO",
            "=": "ASIGNACION", "==": "IGUAL", "!=": "DISTINTO",
            "+=": "ASIGNACION", "-=": "ASIGNACION", "*=": "ASIGNACION", "/=": "ASIGNACION", "%=": "ASIGNACION",
            "<": "MENOR", ">": "MAYOR", "<=": "MENOR_IGUAL", ">=": "MAYOR_IGUAL",
            "&&": "AND", "||": "OR", "!": "NOT",
            "(": "PAREN_IZQ", ")": "PAREN_DER",
            "{": "LLAVE_IZQ", "}": "LLAVE_DER",
            "[": "CORCH_IZQ", "]": "CORCH_DER",
            ";": "PUNTO_Y_COMA", ",": "COMA", ".": "PUNTO", ":": "DOS_PUNTOS"
        }

    def tokenize(self, texto):
        """Devuelve (tokens, errores). Cada token: {'token':lexema,'tipo':tipo,'linea':L,'col':C}"""
        self.tokens_validos = []
        self.errores_lexicos = []

        lines = texto.splitlines(keepends=True)
        # iteramos por líneas para poder calcular columna exacta
        for lineno, line in enumerate(lines, start=1):
            pos = 0
            while pos < len(line):
                m = self.token_regex.match(line, pos)
                if not m:
                    # Caracter inesperado -> error léxico en esa columna
                    bad_char = line[pos]
                    self.errores_lexicos.append({
                        "token": bad_char,
                        "tipo": "ERROR_CARACTER",
                        "linea": lineno,
                        "columna": pos + 1,
                        "mensaje": f"Caracter no reconocido: '{bad_char}'"
                    })
                    pos += 1
                    continue

                kind = m.lastgroup
                lexeme = m.group(kind)
                start_col = m.start() + 1  # columna 1-index
                pos = m.end()

                # Ignorar whitespace y comentarios (pero registrar posición en caso de error)
                if kind == "WHITESPACE" or kind == "COMMENT_LINE" or kind == "COMMENT_BLOCK":
                    continue

                # Identificadores / reservadas
                if kind == "IDENT":
                    low = lexeme  # usar literal; tu gramática ya está en español
                    if low in self.reservadas:
                        tipo = self.reservadas[low]
                    else:
                        tipo = "IDENTIFICADOR"
                        # Insertar en tabla de símbolos (si aplica)
                        if self.tabla_simbolos:
                            simbolo = {
                                "identificador": lexeme,
                                "categoria": tipo,
                                "tipo_dato": None,
                                "ambito": self.ambito,
                                "direccion": None,
                                "linea": lineno,
                                "valor": None,
                                "estado": "declarado",
                                "estructura": None,
                                "contador_referencias": 0
                            }
                            # Asegúrate que tu tabla_simbolos tenga método insertar_simbolo
                            try:
                                self.tabla_simbolos.insertar_simbolo(simbolo)
                            except Exception:
                                # no interrumpir por errores en tabla
                                pass

                    self.tokens_validos.append({
                        "token": lexeme,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue

                # Identificador mal formado (ej: 123abc)
                if kind == "BAD_IDENT":
                    self.errores_lexicos.append({
                        "token": lexeme,
                        "tipo": "ERROR_IDENTIFICADOR_INVALIDO",
                        "linea": lineno,
                        "columna": start_col,
                        "mensaje": "Identificador inválido (comienza con dígito)"
                    })
                    continue

                # Numeros
                if kind == "NUMBER_FLOAT":
                    tipo = "FLOTANTE_LIT"
                    self.tokens_validos.append({
                        "token": lexeme,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue
                if kind == "NUMBER_INT":
                    tipo = "ENTERO_LIT"
                    self.tokens_validos.append({
                        "token": lexeme,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue

                # Strings
                if kind == "STRING":
                    tipo = "CADENA_LIT"
                    self.tokens_validos.append({
                        "token": lexeme,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue
                
                 # Caracter literal (ej: 'J')
                if kind == "CHAR":
                    # guardar sin las comillas si quieres: lexeme[1] o limpio
                    ch = lexeme[1:-1]  # sin comillas
                    tipo = "CARACTER_LIT"
                    self.tokens_validos.append({
                        "token": ch,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue
                
                # Operadores compuestos y simples
                if kind == "OP_COMP" or kind == "OP":
                    # mapear con mapping_ops (si está), sino dejar tal cual
                    tipo = self.mapping_ops.get(lexeme, "OP")
                    self.tokens_validos.append({
                        "token": lexeme,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue

                # Símbolos
                if kind == "SYM":
                    tipo = self.mapping_ops.get(lexeme, lexeme)
                    self.tokens_validos.append({
                        "token": lexeme,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue

                # Cualquier otro caso no esperado:
                self.errores_lexicos.append({
                    "token": lexeme,
                    "tipo": "ERROR_DESCONOCIDO",
                    "linea": lineno,
                    "columna": start_col,
                    "mensaje": "Token no identificado correctamente"
                })

        return self.tokens_validos, self.errores_lexicos
