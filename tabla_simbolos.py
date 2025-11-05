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
        self.contador_direccion = 0  # Para generar direcciones únicas tipo 0x0001

    # ------------------------------------------
    # MÉTODOS DE APOYO
    # ------------------------------------------

    def _tamanio_simbolo(self, simbolo):
        tipo = simbolo.get("Tipo de dato") or simbolo.get("tipo_dato")
        valor = simbolo.get("Valor") or simbolo.get("valor")

        if tipo in ["entero", "int", "TIPO_ENTERO"]:
            return 4
        elif tipo in ["flotante", "float", "TIPO_FLOTANTE"]:
            return 8
        elif tipo in ["cadena", "string", "TIPO_CADENA"] and valor is not None:
            return len(str(valor).encode("utf-8"))
        return 4  # Tamaño por defecto

    # ------------------------------------------
    # INSERCIÓN Y ACTUALIZACIÓN
    # ------------------------------------------

    def insertar(self, simbolo):
        """Inserta símbolo con dirección de memoria y maneja overflow"""
        tam = self._tamanio_simbolo(simbolo)
        simbolo["Dirección"] = self.obtener_direccion()
        self.direccion_actual += tam

        tam_memoria = sum(self._tamanio_simbolo(s) for s in self.memoria)

        if tam_memoria + tam <= self.capacidad_bytes:
            self.memoria.append(simbolo)
        else:
            self.overflow.append(simbolo)
            self._guardar_overflow()

    def actualizar(self, identificador, valor):
        """Actualiza el valor de un símbolo existente"""
        simbolo = self.buscar(identificador)
        if simbolo:
            simbolo["Valor"] = valor  # o "valor", según cómo se esté guardando
        else:
            raise KeyError(f"Símbolo '{identificador}' no encontrado en la tabla.")

    # ------------------------------------------
    # UTILIDADES DE MEMORIA
    # ------------------------------------------

    def _guardar_overflow(self):
        with open(self.archivo_backup, "w") as f:
            json.dump(self.overflow, f, indent=4, ensure_ascii=False)

    def obtener_todos(self):
        todos = self.memoria.copy()
        if os.path.exists(self.archivo_backup):
            with open(self.archivo_backup, "r") as f:
                try:
                    todos.extend(json.load(f))
                except json.JSONDecodeError:
                    pass
        return todos

    def obtener_direccion(self):
        """Genera una dirección única tipo 0x0001"""
        direccion = f"0x{self.contador_direccion:04X}"
        self.contador_direccion += 1
        return direccion

    # ------------------------------------------
    # BÚSQUEDA
    # ------------------------------------------

    def buscar(self, identificador):
        for s in self.memoria + self.overflow:
            if s.get("Identificador") == identificador or s.get("identificador") == identificador:
                return s
        return None


tabla = TablaSimbolos()
