from lexico import Lexico
from leeFlujo import FileManager
from interfaz import Interfaz
class Main:
    def __init__(self):
        self.contenido = None
        self.interfaz = Interfaz()
        self.tokens = []
        self.lexico = Lexico()

    def primerPaso(self, nombre_archivo):
        archivoLeido   = FileManager(nombre_archivo)
        self.contenido = archivoLeido.leer_archivo('T')

    def segundoPaso(self):
        self.tokens = self.lexico.categorizaElementos(self.contenido)

    def tercerPaso(self):
        for elemento in self.tokens:
            print(f"Token: {elemento} es: {self.lexico.identificaToken(elemento)}")

    def muestraContenido(self):
        print(self.contenido)
        
    def ejecucion_Programa(self):
        self.interfaz.ejecutar();

ejecuta = Main()
ejecuta.primerPaso("nombre_archivo.hp")

ejecuta.ejecucion_Programa()
