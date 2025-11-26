import re

class AnalizadorLexico:
    def __init__(self, tabla_simbolos=None):
        self.tabla_simbolos = tabla_simbolos
        self.tokens_validos = []
        self.errores_lexicos = []
        self.ambito = "Global"

        # Palabras reservadas
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
            "verdadero": "BOOLEANO_LIT",
            "vacio": "TIPO_VACIO"
        }

        # Expresiones regulares
        self.token_regex = re.compile(r'''
            (?P<COMMENT_LINE>//[^\n]*) |
            (?P<COMMENT_BLOCK>/\*[\s\S]*?\*/) |
            (?P<OP_COMP>==|!=|<=|>=|&&|\|\||\+=|-=|\*=|/=|%=|\+\+|--) |
            (?P<NUMBER_FLOAT>\d+\.\d+) |
            (?P<NUMBER_INT>\d+) |
            (?P<STRING>"(?:[^"\\]|\\.)*") |
            (?P<CHAR>'(?:[^'\\]|\\.)') |
            (?P<BAD_CHAR>'[^']{2,}') |
            (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*) |
            (?P<BAD_IDENT>\d+[A-Za-z_][A-Za-z0-9_]*) |
            (?P<OP>[+\-*/%!=<>]) |
            (?P<SYM>[(){}\[\],;:.]) |
            (?P<WHITESPACE>\s+)
        ''', re.VERBOSE)

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

    def resetear(self):
        """Reinicia el estado del analizador léxico"""
        self.tokens_validos = []
        self.errores_lexicos = []
        self.ambito = "Global"

    def tokenize(self, texto):
        self.tokens_validos = []
        self.errores_lexicos = []
        lines = texto.splitlines(keepends=True)

        for lineno, line in enumerate(lines, start=1):
            pos = 0
            while pos < len(line):
                m = self.token_regex.match(line, pos)
                if not m:
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
                start_col = m.start() + 1
                pos = m.end()

                if kind in ("WHITESPACE", "COMMENT_LINE", "COMMENT_BLOCK"):
                    continue

                # --- Identificadores o palabras reservadas ---
                if kind == "IDENT":
                    # 1️Si es palabra reservada
                    if lexeme in self.reservadas:
                        tipo = self.reservadas[lexeme]

                    # 2️ Si se parece a una palabra reservada mal escrita
                    elif any(lexeme.lower() != r and lexeme.lower().startswith(r) for r in self.reservadas):
                        self.errores_lexicos.append({
                            "token": lexeme,
                            "tipo": "ERROR_PALABRA_RESERVADA_INVALIDA",
                            "linea": lineno,
                            "columna": start_col,
                            "mensaje": f"Posible palabra reservada mal escrita: '{lexeme}'"
                        })
                        continue

                    # 3 Si es identificador válido
                    else:
                        tipo = "IDENTIFICADOR"
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
                            try:
                                self.tabla_simbolos.insertar_simbolo(simbolo)
                            except Exception:
                                pass

                    self.tokens_validos.append({
                        "token": lexeme,
                        "tipo": tipo,
                        "linea": lineno,
                        "columna": start_col
                    })
                    continue

                if kind == "BAD_IDENT":
                    self.errores_lexicos.append({
                        "token": lexeme,
                        "tipo": "ERROR_IDENTIFICADOR_INVALIDO",
                        "linea": lineno,
                        "columna": start_col,
                        "mensaje": "Identificador inválido: comienza con número"
                    })
                    continue

                if kind == "NUMBER_FLOAT":
                    tipo = "FLOTANTE_LIT"
                elif kind == "NUMBER_INT":
                    tipo = "ENTERO_LIT"
                elif kind == "STRING":
                    tipo = "CADENA_LIT"
                elif kind == "CHAR":
                    tipo = "CARACTER_LIT"
                    # Extrae el valor entre comillas simples
                    valor = lexeme[1:-1]  # Remueve las comillas simples
                    # Si es un escape, procesarlo
                    if len(valor) == 1:
                        lexeme = valor
                elif kind == "BAD_CHAR":
                    self.errores_lexicos.append({
                        "token": lexeme,
                        "tipo": "ERROR_CARACTER_INVALIDO",
                        "linea": lineno,
                        "columna": start_col,
                        "mensaje": "Literal de caracter inválido (debe contener solo un carácter entre comillas simples)"
                    })
                    continue
                elif kind in ("OP_COMP", "OP"):
                    tipo = self.mapping_ops.get(lexeme, "OP")
                elif kind == "SYM":
                    tipo = self.mapping_ops.get(lexeme, lexeme)
                else:
                    self.errores_lexicos.append({
                        "token": lexeme,
                        "tipo": "ERROR_DESCONOCIDO",
                        "linea": lineno,
                        "columna": start_col,
                        "mensaje": "Token no identificado correctamente"
                    })
                    continue

                self.tokens_validos.append({
                    "token": lexeme,
                    "tipo": tipo,
                    "linea": lineno,
                    "columna": start_col
                })

        return self.tokens_validos, self.errores_lexicos
