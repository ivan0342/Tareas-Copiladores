# optimizador.py - VERSIÓN CONSOLIDADA
import json
import time
from datetime import datetime


class OptimizadorMultinivel:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.optimizaciones_aplicadas = []
        self.metricas = {
            'local': {'aplicadas': 0, 'tiempo': 0, 'reduccion_codigo': 0},
            'bucles': {'aplicadas': 0, 'tiempo': 0, 'reduccion_codigo': 0},
            'global': {'aplicadas': 0, 'tiempo': 0, 'reduccion_codigo': 0}
        }
        self.ast_antes = None
        self.ast_despues = None
        self.scopes_antes = {}
        self.scopes_despues = {}

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
        print("📊 Aplicando propagación de constantes...")
        inicio_constantes = time.time()
        propagador = PropagadorConstantes(self.tabla_simbolos)
        constantes_encontradas = propagador.analizar(ast)
        ast_propagado, num_propagaciones = propagador.propagar(ast)
        self.optimizaciones_aplicadas.extend(propagador.optimizaciones_aplicadas)

        metricas_constantes = {
            'aplicadas': num_propagaciones,
            'tiempo': time.time() - inicio_constantes,
            'reduccion_codigo': 0  # Se calculará después
        }

        # Fase 1: Optimización Local (ahora con el AST propagado)
        ast_opt, metricas_local = self.optimizacion_local(ast_propagado)
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

        self._generar_reporte_completo()
        return ast_opt

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
        """Mapea todos los scopes y variables en el AST"""
        scopes_dict.clear()
        self._recorrer_ast_para_scopes(ast, "Global", scopes_dict)

    def _recorrer_ast_para_scopes(self, nodo, ambito_actual, scopes_dict):
        """Recorre el AST para mapear scopes y variables"""
        if not isinstance(nodo, dict):
            return

        # Mapear declaraciones de variables
        if nodo.get("nodo") == "DECL_VAR":
            var_id = nodo.get("id")
            if ambito_actual not in scopes_dict:
                scopes_dict[ambito_actual] = []

            # Contar referencias desde la tabla de símbolos
            referencias = 0
            if hasattr(self.tabla_simbolos, 'variables_extendidas'):
                if var_id in self.tabla_simbolos.variables_extendidas:
                    referencias = self.tabla_simbolos.variables_extendidas[var_id].contador_referencias

            scopes_dict[ambito_actual].append({
                'nombre': var_id,
                'tipo': nodo.get('tipo'),
                'linea': nodo.get('linea'),
                'referencias': referencias
            })

        # Seguir recorriendo el AST
        for key, value in nodo.items():
            if isinstance(value, dict):
                nuevo_ambito = ambito_actual
                if key == "cuerpo" and nodo.get("nodo") == "FUNCION":
                    nuevo_ambito = f"funcion:{nodo.get('nombre')}"
                elif key == "cuerpo" and nodo.get("nodo") == "CLASE":
                    nuevo_ambito = f"clase:{nodo.get('nombre')}"

                self._recorrer_ast_para_scopes(value, nuevo_ambito, scopes_dict)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._recorrer_ast_para_scopes(item, ambito_actual, scopes_dict)

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
            'reduccion_codigo': reduccion,
            'optimizaciones': self.optimizaciones_aplicadas
        }

    def _contar_lineas_ast(self, ast):
        """Cuenta líneas aproximadas en el AST"""
        return len(str(ast))

    def _optimizar_nodo(self, nodo):
        """Aplica optimizaciones a un nodo individual"""
        if not isinstance(nodo, dict):
            return nodo

        # PRIMERO: Propagación de constantes
        nodo = self._propagar_constantes(nodo)

        # Eliminación de código redundante
        nodo = self._eliminar_codigo_redundante(nodo)
        if nodo is None:
            return None

        # Simplificación algebraica
        nodo = self._simplificar_algebraica(nodo)

        # Eliminación de subexpresiones comunes
        nodo = self._eliminar_subexpresiones_comunes(nodo)

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
        """Aplica simplificaciones algebraicas"""
        if not isinstance(nodo, dict) or nodo.get("nodo") != "BIN_OP":
            return nodo

        op = nodo.get("op")
        izq = nodo.get("izq")
        der = nodo.get("der")

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
        if op == "MULT" and (self._es_cero(izq) or self._es_cero(der)):
            self.optimizaciones_aplicadas.append("Simplificación algebraica: x * 0 → 0")
            self.contador += 1
            return {"nodo": "LIT_INT", "valor": 0}

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
        """Optimiza una expresión binaria"""
        return nodo_bin_op  # Ya se maneja en _simplificar_algebraica

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
        lineas_antes = self._contar_lineas_ast(ast)

        for nodo in ast:
            if isinstance(nodo, dict):
                nodo_opt = self._optimizar_nodo(nodo)
                ast_optimizado.append(nodo_opt)
            else:
                ast_optimizado.append(nodo)

        lineas_despues = self._contar_lineas_ast(ast_optimizado)
        reduccion = lineas_antes - lineas_despues

        return ast_optimizado, {
            'aplicadas': self.contador,
            'reduccion_codigo': reduccion,
            'optimizaciones': self.optimizaciones_aplicadas
        }

    def _contar_lineas_ast(self, ast):
        """Cuenta líneas aproximadas en el AST"""
        return len(str(ast))

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
        """Aplica optimizaciones a un bucle"""
        # Por ahora, solo registrar que encontramos un bucle
        self.optimizaciones_aplicadas.append(f"Bucle {nodo_bucle.get('nodo')} identificado")
        self.contador += 1
        return nodo_bucle


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
        """Elimina código que nunca se ejecuta o no tiene efecto"""
        ast_optimizado = []

        for nodo in ast:
            if isinstance(nodo, dict):
                if not self._es_codigo_muerto(nodo):
                    ast_optimizado.append(nodo)
                else:
                    self.optimizaciones_aplicadas.append("Eliminación de código muerto")
                    self.contador += 1
            else:
                ast_optimizado.append(nodo)

        return ast_optimizado

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