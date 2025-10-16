# libreria para el manejo de expresiones regulares
import re

class Lexico:
    patron_identificador = re.compile(r"^[a-zA-Z]+$")
    patron_entero = re.compile(r"^[0-9]+$")
    patron_flotante = re.compile(r"^[0-9]+\.[0-9]+$")
    patron_cadena = re.compile(r'^".*"$')
    patron_aritmetico = re.compile(r'^(\+|-|\*|/|%|\+\+|--)$')
    patron_relacional = re.compile(r'^(==|!=|<=|>=|<|>)$')
    patron_logico = re.compile(r'^(&&|\|\||!)$')



    palabras_reservadas = ["entero", "flotante", "booleano", "caracter", "cadena", "arreglo",
                           "clase", "interfaz", "enumeracion", "si", "sino", "segun", "defecto",
                           "mientras", "para", "hacer", "romper", "continuar", "retornar", "intentar",
                           "capturar", "importar", "exportar", "hereda", "nuevo", "usar"]
    
    def __init__(self):
        self.tokens_validos = []
        self.errores = []

    # Dado un texto, devuelve un arreglo de elementos eliminando espacios y tabuladores
    def categorizaElementos(self, texto):
        tokens = re.findall(r"\S+", texto)
        return tokens

    def identificaToken(self, token):
        if token in self.palabras_reservadas:
            return "Palabra reservada"
        elif re.match(self.patron_identificador, token):
            return "Identificador"
        elif re.match(self.patron_entero, token):
            return "Entero"
        elif re.match(self.patron_flotante, token):
            return "Flotante"
        elif re.match(self.patron_cadena, token):
            return "Cadena"
        elif re.match(self.patron_aritmetico, token):
            return "Signo aritmetico"
        elif re.match(self.patron_relacional, token):
            return "Signo relacional"
        elif re.match(self.patron_logico, token):
            return "Identificador logico"
        elif token == "=":
            return "Operador de asignacion"
        elif token == "{":
            return "token inicio de bloque"
        elif token == "}":
            return "token fin de bloque"
        elif token in ["(", ")", ",", ";"]:
            return "Simbolo especial"
        elif token.startswith("//"):
            return "Comentario de una linea"
        else:
            return "token no valido"

