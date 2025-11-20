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
        self.contador_direccion = 0
        self.pila_ambitos = ["Global"]
        self.errores_semanticos = []
        self.simbolos_por_ambito = {"Global": []}


    def _tamanio_simbolo(self, simbolo):
        tipo = simbolo.get("tipo_dato", "DESCONOCIDO")
        valor = simbolo.get("valor")
        
        tamanios = {
            'TIPO_ENTERO': 4,
            'TIPO_FLOTANTE': 8,
            'TIPO_BOOLEANO': 1,
            'TIPO_CARACTER': 1,
            'TIPO_CADENA': len(str(valor)) + 1 if valor else 8,  # +1 para null terminator
            'TIPO_VACIO': 0
        }
        
        return tamanios.get(tipo, 4)  # Default 4 bytes

    # ------------------------------------------
    # INSERCIÓN Y ACTUALIZACIÓN
    # ------------------------------------------

    def insertar(self, simbolo):
        """Inserta símbolo con verificación de duplicados"""
        nombre = simbolo.get("identificador")
        ambito_actual = self.ambito_actual()
        
        # Verificar si ya existe en el mismo ámbito
        if self.buscar_en_ambito_actual(nombre):
            self.errores_semanticos.append(f"Error semántico: Identificador '{nombre}' ya declarado en el ámbito '{ambito_actual}'")
            return False
        
        # Asignar ámbito y dirección
        simbolo["ambito"] = ambito_actual
        simbolo["direccion"] = self.obtener_direccion()
        
        # Calcular tamaño y actualizar dirección
        tam = self._tamanio_simbolo(simbolo)
        self.direccion_actual += tam
        
        # Manejar capacidad de memoria
        tam_memoria = sum(self._tamanio_simbolo(s) for s in self.memoria)
        
        if tam_memoria + tam <= self.capacidad_bytes:
            self.memoria.append(simbolo)
        else:
            self.overflow.append(simbolo)
            self._guardar_overflow()
        
        # Registrar en símbolos por ámbito
        if ambito_actual not in self.simbolos_por_ambito:
            self.simbolos_por_ambito[ambito_actual] = []
        self.simbolos_por_ambito[ambito_actual].append(simbolo)
        
        return True
    
    
    def buscar(self, identificador, ambito=None):
        """Busca un símbolo en el ámbito actual y padres (scope chain)"""
        if ambito:
            # Búsqueda en ámbito específico
            if ambito in self.simbolos_por_ambito:
                for s in self.simbolos_por_ambito[ambito]:
                    if s.get("identificador") == identificador:
                        return s
            return None
        
        # Búsqueda en la cadena de ámbitos (del más interno al más externo)
        for ambito_actual in reversed(self.pila_ambitos):
            if ambito_actual in self.simbolos_por_ambito:
                for s in self.simbolos_por_ambito[ambito_actual]:
                    if s.get("identificador") == identificador:
                        return s
        return None

    def buscar_en_ambito_actual(self, identificador):
        """Busca solo en el ámbito actual"""
        ambito_actual = self.ambito_actual()
        if ambito_actual in self.simbolos_por_ambito:
            for s in self.simbolos_por_ambito[ambito_actual]:
                if s.get("identificador") == identificador:
                    return s
        return None

    def actualizar(self, identificador, valor):
        simbolo = self.buscar(identificador)
        if simbolo:
            simbolo["valor"] = valor
            simbolo["estado"] = "actualizado"
        else:
            raise KeyError(f"Símbolo '{identificador}' no encontrado")

    # ------------------------------------------
    # UTILIDADES DE MEMORIA
    # ------------------------------------------

    def _guardar_overflow(self):
        with open(self.archivo_backup, "w", encoding='utf-8') as f:
            json.dump(self.overflow, f, indent=4, ensure_ascii=False)

    def obtener_todos(self):
        todos = self.memoria.copy()
        if os.path.exists(self.archivo_backup):
            with open(self.archivo_backup, "r", encoding='utf-8') as f:
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


    def entrar_ambito(self, nombre):
        self.pila_ambitos.append(nombre)
        if nombre not in self.simbolos_por_ambito:
            self.simbolos_por_ambito[nombre] = []

    def salir_ambito(self):
        """Sale del ámbito actual"""
        if len(self.pila_ambitos) > 1:  # No salir del ámbito Global
            self.pila_ambitos.pop()

    def ambito_actual(self):
        return self.pila_ambitos[-1] if self.pila_ambitos else "Global"

    def en_clase(self):
        return any(isinstance(a, str) and a.startswith("clase:") for a in self.pila_ambitos)

    def limpiar_errores(self):
        """Limpia los errores semánticos acumulados"""
        self.errores_semanticos = []
        

    def obtener_errores_semanticos(self):
        return self.errores_semanticos
    
    def verificar_declaracion(self, identificador, linea):
        """Verifica que un identificador esté declarado antes de usarlo"""
        simbolo = self.buscar(identificador)
        if not simbolo:
            self.errores_semanticos.append(f"Línea {linea}: Identificador '{identificador}' no declarado")
            return False
        return True

tabla = TablaSimbolos()
