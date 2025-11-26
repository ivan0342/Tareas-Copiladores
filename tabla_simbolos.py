# archivo: tabla_simbolos.py
import json
import os
from typing import Dict, List, Any, Optional


class InformacionVariable:
    def __init__(self, tipo_dato: str, ambito: str, linea_declaracion: int):
        self.tipo_dato = tipo_dato
        self.ambito = ambito
        self.linea_declaracion = linea_declaracion
        self.estado = "declarada"
        self.contador_referencias = 0
        self.tamanio_bytes = self._calcular_tamanio(tipo_dato)  # ← Ahora funciona
        self.direccion_relativa = None
        self.es_constante = False
        self.modificable = True
        self.valor = None
        self.vivo = True



    def _calcular_tamanio(self, tipo_dato: str) -> int:
        """Calcular tamaño basado solo en el tipo (versión simplificada)"""
        tamanios = {
            'TIPO_ENTERO': 4,
            'entero': 4,
            'TIPO_FLOTANTE': 8,
            'flotante': 8,
            'TIPO_BOOLEANO': 1,
            'booleano': 1,
            'TIPO_CARACTER': 1,
            'caracter': 1,
            'TIPO_CADENA': 8,  # Tamaño fijo para cadenas (puntero)
            'cadena': 8,  # Tamaño fijo para cadenas (puntero)
            'TIPO_VACIO': 0,
            'vacio': 0
        }
        return tamanios.get(tipo_dato, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tipo_dato": self.tipo_dato,
            "ambito": self.ambito,
            "linea_declaracion": self.linea_declaracion,
            "estado": self.estado,
            "contador_referencias": self.contador_referencias,
            "tamanio_bytes": self.tamanio_bytes,
            "direccion_relativa": self.direccion_relativa,
            "es_constante": self.es_constante,
            "modificable": self.modificable,
            "valor": self.valor,
            "vivo": self.vivo
        }


class InformacionParametro:
    def __init__(self, nombre: str, tipo_dato: str, paso_por_referencia: bool = False):
        self.nombre = nombre
        self.tipo_dato = tipo_dato
        self.paso_por_referencia = paso_por_referencia
        self.valor_por_defecto = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nombre": self.nombre,
            "tipo_dato": self.tipo_dato,
            "paso_por_referencia": self.paso_por_referencia,
            "valor_por_defecto": self.valor_por_defecto
        }


class InformacionFuncion:
    def __init__(self, nombre: str, tipo_retorno: str, ambito: str, linea_declaracion: int):
        self.nombre = nombre
        self.tipo_retorno = tipo_retorno
        self.ambito = ambito
        self.linea_declaracion = linea_declaracion
        self.parametros: List[InformacionParametro] = []
        self.variables_locales: Dict[str, InformacionVariable] = {}
        self.estado_implementacion = "declarada"
        self.contador_llamadas = 0
        self.tiene_retorno = False
        self.complejidad_ciclomatica = 1

    def agregar_parametro(self, parametro: InformacionParametro):
        self.parametros.append(parametro)

    def agregar_variable_local(self, nombre: str, variable: InformacionVariable):
        self.variables_locales[nombre] = variable

    def obtener_firma(self) -> str:
        parametros_str = ", ".join([f"{p.tipo_dato} {p.nombre}" for p in self.parametros])
        return f"{self.tipo_retorno} {self.nombre}({parametros_str})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nombre": self.nombre,
            "tipo_retorno": self.tipo_retorno,
            "ambito": self.ambito,
            "linea_declaracion": self.linea_declaracion,
            "parametros": [p.to_dict() for p in self.parametros],
            "variables_locales": {k: v.to_dict() for k, v in self.variables_locales.items()},
            "estado_implementacion": self.estado_implementacion,
            "contador_llamadas": self.contador_llamadas,
            "tiene_retorno": self.tiene_retorno,
            "complejidad_ciclomatica": self.complejidad_ciclomatica,
            "firma": self.obtener_firma()
        }


