from lexico import Lexico

class Analizador:
    def __init__(self):
        self.lexico = Lexico()
        self.tokens_validos = []
        self.errores_lexicos = []
    
    def analizador(self, texto):
        self.tokens_validos.clear()
        self.errores_lexicos.clear()
        
        lineas = texto.splitlines()
        for i, linea in enumerate(lineas, start =1):
            elementos = self.lexico.categorizaElementos(linea);
            
            for elemento in elementos:
                token = self.lexico.identificaToken(elemento)
                if token == "token no valido":
                    
                    columna = linea.find(elemento) +1
                    self.errores_lexicos.append({
                        "token": elemento,
                        "linea": i,
                        "columna": columna
                    })
                else:
                      self.tokens_validos.append({
                        "token": elemento,
                        "tipo": token
                    })
        return self.tokens_validos, self.errores_lexicos
                
        
        
            
        
        