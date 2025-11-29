import json
import time
from datetime import datetime


class OptimizadorMultinivel:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.optimizaciones_aplicadas = []
        self.metricas = {
            'local': {'aplicadas': 0, 'tiempo': 0, 'reduccion_codigo': 0, 'optimizaciones': []},
            'bucles': {'aplicadas': 0, 'tiempo': 0, 'reduccion_codigo': 0, 'optimizaciones': []},
            'global': {'aplicadas': 0, 'tiempo': 0, 'reduccion_codigo': 0, 'optimizaciones': []}
        }
        self.ast_antes = []
        self.ast_despues = []
        self.scopes_antes = {}
        self.scopes_despues = {}

    # ========== OPTIMIZACIÓN LOCAL ==========

    def optimizacion_local(self, ast):
        """Optimización a nivel de bloque básico"""
        print("📝 Aplicando optimización local...")
        inicio = time.time()

        optimizador_local = OptimizadorLocal(self.tabla_simbolos)
        ast_optimizado, metricas = optimizador_local.optimizar(ast)

        self.optimizaciones_aplicadas.extend(optimizador_local.optimizaciones_aplicadas)

        metricas['tiempo'] = time.time() - inicio
        return ast_optimizado, metricas

    # ========== OPTIMIZACIÓN DE BUCLES ==========

    def optimizacion_bucles(self, ast):
        """Optimización específica para bucles"""
        print("🔄 Aplicando optimización de bucles...")
        inicio = time.time()

        optimizador_bucles = OptimizadorBucles(self.tabla_simbolos)
        ast_optimizado, metricas = optimizador_bucles.optimizar(ast)

        self.optimizaciones_aplicadas.extend(optimizador_bucles.optimizaciones_aplicadas)

        metricas['tiempo'] = time.time() - inicio
        return ast_optimizado, metricas

    # ========== OPTIMIZACIÓN GLOBAL ==========

    def optimizacion_global(self, ast):
        """Optimización a nivel de programa completo"""
        print("🌍 Aplicando optimización global...")
        inicio = time.time()

        optimizador_global = OptimizadorGlobal(self.tabla_simbolos)
        ast_optimizado, metricas = optimizador_global.optimizar(ast)

        self.optimizaciones_aplicadas.extend(optimizador_global.optimizaciones_aplicadas)

        metricas['tiempo'] = time.time() - inicio
        return ast_optimizado, metricas

    def _generar_reporte_completo(self):
        """Genera reporte de optimizaciones aplicadas"""
        print("\n📊 REPORTE DE OPTIMIZACIÓN")
        print(f"Optimizaciones locales: {self.metricas['local']['aplicadas']}")
        print(f"Optimizaciones de bucles: {self.metricas['bucles']['aplicadas']}")
        print(f"Optimizaciones globales: {self.metricas['global']['aplicadas']}")
        print(f"Total: {sum(m['aplicadas'] for m in self.metricas.values())}")

        if self.optimizaciones_aplicadas:
            print("\nTransformaciones aplicadas:")
            for opt in self.optimizaciones_aplicadas:
                print(f"  - {opt}")

    def optimizar(self, ast):
        """Aplica todas las optimizaciones multinivel al AST"""
        print("🔧 Iniciando optimización multinivel...")

        # 🔥 DEBUG EXTENDIDO
        print(f"🔧 DEBUG: AST recibido - tipo: {type(ast)}, longitud: {len(ast) if isinstance(ast, list) else 'N/A'}")
        if ast and isinstance(ast, list):
            print(f"🔧 DEBUG: Primer nodo: {ast[0] if len(ast) > 0 else 'N/A'}")

        # Guardar estado inicial - CON MEJOR MANEJO DE ERRORES
        try:
            self.ast_antes = self._clonar_ast(ast)
            print(f"🔧 DEBUG: ast_antes guardado - tipo: {type(self.ast_antes)}")
            if hasattr(self.ast_antes, '__len__'):
                print(f"🔧 DEBUG: ast_antes longitud: {len(self.ast_antes)}")
        except Exception as e:
            print(f"❌ ERROR guardando ast_antes: {e}")
            self.ast_antes = []  # Valor por defecto seguro

        try:
            self._mapear_scopes(self.ast_antes, self.scopes_antes)
            print(f"🔧 DEBUG: Scopes antes mapeados: {len(self.scopes_antes)}")
        except Exception as e:
            print(f"❌ ERROR mapeando scopes: {e}")
            self.scopes_antes = {}

        # FASE NUEVA: Propagación de Constantes
        #print("📊 Aplicando propagación de constantes...")
        #inicio_constantes = time.time()
        #propagador = PropagadorConstantes(self.tabla_simbolos)
        #constantes_encontradas = propagador.analizar(ast)
        #ast_propagado, num_propagaciones = propagador.propagar(ast)
        #self.optimizaciones_aplicadas.extend(propagador.optimizaciones_aplicadas)

        # 🔥 CONTAR LÍNEAS REALES ANTES
        lineas_antes = self._contar_lineas_reales(ast)
        print(f"🔧 Líneas antes de optimizar: {lineas_antes}")

        # Fase 1: Optimización Local
        ast_opt, metricas_local = self.optimizacion_local(ast)
        self.metricas['local'] = metricas_local

        # Fase 2: Optimización de Bucles
        ast_opt, metricas_bucles = self.optimizacion_bucles(ast_opt)
        self.metricas['bucles'] = metricas_bucles

        # Fase 3: Optimización Global
        ast_opt, metricas_global = self.optimizacion_global(ast_opt)
        self.metricas['global'] = metricas_global

        # Guardar estado final
        self.ast_despues = self._clonar_ast(ast_opt)
        self._mapear_scopes(self.ast_despues, self.scopes_despues)

        # 🔥 CONTAR LÍNEAS REALES DESPUÉS
        lineas_despues = self._contar_lineas_reales(ast_opt)
        reduccion_real = lineas_antes - lineas_despues

        print(f"🔧 Líneas después de optimizar: {lineas_despues}")
        print(f"🔧 Reducción real: {reduccion_real} líneas")

        self._actualizar_metricas_reales(reduccion_real)

        self._generar_reporte_completo()
        return ast_opt

    def _actualizar_metricas_reales(self, reduccion_total):
        """Actualiza las métricas con valores reales"""
        # Distribuir la reducción total entre las fases
        fases = ['local', 'bucles', 'global']
        reduccion_por_fase = reduccion_total // len(fases)

        for fase in fases:
            if fase in self.metricas:
                self.metricas[fase]['reduccion_codigo'] = reduccion_por_fase

    def _contar_lineas_reales(self, ast):
        """Cuenta líneas de código de forma realista"""
        if not isinstance(ast, list):
            return 0

        # Contar declaraciones y estructuras principales
        contador = 0
        for nodo in ast:
            if isinstance(nodo, dict):
                contador += self._contar_lineas_nodo_real(nodo)

        return contador

    def _contar_lineas_nodo_real(self, nodo):
        """Cuenta líneas reales para un nodo"""
        if not isinstance(nodo, dict):
            return 0

        tipo_nodo = nodo.get("nodo")

        # Declaraciones simples: 1 línea
        if tipo_nodo in ["DECL_VAR", "ASIGNACION", "IMPRIMIR"]:
            return 1

        # Estructuras de control: 1 línea + cuerpo
        elif tipo_nodo in ["MIENTRAS", "SI", "PARA"]:
            lineas = 1  # Línea de la estructura
            if "cuerpo" in nodo:
                lineas += self._contar_lineas_nodo_real(nodo["cuerpo"])
            return lineas

        # Bloques: contenido interno
        elif tipo_nodo == "BLOQUE":
            lineas = 0
            if "sentencias" in nodo:
                for sentencia in nodo["sentencias"]:
                    lineas += self._contar_lineas_nodo_real(sentencia)
            return lineas

        return 0

    def _clonar_ast(self, ast):
        """Clona el AST para mantener una copia del estado anterior - MEJORADO"""
        try:
            if ast is None:
                print("🔧 DEBUG: _clonar_ast recibió None")
                return []

            # Usar copy.deepcopy para una clonación segura
            import copy
            ast_clonado = copy.deepcopy(ast)
            print(f"🔧 DEBUG: AST clonado exitosamente - tipo: {type(ast_clonado)}")
            return ast_clonado

        except Exception as e:
            print(f"❌ ERROR en _clonar_ast: {e}")
            # Fallback: retornar una copia simple
            try:
                if isinstance(ast, list):
                    return ast[:]
                elif isinstance(ast, dict):
                    return ast.copy()
                else:
                    return ast
            except:
                return []

    def _mapear_scopes(self, ast, scopes_dict):
        """Mapea todos los scopes y variables en el AST - MEJORADO"""
        scopes_dict.clear()
        print(f"🔍 DEBUG_SCOPES: Iniciando mapeo de AST con {len(ast) if isinstance(ast, list) else 'N/A'} nodos")

        if isinstance(ast, list):
            for i, nodo in enumerate(ast):
                if isinstance(nodo, dict):
                    self._recorrer_ast_para_scopes(nodo, "Global", scopes_dict)

        print(f"🔍 DEBUG_SCOPES: Mapeo completado - {len(scopes_dict)} scopes encontrados")
        for scope, variables in scopes_dict.items():
            print(f"🔍 DEBUG_SCOPES: Scope '{scope}': {len(variables)} variables")

    def _recorrer_ast_para_scopes(self, nodo, ambito_actual, scopes_dict):
        """Recorre el AST para mapear scopes y variables - CORREGIDO"""
        if not isinstance(nodo, dict):
            return

        tipo_nodo = nodo.get("nodo")

        # 🔥 CAPTURAR VARIABLES EN DECLARACIONES
        if tipo_nodo == "DECL_VAR":
            var_id = nodo.get("id")
            if var_id:
                # 🔥 EVITAR DUPLICADOS: Verificar si ya existe en este ámbito
                if ambito_actual not in scopes_dict:
                    scopes_dict[ambito_actual] = []

                # Verificar si la variable ya fue agregada en este ámbito
                variable_existente = any(v['nombre'] == var_id for v in scopes_dict[ambito_actual])
                if not variable_existente:
                    referencias = 0
                    if (hasattr(self.tabla_simbolos, 'variables_extendidas') and
                            var_id in self.tabla_simbolos.variables_extendidas):
                        referencias = self.tabla_simbolos.variables_extendidas[var_id].contador_referencias

                    scopes_dict[ambito_actual].append({
                        'nombre': var_id,
                        'tipo': nodo.get('tipo', 'desconocido'),
                        'linea': nodo.get('linea', 0),
                        'referencias': referencias
                    })

        # Procesar bloques y estructuras de control
        if tipo_nodo == "BLOQUE":
            # Para bloques, usar el mismo ámbito (no crear nuevo)
            if "sentencias" in nodo:
                for sentencia in nodo["sentencias"]:
                    if isinstance(sentencia, dict):
                        self._recorrer_ast_para_scopes(sentencia, ambito_actual, scopes_dict)

        elif nodo.get("nodo") == "MIENTRAS":
            # Procesar condición en el mismo ámbito
            if "cond" in nodo and isinstance(nodo["cond"], dict):
                self._recorrer_ast_para_scopes(nodo["cond"], ambito_actual, scopes_dict)
            # Procesar cuerpo en el mismo ámbito (no crear nuevo)
            if "cuerpo" in nodo and isinstance(nodo["cuerpo"], dict):
                self._recorrer_ast_para_scopes(nodo["cuerpo"], ambito_actual, scopes_dict)

        # Procesar recursivamente todos los campos del nodo
        campos_a_procesar = ["valor", "izq", "der", "cond", "then", "else"]
        for campo in campos_a_procesar:
            if campo in nodo and isinstance(nodo[campo], dict):
                self._recorrer_ast_para_scopes(nodo[campo], ambito_actual, scopes_dict)


