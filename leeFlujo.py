class FileManager:
    def __init__(self, nombre_archivo):
        self.nombre_archivo = nombre_archivo
        self.contenido = None

    def leer_archivo(self, opcion):
        if self.nombre_archivo:
            # abrir archivo en modo lectura
            with open(self.nombre_archivo,"r") as flujo:
                if opcion == 'T':
                    # leer todo el archivo
                    self.contenido = flujo.read()
                elif opcion == 'L':
                    # devuelve un arreglo por cada linea de codigo fuente leído
                    self.contenido = flujo.readlines()
            return self.contenido
        else:
            return None