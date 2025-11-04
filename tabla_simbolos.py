# archivo: tabla_de_simbolos.py
import json
import os

class TablaSimbolos:
    def __init__(self, capacidad_bytes=100, archivo_backup="tabla_overflow.json"):
        self.capacidad_bytes = capacidad_bytes
        self.archivo_backup = archivo_backup
        self.memoria = []
        self.overflow = []
        self.direccion_actual = 0

    def _tamanio_simbolo(self, simbolo):
        tipo = simbolo.get("tipo_dato")
        valor = simbolo.get("valor")

        if tipo == "entero":
            return 4
        elif tipo == "flotante":
            return 8
        elif tipo == "cadena" and valor is not None:
            return len(valor.encode("utf-8"))
        return 4

    def insertar(self, simbolo):
        """Inserta símbolo con dirección de memoria y maneja overflow"""
        tam = self._tamanio_simbolo(simbolo)
        simbolo["direccion"] = self.direccion_actual
        self.direccion_actual += tam

        tam_memoria = sum(self._tamanio_simbolo(s) for s in self.memoria)

        if tam_memoria + tam <= self.capacidad_bytes:
            self.memoria.append(simbolo)
        else:
            self.overflow.append(simbolo)
            self._guardar_overflow()

    def actualizar(self, identificador, valor):
        """Actualiza valor del símbolo en tabla"""
        simbolo = self.buscar_simbolo(identificador)
        if simbolo:
            simbolo["valor"] = valor

    def _guardar_overflow(self):
        with open(self.archivo_backup, "w") as f:
            json.dump(self.overflow, f, indent=4)

    def obtener_todos(self):
        todos = self.memoria.copy()
        if os.path.exists(self.archivo_backup):
            with open(self.archivo_backup, "r") as f:
                todos.extend(json.load(f))
        return todos

    def buscar_simbolo(self, identificador):
        for s in self.memoria + self.overflow:
            if s["identificador"] == identificador:
                return s
        return None


tabla = TablaSimbolos()