class InformacionClase:
    def __init__(self, nombre: str, ambito: str, linea_declaracion: int):
        self.nombre = nombre
        self.ambito = ambito
        self.linea_declaracion = linea_declaracion
        self.atributos: Dict[str, InformacionVariable] = {}
        self.metodos: Dict[str, InformacionFuncion] = {}
        self.herencia: List[str] = []
        self.implementa: List[str] = []
        self.acceso = "publico"
        self.es_abstracta = False

    def agregar_atributo(self, nombre: str, atributo: InformacionVariable):
        self.atributos[nombre] = atributo

    def agregar_metodo(self, nombre: str, metodo: InformacionFuncion):
        self.metodos[nombre] = metodo

    def agregar_herencia(self, clase_base: str):
        self.herencia.append(clase_base)

    def agregar_implementacion(self, interfaz: str):
        self.implementa.append(interfaz)

    def obtener_arbol_herencia(self) -> List[str]:
        arbol = [self.nombre]
        arbol.extend(self.herencia)
        return arbol

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nombre": self.nombre,
            "ambito": self.ambito,
            "linea_declaracion": self.linea_declaracion,
            "atributos": {k: v.to_dict() for k, v in self.atributos.items()},
            "metodos": {k: v.to_dict() for k, v in self.metodos.items()},
            "herencia": self.herencia,
            "implementa": self.implementa,
            "acceso": self.acceso,
            "es_abstracta": self.es_abstracta,
            "arbol_herencia": self.obtener_arbol_herencia()
        }


