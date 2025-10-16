import re
from lexico import Lexico

class Analizador:
    def __init__(self):
        self.lexico = Lexico()
        self.tokens_validos = []
        self.errores_lexicos = []
    

    def analizador(self, texto):
        self.tokens_validos.clear()
        self.errores_lexicos.clear()

        token_pattern = re.compile(r'''
            "(?:[^"\\]|\\.)*"         | # cadenas entre comillas
            //[^\n]*                  | # comentarios de una línea
            \d+\.\d+                  | # números flotantes
            \d+                       | # números enteros
            [a-zA-Z_][a-zA-Z0-9_]*    | # identificadores
            [=+\-*/<>]                | # operadores
            [(){},;]                   # símbolos especiales   
        ''', re.VERBOSE)

        for num_linea, linea in enumerate(texto.splitlines(), start=1):
            for match in token_pattern.finditer(linea):
                token = match.group()
                columna = match.start() + 1
                tipo = self.lexico.identificaToken(token)
                if tipo == "token no valido":
                    self.errores_lexicos.append({"token": token, "linea": num_linea, "columna": columna})
                else:
                    self.tokens_validos.append({"token": token, "tipo": tipo})

        return self.tokens_validos, self.errores_lexicos
    
    
                
        
        
            
        
        