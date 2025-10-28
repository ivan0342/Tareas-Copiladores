from interfaz import Interfaz
class Main:
    def __init__(self):
        self.contenido = None
        self.interfaz = Interfaz()
        self.tokens = []
                
    def ejecucion_Programa(self):
        self.interfaz.ejecutar();

ejecuta = Main()

ejecuta.ejecucion_Programa()