class TablaSimbolos:
    def __init__(self, capacidad_bytes=100, archivo_backup="tabla_overflow.json"):
        # ========== ESTRUCTURA ANTIGUA (COMPATIBILIDAD) ==========
        self.capacidad_bytes = capacidad_bytes
        self.archivo_backup = archivo_backup
        self.memoria = []  # Lista antigua para compatibilidad
        self.overflow = []  # Lista antigua para compatibilidad
        self.direccion_actual = 0
        self.contador_direccion = 0
        self.pila_ambitos = ["Global"]
        self.errores_semanticos = []
        self.simbolos_por_ambito = {"Global": []}

        # ========== ESTRUCTURA NUEVA EXTENDIDA ==========
        self.variables_extendidas: Dict[str, InformacionVariable] = {}
        self.funciones_extendidas: Dict[str, InformacionFuncion] = {}
        self.clases_extendidas: Dict[str, InformacionClase] = {}
        self.constantes_extendidas: Dict[str, InformacionVariable] = {}
        self.grafo_referencias = {}

    def resetear(self):
        """Reinicia la tabla de símbolos PERO preserva contadores de referencias"""
        print("DEBUG: Realizando reset selectivo - PRESERVANDO contadores")

        # ========== ESTRUCTURA ANTIGUA ==========
        self.memoria = []
        self.overflow = []
        self.direccion_actual = 0
        # NO resetear: self.contador_direccion (para mantener direcciones únicas)
        self.pila_ambitos = ["Global"]
        self.errores_semanticos = []
        self.simbolos_por_ambito = {"Global": []}

        # ========== ESTRUCTURA NUEVA EXTENDIDA ==========
        # 🔥 CORRECCIÓN CRÍTICA: PRESERVAR contadores de referencias
        # Solo limpiar valores temporales, NO los contadores

        # Para variables extendidas
        for nombre, variable in self.variables_extendidas.items():
            # Preservar el contador de referencias
            contador_actual = variable.contador_referencias
            # Resetear otros campos
            variable.valor = None
            variable.estado = "declarada"
            variable.vivo = True
            # 🔥 RESTAURAR el contador preservado
            variable.contador_referencias = contador_actual
            print(f"DEBUG: Variable '{nombre}' - contador preservado: {contador_actual}")

        # Para constantes extendidas
        for nombre, constante in self.constantes_extendidas.items():
            contador_actual = constante.contador_referencias
            constante.valor = None
            constante.estado = "declarada"
            constante.contador_referencias = contador_actual
            print(f"DEBUG: Constante '{nombre}' - contador preservado: {contador_actual}")

        # Resetear otras estructuras que no afectan contadores
        self.grafo_referencias = {}

        print("DEBUG: Reset selectivo completado - contadores PRESERVADOS")

    # ========== MÉTODOS ANTIGUOS (COMPATIBILIDAD CON PARSER ACTUAL) ==========

    def _tamanio_simbolo(self, simbolo):
        """Método antiguo - mantener compatibilidad"""
        tipo = simbolo.get("tipo_dato", "DESCONOCIDO")
        valor = simbolo.get("valor")

        tamanios = {
            'TIPO_ENTERO': 4,
            'TIPO_FLOTANTE': 8,
            'TIPO_BOOLEANO': 1,
            'TIPO_CARACTER': 1,
            'TIPO_CADENA': len(str(valor)) + 1 if valor else 8,
            'TIPO_VACIO': 0
        }

        return tamanios.get(tipo, 4)

    def insertar(self, simbolo):
        """MÉTODO ANTIGUO - mantener para compatibilidad con parser"""
        nombre = simbolo.get("identificador")
        ambito_actual = self.ambito_actual()

        # Verificar si ya existe en el mismo ámbito (comportamiento antiguo)
        if self.buscar_en_ambito_actual(nombre):
            self.errores_semanticos.append(
                f"Error semántico: Identificador '{nombre}' ya declarado en el ámbito '{ambito_actual}'")
            return False

        # Asignar ámbito y dirección (comportamiento antiguo)
        simbolo["ambito"] = ambito_actual
        simbolo["direccion"] = self.obtener_direccion()

        # Calcular tamaño y actualizar dirección (comportamiento antiguo)
        tam = self._tamanio_simbolo(simbolo)
        self.direccion_actual += tam

        # Manejar capacidad de memoria (comportamiento antiguo)
        tam_memoria = sum(self._tamanio_simbolo(s) for s in self.memoria)

        if tam_memoria + tam <= self.capacidad_bytes:
            self.memoria.append(simbolo)
        else:
            self.overflow.append(simbolo)
            self._guardar_overflow()

        # Registrar en símbolos por ámbito (comportamiento antiguo)
        if ambito_actual not in self.simbolos_por_ambito:
            self.simbolos_por_ambito[ambito_actual] = []
        self.simbolos_por_ambito[ambito_actual].append(simbolo)

        # ========== NUEVO: También insertar en estructura extendida ==========
        self._insertar_en_estructura_extendida(simbolo)

        return True

    def _insertar_en_estructura_extendida(self, simbolo):
        """Inserta el símbolo en la nueva estructura extendida"""
        nombre = simbolo.get("identificador")
        categoria = simbolo.get("categoria")
        tipo_dato = simbolo.get("tipo_dato")
        linea = simbolo.get("linea", 0)
        valor = simbolo.get("valor")
        ambito = simbolo.get("ambito", "Global")

        if categoria == "variable":
            info_var = InformacionVariable(tipo_dato, ambito, linea)
            info_var.valor = valor
            info_var.direccion_relativa = simbolo.get("direccion")
            info_var.estado = simbolo.get("estado", "declarada")
            self.variables_extendidas[nombre] = info_var

        elif categoria == "constante":
            info_var = InformacionVariable(tipo_dato, ambito, linea)
            info_var.valor = valor
            info_var.es_constante = True
            info_var.modificable = False
            self.constantes_extendidas[nombre] = info_var

        elif categoria == "funcion":
            info_func = InformacionFuncion(nombre, tipo_dato, ambito, linea)
            self.funciones_extendidas[nombre] = info_func

        elif categoria == "clase":
            info_clase = InformacionClase(nombre, ambito, linea)
            self.clases_extendidas[nombre] = info_clase

    def buscar(self, identificador, ambito=None):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        # Comportamiento antiguo
        if ambito:
            if ambito in self.simbolos_por_ambito:
                for s in self.simbolos_por_ambito[ambito]:
                    if s.get("identificador") == identificador:
                        return s
            return None

        for ambito_actual in reversed(self.pila_ambitos):
            if ambito_actual in self.simbolos_por_ambito:
                for s in self.simbolos_por_ambito[ambito_actual]:
                    if s.get("identificador") == identificador:
                        return s
        return None

    def buscar_en_ambito_actual(self, identificador):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        ambito_actual = self.ambito_actual()
        if ambito_actual in self.simbolos_por_ambito:
            for s in self.simbolos_por_ambito[ambito_actual]:
                if s.get("identificador") == identificador:
                    return s
        return None

    def actualizar(self, identificador, valor):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        simbolo = self.buscar(identificador)
        if simbolo:
            simbolo["valor"] = valor
            simbolo["estado"] = "actualizado"

            # ========== NUEVO: También actualizar en estructura extendida ==========
            if identificador in self.variables_extendidas:
                self.variables_extendidas[identificador].valor = valor
                self.variables_extendidas[identificador].estado = "actualizada"
        else:
            raise KeyError(f"Símbolo '{identificador}' no encontrado")

    def _guardar_overflow(self):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        with open(self.archivo_backup, "w", encoding='utf-8') as f:
            json.dump(self.overflow, f, indent=4, ensure_ascii=False)

    def obtener_todos(self):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        todos = self.memoria.copy()
        if os.path.exists(self.archivo_backup):
            with open(self.archivo_backup, "r", encoding='utf-8') as f:
                try:
                    todos.extend(json.load(f))
                except json.JSONDecodeError:
                    pass
        return todos

    def obtener_direccion(self):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        direccion = f"0x{self.contador_direccion:04X}"
        self.contador_direccion += 1
        return direccion

    def entrar_ambito(self, nombre):
        """MÉTODO COMPARTIDO - funciona para ambas estructuras"""
        self.pila_ambitos.append(nombre)
        if nombre not in self.simbolos_por_ambito:
            self.simbolos_por_ambito[nombre] = []

    def salir_ambito(self):
        """MÉTODO COMPARTIDO"""
        if len(self.pila_ambitos) > 1:
            self.pila_ambitos.pop()

    def ambito_actual(self):
        """MÉTODO COMPARTIDO"""
        return self.pila_ambitos[-1] if self.pila_ambitos else "Global"

    def en_clase(self):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        return any(isinstance(a, str) and a.startswith("clase:") for a in self.pila_ambitos)

    def limpiar_errores(self):
        """MÉTODO COMPARTIDO"""
        self.errores_semanticos = []

    def obtener_errores_semanticos(self):
        """MÉTODO COMPARTIDO"""
        return self.errores_semanticos

    def verificar_declaracion(self, identificador, linea):
        """MÉTODO ANTIGUO - mantener compatibilidad"""
        simbolo = self.buscar(identificador)
        if not simbolo:
            self.errores_semanticos.append(f"Línea {linea}: Identificador '{identificador}' no declarado")
            return False
        return True

    # ========== MÉTODOS NUEVOS EXTENDIDOS ==========

    def insertar_variable_extendida(self, nombre: str, tipo_dato: str, linea: int,
                                    es_constante: bool = False, valor=None) -> bool:
        """NUEVO MÉTODO - Insertar variable en estructura extendida CORREGIDO"""
        if self.buscar_variable_extendida_ambito_actual(nombre):
            self.errores_semanticos.append(f"Variable '{nombre}' ya declarada en ámbito actual")
            return False

        ambito = self.ambito_actual()
        variable = InformacionVariable(tipo_dato, ambito, linea)
        variable.es_constante = es_constante
        variable.valor = valor
        variable.direccion_relativa = self._asignar_direccion_extendida(variable.tamanio_bytes)

        # CORRECCIÓN: Inicializar contador explícitamente
        variable.contador_referencias = 0

        if es_constante:
            self.constantes_extendidas[nombre] = variable
        else:
            self.variables_extendidas[nombre] = variable

        self._actualizar_grafo_referencias(nombre, "declaracion")
        return True

    def buscar_variable_extendida(self, nombre: str) -> Optional[InformacionVariable]:
        """NUEVO MÉTODO - Buscar variable en estructura extendida"""
        # Buscar en ámbito actual y padres
        for ambito in reversed(self.pila_ambitos):
            for var_nombre, variable in self.variables_extendidas.items():
                if var_nombre == nombre and variable.ambito == ambito:
                    variable.contador_referencias += 1
                    return variable

            for const_nombre, constante in self.constantes_extendidas.items():
                if const_nombre == nombre and constante.ambito == ambito:
                    constante.contador_referencias += 1
                    return constante

        return None

    def buscar_variable_extendida_ambito_actual(self, nombre: str) -> Optional[InformacionVariable]:
        """NUEVO MÉTODO - Buscar solo en ámbito actual"""
        ambito_actual = self.ambito_actual()

        if (nombre in self.variables_extendidas and
                self.variables_extendidas[nombre].ambito == ambito_actual):
            return self.variables_extendidas[nombre]

        if (nombre in self.constantes_extendidas and
                self.constantes_extendidas[nombre].ambito == ambito_actual):
            return self.constantes_extendidas[nombre]

        return None

    def insertar_funcion_extendida(self, nombre: str, tipo_retorno: str, linea: int) -> bool:
        """NUEVO MÉTODO - Insertar función en estructura extendida"""
        if nombre in self.funciones_extendidas:
            self.errores_semanticos.append(f"Función '{nombre}' ya declarada")
            return False

        funcion = InformacionFuncion(nombre, tipo_retorno, "Global", linea)
        self.funciones_extendidas[nombre] = funcion
        return True

    def buscar_funcion_extendida(self, nombre: str) -> Optional[InformacionFuncion]:
        """NUEVO MÉTODO - Buscar función en estructura extendida"""
        return self.funciones_extendidas.get(nombre)

    # ========== MÉTODOS DE GESTIÓN DE MEMORIA EXTENDIDA ==========

    def _asignar_direccion_extendida(self, tamanio: int) -> str:
        """NUEVO MÉTODO - Asignar dirección en estructura extendida"""
        direccion = f"0x{self.contador_direccion:04X}"
        self.contador_direccion += 1
        self.direccion_actual += tamanio
        return direccion

    def obtener_uso_memoria_extendido(self) -> Dict[str, Any]:
        """NUEVO MÉTODO - Obtener uso de memoria de estructura extendida"""
        total_variables = len(self.variables_extendidas) + len(self.constantes_extendidas)
        memoria_utilizada = self.direccion_actual
        porcentaje_uso = (memoria_utilizada / self.capacidad_bytes) * 100 if self.capacidad_bytes > 0 else 0

        return {
            "total_variables": total_variables,
            "memoria_utilizada_bytes": memoria_utilizada,
            "capacidad_total_bytes": self.capacidad_bytes,
            "porcentaje_uso": f"{porcentaje_uso:.2f}%",
            "variables_por_ambito": self._contar_variables_por_ambito_extendido()
        }

    def _contar_variables_por_ambito_extendido(self) -> Dict[str, int]:
        """NUEVO MÉTODO - Contar variables por ámbito en estructura extendida"""
        conteo = {}
        for variable in self.variables_extendidas.values():
            conteo[variable.ambito] = conteo.get(variable.ambito, 0) + 1
        for constante in self.constantes_extendidas.values():
            conteo[constante.ambito] = conteo.get(constante.ambito, 0) + 1
        return conteo

    # ========== MÉTODOS DE ANÁLISIS PARA OPTIMIZACIÓN ==========

    def _actualizar_grafo_referencias(self, simbolo: str, tipo_referencia: str):
        """NUEVO MÉTODO - Actualizar grafo de referencias"""
        if simbolo not in self.grafo_referencias:
            self.grafo_referencias[simbolo] = {
                "declaraciones": [],
                "referencias": [],
                "actualizaciones": []
            }

        if tipo_referencia.startswith("declaracion"):
            self.grafo_referencias[simbolo]["declaraciones"].append(tipo_referencia)
        elif tipo_referencia.startswith("actualizacion"):
            self.grafo_referencias[simbolo]["actualizaciones"].append(tipo_referencia)
        else:
            self.grafo_referencias[simbolo]["referencias"].append(tipo_referencia)

    def obtener_variables_no_utilizadas_extendidas(self) -> List[str]:
        """NUEVO MÉTODO - Identificar variables no utilizadas CORREGIDO"""
        print("DEBUG: Calculando variables no utilizadas...")
        no_utilizadas = []

        for nombre, variable in self.variables_extendidas.items():
            print(f"DEBUG: Variable '{nombre}' - referencias: {variable.contador_referencias}")
            # CORRECCIÓN: Solo considerar variables con 0 referencias como no utilizadas
            if variable.contador_referencias == 0:
                no_utilizadas.append(nombre)
                print(f"DEBUG: → '{nombre}' marcada como no utilizada")
            else:
                print(f"DEBUG: → '{nombre}' TIENE {variable.contador_referencias} referencias - NO es no utilizada")

        print(f"DEBUG: Total variables no utilizadas: {len(no_utilizadas)}")
        return no_utilizadas

    def obtener_variables_muertas_extendidas(self) -> List[str]:
        """NUEVO MÉTODO - Identificar variables muertas"""
        muertas = []
        for nombre, variable in self.variables_extendidas.items():
            if (variable.ambito != "Global" and
                    variable.contador_referencias > 0 and
                    len(self.grafo_referencias.get(nombre, {}).get("referencias", [])) ==
                    len(self.grafo_referencias.get(nombre, {}).get("actualizaciones", []))):
                muertas.append(nombre)
        return muertas

    # ========== MÉTODOS DE SERIALIZACIÓN Y REPORTES ==========

    def generar_reporte_completo_extendido(self) -> Dict[str, Any]:
        """NUEVO MÉTODO - Generar reporte completo de estructura extendida"""
        return {
            "variables": {k: v.to_dict() for k, v in self.variables_extendidas.items()},
            "constantes": {k: v.to_dict() for k, v in self.constantes_extendidas.items()},
            "funciones": {k: v.to_dict() for k, v in self.funciones_extendidas.items()},
            "clases": {k: v.to_dict() for k, v in self.clases_extendidas.items()},
            "uso_memoria": self.obtener_uso_memoria_extendido(),
            "estadisticas": {
                "total_simbolos": (len(self.variables_extendidas) + len(self.constantes_extendidas) +
                                   len(self.funciones_extendidas) + len(self.clases_extendidas)),
                "variables_no_utilizadas": self.obtener_variables_no_utilizadas_extendidas(),
                "variables_muertas": self.obtener_variables_muertas_extendidas(),
                "errores_semanticos": self.errores_semanticos
            },
            "grafo_referencias": self.grafo_referencias
        }

    def guardar_estado_extendido(self, archivo: str = None):
        """NUEVO MÉTODO - Guardar estado de estructura extendida"""
        archivo = archivo or "tabla_extendida_backup.json"
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(self.generar_reporte_completo_extendido(), f, indent=2, ensure_ascii=False)

    def mostrar_estado_dual(self):
        """NUEVO MÉTODO - Mostrar estado de ambas estructuras"""
        print("=== ESTRUCTURA ANTIGUA ===")
        print(f"Total símbolos: {len(self.memoria)}")
        print(f"Ámbito actual: {self.ambito_actual()}")

        print("\n=== ESTRUCTURA EXTENDIDA ===")
        reporte = self.generar_reporte_completo_extendido()
        print(f"Variables: {len(reporte['variables'])}")
        print(f"Constantes: {len(reporte['constantes'])}")
        print(f"Funciones: {len(reporte['funciones'])}")
        print(f"Clases: {len(reporte['clases'])}")
        print(f"Uso memoria: {reporte['uso_memoria']['porcentaje_uso']}")


# Instancia global para compatibilidad
tabla = TablaSimbolos()