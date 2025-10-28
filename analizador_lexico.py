import re

class AnalizadorLexico:
    def __init__(self, tabla_simbolos = None):
        self.tokens_validos = []
        self.errores_lexicos = []
        self.tabla_simbolos = tabla_simbolos  # tabla de símbolos externa
        self.ambito ="Global"
        
        # Patrones
        self.patron_identificador = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
        self.patron_entero = re.compile(r"^[0-9]+$")
        self.patron_flotante = re.compile(r"^[0-9]+\.[0-9]+$")
        self.patron_cadena = re.compile(r'^".*"$')
        self.patron_aritmetico = re.compile(r'^(\+|-|\*|/|%|\+\+|--)$')
        self.patron_relacional = re.compile(r'^(==|!=|<=|>=|<|>)$')
        self.patron_logico = re.compile(r'^(&&|\|\||!)$')

        self.palabras_reservadas = [
            "entero", "flotante", "booleano", "caracter", "cadena", "arreglo",
            "clase", "interfaz", "enumeracion", "si", "sino", "segun", "defecto",
            "caso", "mientras", "para", "hacer", "romper", "continuar", "retornar", "vacio",
            "intentar", "capturar", "importar", "exportar", "hereda", "nuevo", "usar",
            "constante", "imprimir"
        ]

        # Patrón para analizar texto
        self.token_pattern = re.compile(r'''
            "(?:[^"\\]|\\.)*"         | # cadenas entre comillas
            /\*.*?\*/                 | # comentarios de bloque
            //[^\n]*                  | # comentarios de una línea
            \d+\.\d+                  | # números flotantes
            \d+                       | # números enteros
            [a-zA-Z_][a-zA-Z0-9_]*    | # identificadores
            \d+[a-zA-Z_][a-zA-Z0-9_]* | # identificadores mal formados
            [=+\-*/<>]                | # operadores
            [(){},;]                   # símbolos especiales   
        ''', re.VERBOSE)

    # Método para identificar el tipo del token
    def identifica_token(self, token):
        if re.fullmatch(r'\d+[a-zA-Z_][a-zA-Z0-9_]*', token):
            return "Error léxico: identificador inválido"
        elif token in self.palabras_reservadas:
            return "Palabra reservada"
        elif self.patron_identificador.fullmatch(token):
            return "Identificador"
        elif self.patron_entero.fullmatch(token):
            return "Entero"
        elif self.patron_flotante.fullmatch(token):
            return "Flotante"
        elif self.patron_cadena.fullmatch(token):
            return "Cadena"
        elif self.patron_aritmetico.fullmatch(token):
            return "Signo aritmetico"
        elif self.patron_relacional.fullmatch(token):
            return "Signo relacional"
        elif self.patron_logico.fullmatch(token):
            return "Operador logico"
        elif token == "=":
            return "Operador de asignacion"
        elif token == "{":
            return "Inicio de bloque"
        elif token == "}":
            return "Fin de bloque"
        elif token in ["(", ")", ",", ";"]:
            return "Simbolo especial"
        elif token.startswith("//"):
            return "Comentario de una linea"
        elif token.startswith("/*") and token.endswith("*/"):
            return "Comentario de bloque"
        else:
            return "token no valido"

    # Método principal del analizador léxico
    def analizar(self, texto):
        self.tokens_validos.clear()
        self.errores_lexicos.clear()

        for num_linea, linea in enumerate(texto.splitlines(), start=1):
            for match in self.token_pattern.finditer(linea):
                token = match.group()
                tipo = self.identifica_token(token)
                
                # Ignorar comentarios
                if tipo in ["Comentario de una linea", "Comentario de bloque"]:
                    continue
                
                # Guardar símbolos en tabla de simbolos
                if tipo == "Identificador" and self.tabla_simbolos:
                    simbolo = {
                        "identificador": token,
                        "categoria": tipo,
                        "tipo_dato": tipo if tipo != "Identificador" else None,
                        "ambito": "global",
                        "direccion": None,
                        "linea": num_linea,
                        "valor": token if tipo != "Identificador" else None,
                        "estado": "declarado",
                        "estructura": None,
                        "contador_referencias": 0
                    }
                    self.tabla_simbolos.insertar_simbolo(simbolo)
                    
                if tipo == "token no valido" or "Error léxico" in tipo:
                    self.errores_lexicos.append({
                        "token": token,
                        "tipo": tipo,
                        "linea": num_linea,
                        
                    })
                else:
                    self.tokens_validos.append({
                        "token": token,
                        "tipo": tipo,
                        "linea": num_linea,
                        
                    })

        return self.tokens_validos, self.errores_lexicos