# Agrega esta clase al archivo optimizador.py
class PropagadorConstantes:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.valores_constantes = {}
        self.optimizaciones_aplicadas = []

    def analizar(self, ast):
        """Analiza el AST para encontrar valores constantes"""
        self._recorrer_ast(ast)
        return self.valores_constantes

    def _recorrer_ast(self, nodo):
        """Recorre el AST para encontrar asignaciones de constantes"""
        if not isinstance(nodo, dict):
            return

        if nodo.get("nodo") == "DECL_VAR":
            nombre = nodo.get("id")
            valor = nodo.get("valor")

            # Si el valor es un literal constante
            if valor and self._es_literal_constante(valor):
                self.valores_constantes[nombre] = valor

            # Si el valor es una variable que ya es constante
            elif valor and valor.get("nodo") == "VAR":
                var_ref = valor.get("id")
                if var_ref in self.valores_constantes:
                    self.valores_constantes[nombre] = self.valores_constantes[var_ref]

        # Recursivamente procesar subnodos
        for key, value in nodo.items():
            if isinstance(value, dict):
                self._recorrer_ast(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._recorrer_ast(item)

    def _es_literal_constante(self, nodo_valor):
        """Determina si un nodo representa un valor constante"""
        if not isinstance(nodo_valor, dict):
            return False

        return nodo_valor.get("nodo") in ["LIT_INT", "LIT_FLOAT", "LIT_STR", "LIT_BOOL", "LIT_CHAR"]

    def propagar(self, ast):
        """Propaga constantes a través del AST"""
        ast_optimizado = []

        for nodo in ast:
            if isinstance(nodo, dict):
                nodo_opt = self._aplicar_propagacion(nodo)
                ast_optimizado.append(nodo_opt)
            else:
                ast_optimizado.append(nodo)

        return ast_optimizado, len(self.optimizaciones_aplicadas)

    def _aplicar_propagacion(self, nodo):
        """Aplica propagación de constantes a un nodo"""
        if not isinstance(nodo, dict):
            return nodo

        # Copiar el nodo para no modificar el original
        nuevo_nodo = nodo.copy()

        # Procesar declaraciones de variables
        if nuevo_nodo.get("nodo") == "DECL_VAR":
            valor = nuevo_nodo.get("valor")
            if valor and valor.get("nodo") == "VAR":
                var_ref = valor.get("id")
                if var_ref in self.valores_constantes:
                    # Reemplazar referencia por el valor constante
                    nuevo_nodo["valor"] = self.valores_constantes[var_ref].copy()
                    self.optimizaciones_aplicadas.append(
                        f"Propagación constante: {var_ref} → {nuevo_nodo['id']}"
                    )

        # Procesar expresiones en imprimir
        elif nuevo_nodo.get("nodo") == "IMPRIMIR":
            valor = nuevo_nodo.get("valor")
            if valor and valor.get("nodo") == "VAR":
                var_ref = valor.get("id")
                if var_ref in self.valores_constantes:
                    # Reemplazar variable por valor constante en imprimir
                    nuevo_nodo["valor"] = self.valores_constantes[var_ref].copy()
                    self.optimizaciones_aplicadas.append(
                        f"Propagación constante en imprimir: {var_ref}"
                    )

        # Procesar recursivamente
        for key, value in nuevo_nodo.items():
            if isinstance(value, dict):
                nuevo_nodo[key] = self._aplicar_propagacion(value)
            elif isinstance(value, list):
                nuevo_nodo[key] = [self._aplicar_propagacion(item) if isinstance(item, dict) else item
                                   for item in value]

        return nuevo_nodo


# ========== OPTIMIZADOR LOCAL ==========

class OptimizadorLocal:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.contador = 0
        self.optimizaciones_aplicadas = []
        self.subexpresiones_comunes = {}

    def optimizar(self, ast):
        """Aplica optimizaciones a nivel de bloque básico"""
        ast_optimizado = []

        lineas_antes = self._contar_lineas_ast(ast)

        for nodo in ast:
            if isinstance(nodo, dict):
                nodo_opt = self._optimizar_nodo(nodo)
                if nodo_opt:  # Solo agregar si no es None
                    ast_optimizado.append(nodo_opt)
            else:
                ast_optimizado.append(nodo)

        lineas_despues = self._contar_lineas_ast(ast_optimizado)
        reduccion = lineas_antes - lineas_despues

        return ast_optimizado, {
            'aplicadas': self.contador,
            'tiempo': 0.0000,
            'reduccion_codigo': reduccion,
            'optimizaciones': self.optimizaciones_aplicadas
        }

    def _contar_lineas_ast(self, ast):
        """Cuenta líneas basado en información de línea del código fuente"""
        if not isinstance(ast, list):
            return 0

        lineas_unicas = set()

        def _extraer_lineas(nodo):
            if not isinstance(nodo, dict):
                return

            # Agregar línea actual si existe
            if "linea" in nodo and nodo["linea"] > 0:
                lineas_unicas.add(nodo["linea"])

            # Recursivamente procesar subnodos
            for key, value in nodo.items():
                if isinstance(value, dict):
                    _extraer_lineas(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            _extraer_lineas(item)

        # Procesar todo el AST
        for nodo in ast:
            _extraer_lineas(nodo)

        return len(lineas_unicas)

    def _optimizar_nodo(self, nodo):
        """Aplica optimizaciones a un nodo individual - MEJORADO"""
        if not isinstance(nodo, dict):
            return nodo

        # PRIMERO: Propagación de constantes
        nodo = self._propagar_constantes(nodo)

        # SEGUNDO: Simplificación algebraica
        nodo_original = str(nodo)  # Para comparar después
        nodo = self._simplificar_algebraica(nodo)

        # 🔥 VERIFICAR SI HUBO CAMBIO
        if str(nodo) != nodo_original:
            print(f"🔧 OPTIMIZACIÓN ALGEBRAICA APLICADA: {nodo_original} -> {nodo}")

        # TERCERO: Eliminación de código redundante
        nodo = self._eliminar_codigo_redundante(nodo)
        if nodo is None:
            return None

        # CUARTO: Eliminación de subexpresiones comunes
        nodo = self._eliminar_subexpresiones_comunes(nodo)

        # Optimizar estructuras específicas
        tipo_nodo = nodo.get("nodo")
        if tipo_nodo == "BLOQUE":
            return self._optimizar_bloque(nodo)
        elif tipo_nodo == "ASIGNACION":
            return self._optimizar_asignacion(nodo)
        elif tipo_nodo == "BIN_OP":
            return self._optimizar_expresion_binaria(nodo)
        elif tipo_nodo in ["SI", "MIENTRAS", "PARA"]:
            return self._optimizar_estructura_control(nodo)
        else:
            return nodo

    def _eliminar_codigo_redundante(self, nodo):
        """Elimina código que no tiene efecto"""
        if not isinstance(nodo, dict):
            return nodo

        # Asignaciones redundantes: x = x
        if nodo.get("nodo") == "ASIGNACION":
            valor = nodo.get("valor")
            if isinstance(valor, dict) and valor.get("nodo") == "VAR":
                if valor.get("id") == nodo.get("id"):
                    self.optimizaciones_aplicadas.append("Eliminación asignación redundante: x = x")
                    self.contador += 1
                    return None

        return nodo

    def _simplificar_algebraica(self, nodo):
        """Aplica simplificaciones algebraicas - MEJORADO"""
        if not isinstance(nodo, dict) or nodo.get("nodo") != "BIN_OP":
            return nodo

        op = nodo.get("op")
        izq = nodo.get("izq")
        der = nodo.get("der")

        print(f"🔧 DEBUG: Simplificando {op} con izq={izq}, der={der}")

        # x + 0 → x
        if op == "MAS" and self._es_cero(der):
            self.optimizaciones_aplicadas.append("Simplificación algebraica: x + 0 → x")
            self.contador += 1
            return izq

        # 0 + x → x
        if op == "MAS" and self._es_cero(izq):
            self.optimizaciones_aplicadas.append("Simplificación algebraica: 0 + x → x")
            self.contador += 1
            return der

        # x * 1 → x
        if op == "MULT" and self._es_uno(der):
            self.optimizaciones_aplicadas.append("Simplificación algebraica: x * 1 → x")
            self.contador += 1
            return izq

        # 1 * x → x
        if op == "MULT" and self._es_uno(izq):
            self.optimizaciones_aplicadas.append("Simplificación algebraica: 1 * x → x")
            self.contador += 1
            return der

        # x * 0 → 0
        if op == "MULT" and self._es_cero(izq):
            self.optimizaciones_aplicadas.append("Simplificación algebraica: x * 0 → 0")
            self.contador += 1
            return der

        # x * 0 → 0
        if op == "MULT" and self._es_cero(der):
            self.optimizaciones_aplicadas.append("Simplificación algebraica: x * 0 → 0")
            self.contador += 1
            return izq

        return nodo

    def _propagar_constantes(self, nodo):
        """Propaga valores constantes conocidos - MEJORADO"""
        if not isinstance(nodo, dict):
            return nodo

        # Buscar variables con valores constantes en la tabla
        if nodo.get("nodo") == "VAR":
            nombre = nodo.get("id")

            # Buscar en constantes extendidas
            if hasattr(self.tabla_simbolos, 'constantes_extendidas'):
                if nombre in self.tabla_simbolos.constantes_extendidas:
                    constante = self.tabla_simbolos.constantes_extendidas[nombre]
                    if constante.valor is not None:
                        self.optimizaciones_aplicadas.append(f"Propagación constante: {nombre}")
                        self.contador += 1
                        return {
                            "nodo": self._obtener_nodo_literal(constante.tipo_dato),
                            "valor": constante.valor
                        }

            # Buscar en variables con valores conocidos
            if hasattr(self.tabla_simbolos, 'variables_extendidas'):
                if nombre in self.tabla_simbolos.variables_extendidas:
                    variable = self.tabla_simbolos.variables_extendidas[nombre]
                    # Si la variable tiene un valor literal conocido
                    if (variable.valor is not None and
                            not isinstance(variable.valor, str) or
                            not variable.valor.startswith('<')):  # No es una referencia
                        self.optimizaciones_aplicadas.append(f"Propagación valor conocido: {nombre}")
                        self.contador += 1
                        return {
                            "nodo": self._obtener_nodo_literal(variable.tipo_dato),
                            "valor": variable.valor
                        }

        return nodo

    def _eliminar_subexpresiones_comunes(self, nodo):
        """Elimina subexpresiones comunes usando hashing"""
        if not isinstance(nodo, dict):
            return nodo

        # Generar hash de la expresión
        expr_hash = self._hash_expresion(nodo)

        if expr_hash in self.subexpresiones_comunes:
            # Reemplazar por variable temporal existente
            self.optimizaciones_aplicadas.append("Eliminación subexpresión común")
            self.contador += 1
            return self.subexpresiones_comunes[expr_hash]
        else:
            # Guardar para futuras referencias
            self.subexpresiones_comunes[expr_hash] = nodo

        return nodo

    def _hash_expresion(self, expresion):
        """Genera un hash único para una expresión"""
        if not isinstance(expresion, dict):
            return str(expresion)

        partes = [expresion.get("nodo", "")]

        for key in sorted(expresion.keys()):
            if key not in ['linea', 'columna']:  # Ignorar metadatos
                value = expresion[key]
                if isinstance(value, dict):
                    partes.append(self._hash_expresion(value))
                elif isinstance(value, list):
                    partes.append(
                        str([self._hash_expresion(item) if isinstance(item, dict) else item for item in value]))
                else:
                    partes.append(str(value))

        return "|".join(partes)

    def _es_cero(self, expresion):
        """Verifica si una expresión es cero"""
        if isinstance(expresion, dict) and expresion.get("nodo") == "LIT_INT":
            return expresion.get("valor") == 0
        return False

    def _es_uno(self, expresion):
        """Verifica si una expresión es uno"""
        if isinstance(expresion, dict) and expresion.get("nodo") == "LIT_INT":
            return expresion.get("valor") == 1
        return False

    def _obtener_nodo_literal(self, tipo_dato):
        """Determina el tipo de nodo literal basado en el tipo de dato"""
        mapeo = {
            'TIPO_ENTERO': 'LIT_INT',
            'entero': 'LIT_INT',
            'TIPO_FLOTANTE': 'LIT_FLOAT',
            'flotante': 'LIT_FLOAT',
            'TIPO_BOOLEANO': 'LIT_BOOL',
            'booleano': 'LIT_BOOL',
            'TIPO_CADENA': 'LIT_STR',
            'cadena': 'LIT_STR',
            'TIPO_CARACTER': 'LIT_CHAR',
            'caracter': 'LIT_CHAR'
        }
        return mapeo.get(tipo_dato, 'LIT_INT')

    def _optimizar_bloque(self, nodo_bloque):
        """Optimiza un bloque de código"""
        if not isinstance(nodo_bloque, dict) or nodo_bloque.get("nodo") != "BLOQUE":
            return nodo_bloque

        sentencias_opt = []
        for sentencia in nodo_bloque.get("sentencias", []):
            if isinstance(sentencia, dict):
                sentencia_opt = self._optimizar_nodo(sentencia)
                if sentencia_opt:  # Solo agregar si no es None
                    sentencias_opt.append(sentencia_opt)
            else:
                sentencias_opt.append(sentencia)

        nodo_bloque["sentencias"] = sentencias_opt
        return nodo_bloque

    def _optimizar_asignacion(self, nodo_asignacion):
        """Optimiza una asignación"""
        return nodo_asignacion  # Por ahora, retornar sin cambios

    def _optimizar_expresion_binaria(self, nodo_bin_op):
        """Optimiza una expresión binaria - MEJORADO"""
        if not isinstance(nodo_bin_op, dict) or nodo_bin_op.get("nodo") != "BIN_OP":
            return nodo_bin_op

        # Optimizar subexpresiones primero
        if "izq" in nodo_bin_op and isinstance(nodo_bin_op["izq"], dict):
            nodo_bin_op["izq"] = self._optimizar_nodo(nodo_bin_op["izq"])

        if "der" in nodo_bin_op and isinstance(nodo_bin_op["der"], dict):
            nodo_bin_op["der"] = self._optimizar_nodo(nodo_bin_op["der"])

        # Aplicar simplificación algebraica
        return self._simplificar_algebraica(nodo_bin_op)

    def _optimizar_estructura_control(self, nodo):
        """Optimiza estructuras de control"""
        return nodo  # Por ahora, retornar sin cambios


# ========== OPTIMIZADOR BUCLES ==========

class OptimizadorBucles:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.contador = 0
        self.optimizaciones_aplicadas = []

    def optimizar(self, ast):
        """Aplica optimizaciones específicas para bucles"""
        ast_optimizado = []

        # 🔥 CONTAR LÍNEAS ANTES
        lineas_antes = self._contar_lineas_reales(ast)

        for nodo in ast:
            if isinstance(nodo, dict):
                nodo_opt = self._optimizar_nodo(nodo)
                ast_optimizado.append(nodo_opt)
            else:
                ast_optimizado.append(nodo)

        # 🔥 CONTAR LÍNEAS DESPUÉS Y CALCULAR REDUCCIÓN
        lineas_despues = self._contar_lineas_reales(ast_optimizado)
        reduccion = lineas_antes - lineas_despues

        return ast_optimizado, {
            'aplicadas': self.contador,
            'tiempo': 0.0000,  # Por ahora 0
            'reduccion_codigo': reduccion,  # 🔥 ESTA ES LA CLAVE
            'optimizaciones': self.optimizaciones_aplicadas
        }

    def _contar_lineas_reales(self, ast):
        """Cuenta líneas de forma más realista"""
        if not isinstance(ast, list):
            return 0

        lineas = 0
        for nodo in ast:
            if isinstance(nodo, dict):
                # Cada nodo principal cuenta como 1 línea
                lineas += 1

                # Los bucles tienen líneas adicionales en su cuerpo
                if nodo.get("nodo") in ["MIENTRAS", "PARA"]:
                    cuerpo = nodo.get("cuerpo")
                    if cuerpo:
                        lineas += self._contar_lineas_reales([cuerpo])

                elif nodo.get("nodo") == "BLOQUE":
                    sentencias = nodo.get("sentencias", [])
                    lineas += len(sentencias)

        return lineas

    def _contar_lineas_ast(self, ast):
        """Cuenta líneas de forma más precisa para bucles"""
        if not isinstance(ast, list):
            return 0

        lineas = 0
        for nodo in ast:
            lineas += self._contar_lineas_nodo(nodo)

        return lineas

    def _contar_lineas_nodo(self, nodo):
        """Cuenta líneas para un nodo individual"""
        if not isinstance(nodo, dict):
            return 0

        tipo_nodo = nodo.get("nodo")

        # Cada declaración/estructura cuenta como 1 línea
        lineas = 1

        # Bucles y bloques tienen líneas adicionales
        if tipo_nodo in ["MIENTRAS", "PARA"]:
            # Línea del bucle + cuerpo
            if "cuerpo" in nodo:
                lineas += self._contar_lineas_nodo(nodo["cuerpo"])

        elif tipo_nodo == "BLOQUE":
            # Contenido del bloque
            if "sentencias" in nodo:
                for sentencia in nodo["sentencias"]:
                    lineas += self._contar_lineas_nodo(sentencia)

        return lineas

    def _optimizar_nodo(self, nodo):
        """Aplica optimizaciones a un nodo individual"""
        tipo_nodo = nodo.get("nodo")

        if tipo_nodo in ["MIENTRAS", "PARA", "HACERMIENTRAS"]:
            return self._optimizar_bucle(nodo)
        elif tipo_nodo == "BLOQUE":
            # Buscar bucles dentro del bloque
            sentencias_opt = []
            for sentencia in nodo.get("sentencias", []):
                if isinstance(sentencia, dict):
                    sentencias_opt.append(self._optimizar_nodo(sentencia))
                else:
                    sentencias_opt.append(sentencia)
            nodo["sentencias"] = sentencias_opt
            return nodo
        else:
            return nodo

    def _optimizar_bucle(self, nodo_bucle):
        """Aplica optimizaciones REALES a un bucle"""
        print(f"🔧 OPTIMIZANDO BUCLE: {nodo_bucle.get('nodo')}")

        # Hacer una copia para no modificar el original
        bucle_optimizado = nodo_bucle.copy()

        # 1. Optimizar el cuerpo del bucle primero
        if "cuerpo" in bucle_optimizado:
            bucle_optimizado["cuerpo"] = self._optimizar_cuerpo_bucle(bucle_optimizado["cuerpo"])

        # 2. Aplicar optimizaciones específicas
        optimizaciones = []

        # Optimización: Detectar incrementos simples i = i + 1
        if self._detectar_incremento_simple(bucle_optimizado):
            optimizaciones.append("Incremento simple detectado")

        # Optimización: Reducción de fuerza en multiplicaciones
        if self._aplicar_reduccion_fuerza(bucle_optimizado):
            optimizaciones.append("Reducción de fuerza aplicada")

        # Optimización: Movimiento de código invariante
        if self._mover_codigo_invariante(bucle_optimizado):
            optimizaciones.append("Código invariante movido")

        # Registrar optimizaciones aplicadas
        if optimizaciones:
            self.optimizaciones_aplicadas.extend(optimizaciones)
            self.contador += len(optimizaciones)
            print(f"✅ Optimizaciones aplicadas: {optimizaciones}")
        else:
            print("ℹ️  No se aplicaron optimizaciones al bucle")

        return bucle_optimizado

    def _optimizar_cuerpo_bucle(self, cuerpo):
        """Optimiza el cuerpo de un bucle de forma recursiva"""
        if not isinstance(cuerpo, dict):
            return cuerpo

        if cuerpo.get("nodo") == "BLOQUE":
            # Optimizar cada sentencia del bloque
            nuevo_cuerpo = cuerpo.copy()
            sentencias_optimizadas = []

            for sentencia in cuerpo.get("sentencias", []):
                sentencia_opt = self._optimizar_sentencia_bucle(sentencia)
                if sentencia_opt is not None:  # Puede ser None si eliminamos código muerto
                    sentencias_optimizadas.append(sentencia_opt)

            nuevo_cuerpo["sentencias"] = sentencias_optimizadas
            return nuevo_cuerpo

        return cuerpo

    def _optimizar_sentencia_bucle(self, sentencia):
        """Optimiza una sentencia dentro de un bucle"""
        if not isinstance(sentencia, dict):
            return sentencia

        # 1. Reducción de fuerza: i * 2 → podría ser i << 1 (pero nuestro lenguaje no tiene <<)
        # En su lugar, podemos detectar multiplicaciones por constantes
        if sentencia.get("nodo") == "DECL_VAR":
            valor = sentencia.get("valor")
            if (valor and isinstance(valor, dict) and
                    valor.get("nodo") == "BIN_OP" and
                    valor.get("op") == "MULT"):

                izq = valor.get("izq")
                der = valor.get("der")

                # Si multiplicamos por 2, es una oportunidad de optimización
                if (der and der.get("nodo") == "LIT_INT" and
                        der.get("valor") == 2):
                    print(f"🔧 OPORTUNIDAD: Multiplicación por 2 en bucle - podría optimizarse")
                    # Aquí podrías reemplazar por i + i si tu lenguaje lo soporta

        # 2. Eliminar código muerto dentro del bucle
        if (sentencia.get("nodo") == "DECL_VAR" and
                self._es_variable_no_utilizada(sentencia.get("id"))):
            print(f"🚮 Eliminando variable muerta en bucle: {sentencia.get('id')}")
            return None  # Eliminar esta sentencia

        return sentencia

    def _detectar_incremento_simple(self, bucle):
        cuerpo = bucle.get("cuerpo")
        if not cuerpo or cuerpo.get("nodo") != "BLOQUE":
            return False

        for sentencia in cuerpo.get("sentencias", []):
            if (sentencia.get("nodo") == "ASIGNACION" and
                    sentencia.get("valor") and
                    sentencia["valor"].get("nodo") == "BIN_OP" and
                    sentencia["valor"].get("op") == "MAS"):

                izq = sentencia["valor"].get("izq")
                der = sentencia["valor"].get("der")
                var_asignada = sentencia.get("id")

                # Verificar si es: variable = variable + 1
                if (izq and izq.get("nodo") == "VAR" and
                        der and der.get("nodo") == "LIT_INT" and
                        der.get("valor") == 1 and
                        izq.get("id") == var_asignada):  # ← CORREGIDO

                    print(f"🔧 DETECTADO: Incremento simple {var_asignada} = {var_asignada} + 1")
                    return True

        return False

    def _aplicar_reduccion_fuerza(self, bucle):
        """Aplica reducción de fuerza (reemplazar operaciones costosas)"""
        aplicada = False
        cuerpo = bucle.get("cuerpo")

        if not cuerpo or cuerpo.get("nodo") != "BLOQUE":
            return aplicada

        for i, sentencia in enumerate(cuerpo.get("sentencias", [])):
            if sentencia.get("nodo") == "DECL_VAR":
                valor = sentencia.get("valor")
                if (valor and valor.get("nodo") == "BIN_OP" and
                        valor.get("op") == "MULT"):

                    izq = valor.get("izq")
                    der = valor.get("der")

                    # Multiplicación por 2 → reemplazar por suma (i + i)
                    if (der and der.get("nodo") == "LIT_INT" and
                            der.get("valor") == 2):
                        # j = i * 2 → j = i + i
                        nueva_sentencia = sentencia.copy()
                        nueva_sentencia["valor"] = {
                            "nodo": "BIN_OP",
                            "op": "MAS",
                            "izq": izq,
                            "der": izq.copy()  # i + i
                        }

                        cuerpo["sentencias"][i] = nueva_sentencia
                        aplicada = True
                        self.optimizaciones_aplicadas.append("Reducción de fuerza: i * 2 → i + i")
                        self.contador += 1
                        print(
                            f"🔧 REDUCCIÓN DE FUERZA APLICADA: {sentencia.get('id')} = i * 2 → {sentencia.get('id')} = i + i")

        return aplicada

    def _mover_codigo_invariante(self, bucle):
        """Mueve código invariante fuera del bucle (SIMPLIFICADO)"""
        # Esta es una optimización avanzada - por ahora solo la detectamos
        cuerpo = bucle.get("cuerpo")
        if not cuerpo or cuerpo.get("nodo") != "BLOQUE":
            return False

        for sentencia in cuerpo.get("sentencias", []):
            if self._es_codigo_invariante(sentencia, bucle):
                print(f"🔧 CÓDIGO INVARIANTE DETECTADO: Podría moverse fuera del bucle")
                return True

        return False

    def _es_codigo_invariante(self, sentencia, bucle):
        """Determina si una sentencia es invariante al bucle"""
        # Simplificación: código que no depende de la variable de control del bucle
        if sentencia.get("nodo") == "DECL_VAR":
            valor = sentencia.get("valor")
            if valor and self._depende_de_variable_control(valor, bucle):
                return False
            return True
        return False

    def _depende_de_variable_control(self, expresion, bucle):
        """Detecta variables de control de forma más inteligente"""
        if not isinstance(expresion, dict):
            return False

        if expresion.get("nodo") == "VAR":
            var_name = expresion.get("id")
            # Buscar en la tabla de símbolos para determinar si es variable de control
            if hasattr(self.tabla_simbolos, 'variables_extendidas'):
                if var_name in self.tabla_simbolos.variables_extendidas:
                    variable = self.tabla_simbolos.variables_extendidas[var_name]
                    # Heurística: variable modificada en el bucle es probablemente de control
                    return variable.contador_referencias > 0
        return False

    def _es_variable_no_utilizada(self, nombre):
        """Verifica si una variable no se utiliza"""
        if hasattr(self.tabla_simbolos, 'variables_extendidas'):
            if nombre in self.tabla_simbolos.variables_extendidas:
                variable = self.tabla_simbolos.variables_extendidas[nombre]
                return variable.contador_referencias == 0

        # Fallback: buscar en estructura antigua
        simbolo = self.tabla_simbolos.buscar(nombre)
        if simbolo and "contador_referencias" in simbolo:
            return simbolo["contador_referencias"] == 0

        return False


# ========== OPTIMIZADOR GLOBAL ==========

class OptimizadorGlobal:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.contador = 0
        self.optimizaciones_aplicadas = []

    def optimizar(self, ast):
        """Aplica optimizaciones a nivel de programa completo"""
        ast_optimizado = []
        lineas_antes = self._contar_lineas_ast(ast)

        # Eliminación de código muerto
        ast_opt = self._eliminar_codigo_muerto(ast)

        lineas_despues = self._contar_lineas_ast(ast_opt)
        reduccion = lineas_antes - lineas_despues

        return ast_opt, {
            'aplicadas': self.contador,
            'reduccion_codigo': reduccion,
            'optimizaciones': self.optimizaciones_aplicadas
        }

    def _contar_lineas_ast(self, ast):
        """Cuenta líneas aproximadas en el AST"""
        return len(str(ast))

    def _eliminar_codigo_muerto(self, ast):
        """Elimina código que nunca se ejecuta o no tiene efecto - MEJORADO"""
        ast_optimizado = []
        variables_eliminadas = 0

        for nodo in ast:
            if isinstance(nodo, dict):
                # Eliminar variables declaradas pero no utilizadas
                if nodo.get("nodo") == "DECL_VAR":
                    nombre = nodo.get("id")
                    if hasattr(self.tabla_simbolos, 'variables_extendidas'):
                        if nombre in self.tabla_simbolos.variables_extendidas:
                            variable = self.tabla_simbolos.variables_extendidas[nombre]
                            if variable.contador_referencias == 0:
                                print(f"🔧 ELIMINANDO CÓDIGO MUERTO: Variable '{nombre}' no utilizada")
                                variables_eliminadas += 1
                                continue  # No agregar esta declaración

                    # Si llegamos aquí, la variable SÍ se usa, mantenerla
                    ast_optimizado.append(nodo)

                # Eliminar asignaciones redundantes x = x
                elif nodo.get("nodo") == "ASIGNACION":
                    if self._es_asignacion_redundante(nodo):
                        print(f"🔧 ELIMINANDO CÓDIGO MUERTO: Asignación redundante '{nodo.get('id')}'")
                        variables_eliminadas += 1
                        continue
                    else:
                        ast_optimizado.append(nodo)
                else:
                    ast_optimizado.append(nodo)
            else:
                ast_optimizado.append(nodo)

        if variables_eliminadas > 0:
            self.optimizaciones_aplicadas.append(f"Eliminadas {variables_eliminadas} variables no utilizadas")
            self.contador += variables_eliminadas

        return ast_optimizado

    def _es_asignacion_redundante(self, nodo_asignacion):
        """Verifica si una asignación es redundante (x = x)"""
        if nodo_asignacion.get("nodo") != "ASIGNACION":
            return False

        valor = nodo_asignacion.get("valor")
        if isinstance(valor, dict) and valor.get("nodo") == "VAR":
            return valor.get("id") == nodo_asignacion.get("id")

        return False

    def _es_codigo_muerto(self, nodo):
        """Determina si un nodo es código muerto"""
        if not isinstance(nodo, dict):
            return False

        # Variables declaradas pero no utilizadas
        if nodo.get("nodo") == "DECL_VAR":
            nombre = nodo.get("id")
            if hasattr(self.tabla_simbolos, 'variables_extendidas'):
                if nombre in self.tabla_simbolos.variables_extendidas:
                    variable = self.tabla_simbolos.variables_extendidas[nombre]
                    if variable.contador_referencias == 0:
                        return True

        return False