import json

class TablaSimbolos:
    def __init__(self, capacidad_bytes=100, archivo_backup="tabla_overflow.json"):
        self.capacidad_bytes = capacidad_bytes
        self.archivo_backup = archivo_backup
        self.memoria = []          # símbolos en memoria principal
        self.overflow = []         # símbolos que no caben y van al JSON
        self.direccion_actual = 0  # contador de direcciones de memoria
        self.simbolos = []

    def _tamanio_simbolo(self, simbolo):
        """Calcula tamaño en bytes según categoría del símbolo"""
        categoria = simbolo.get("categoria")
        valor = simbolo.get("valor")

        if categoria == "Entero":
            return 4
        elif categoria == "Flotante":
            return 8
        elif categoria == "Cadena" and valor is not None:
            return len(valor.encode("utf-8"))
        else:  # Identificador u otros
            return 4

    def insertar_simbolo(self, simbolo):
        """Inserta un símbolo y le asigna dirección de memoria"""
        tam_simbolo = self._tamanio_simbolo(simbolo)
        simbolo["direccion"] = self.direccion_actual
        self.direccion_actual += tam_simbolo

        tam_memoria = sum(self._tamanio_simbolo(s) for s in self.memoria)
        if tam_memoria + tam_simbolo <= self.capacidad_bytes:
            self.memoria.append(simbolo)
        else:
            self.overflow.append(simbolo)
            self._guardar_overflow()

    def _guardar_overflow(self):
        """Guarda los símbolos que exceden la memoria principal en archivo JSON"""
        with open(self.archivo_backup, "w") as f:
            json.dump(self.overflow, f, indent=4)

    def obtener_todos(self):
        """Devuelve todos los símbolos: memoria principal + overflow"""
        todos = self.memoria.copy()
        try:
            with open(self.archivo_backup, "r") as f:
                overflow = json.load(f)
                todos.extend(overflow)
        except FileNotFoundError:
            pass
        return todos
    
    def buscar_simbolo(self, identificador):
        for s in self.memoria + self.overflow:
            if s["identificador"] == identificador:
                return s
        return None
