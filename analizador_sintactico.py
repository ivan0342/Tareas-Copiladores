# archivo: analizador_sintactico.py
from parser import Parser, ParserError
from interprete import Interprete, RuntimeErrorInterp
from analizador_semantico import AnalizadorSemantico
from verificaciones.clasificacion_errores import ReporteErrores

class AnalizadorSintactico:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.reporte_errores = ReporteErrores()

    def analizar(self, tokens):
        print("TOKENS RECIBIDOS POR EL PARSER:")
        for t in tokens:
            print(t)

        errores = []
        self.reporte_errores.limpiar()
        print(f"DEBUG: ID de tabla_simbolos en sintactico: {id(self.tabla_simbolos)}")

        # ✅ CORRECCIÓN CRÍTICA: Guardar referencia a la tabla actual para usar después
        tabla_original = self.tabla_simbolos

        # Asegurar EOF al final
        if not tokens or tokens[-1].get("tipo") != "EOF":
            tokens = tokens[:]
            tokens.append({"token": "EOF", "tipo": "EOF", "linea": -1, "columna": -1})

        # 1) Parseo -> AST (esto pobla la tabla de símbolos)
        ast = None
        parser = None
        try:
            # ✅ USAR LA MISMA INSTANCIA de tabla_simbolos
            parser = Parser(tokens, tabla_original, self.reporte_errores)
            ast = parser.parse()
            errores.extend(parser.errores)
        except ParserError as e:
            errores.append(f"Error de parser: {e}")
            return errores

        print(f"DEBUG: AST generado con {len(ast)} nodos")

        # 🔥 VERIFICAR QUE LA TABLA SIGUE SIENDO LA MISMA
        print(f"DEBUG: ID de tabla después del parsing: {id(self.tabla_simbolos)}")
        print(f"DEBUG: ¿Misma instancia? {self.tabla_simbolos is tabla_original}")

        # 🔥 CORRECCIÓN CRÍTICA: Verificar estado REAL de la tabla DESPUÉS del parsing
        print("DEBUG: ========== ESTADO DE LA TABLA DESPUÉS DEL PARSING ==========")

        # Mostrar estructura antigua
        simbolos_antiguos = self.tabla_simbolos.obtener_todos()
        print(f"DEBUG: Símbolos en estructura antigua: {len(simbolos_antiguos)}")
        for i, simbolo in enumerate(simbolos_antiguos):
            print(f"  {i}: {simbolo.get('identificador', 'N/A')} - {simbolo.get('tipo_dato', 'N/A')}")

        # Mostrar estructura extendida
        if hasattr(self.tabla_simbolos, 'variables_extendidas'):
            print(f"DEBUG: Variables en estructura extendida: {len(self.tabla_simbolos.variables_extendidas)}")
            for nombre, variable in self.tabla_simbolos.variables_extendidas.items():
                print(
                    f"  {nombre}: {variable.tipo_dato} - refs: {variable.contador_referencias} - valor: {variable.valor}")
        else:
            print("DEBUG: ❌ NO existe estructura variables_extendidas")

        if hasattr(self.tabla_simbolos, 'constantes_extendidas'):
            print(f"DEBUG: Constantes en estructura extendida: {len(self.tabla_simbolos.constantes_extendidas)}")
            for nombre, constante in self.tabla_simbolos.constantes_extendidas.items():
                print(f"  {nombre}: {constante.tipo_dato} - refs: {constante.contador_referencias}")

        # 2) Poblar la tabla de símbolos (VERSIÓN SIMPLIFICADA) - PRIMERO
        try:
            self._actualizar_tabla_desde_ast_simple(ast)
            print("DEBUG: Tabla de símbolos actualizada desde AST")
        except Exception as e:
            errores.append(f"Error al actualizar tabla de símbolos: {e}")

        # 🔥 DECISIÓN: Ejecutar análisis semántico SOLO si hay variables en la tabla extendida
        tiene_variables_extendidas = (hasattr(self.tabla_simbolos, 'variables_extendidas') and
                                      len(self.tabla_simbolos.variables_extendidas) > 0)

        if tiene_variables_extendidas:
            print("DEBUG: ✅ Ejecutando análisis semántico (hay variables en tabla extendida)")
            try:
                analizador_semantico = AnalizadorSemantico(self.tabla_simbolos, self.reporte_errores)
                errores_semanticos = analizador_semantico.analizar(ast)

                if errores_semanticos:
                    print("DEBUG: Se encontraron errores semánticos:")
                    for error_sem in errores_semanticos:
                        print(f"  - {error_sem}")
                        errores.append(f"SEMÁNTICO: {error_sem}")
                else:
                    print("DEBUG: ✅ Análisis semántico completado sin errores")
            except Exception as e:
                print(f"DEBUG: ❌ Error durante análisis semántico: {e}")
        else:
            print("DEBUG: ⚠️ Saltando análisis semántico - NO hay variables en tabla extendida")

        # 4) Mostrar contenido de la tabla para debug DESPUÉS del análisis semántico
        print("DEBUG: ========== ESTADO FINAL DE LA TABLA ==========")

        # Mostrar estructura extendida FINAL
        if hasattr(self.tabla_simbolos, 'variables_extendidas'):
            print(f"DEBUG: Variables extendidas FINALES: {len(self.tabla_simbolos.variables_extendidas)}")
            for nombre, variable in self.tabla_simbolos.variables_extendidas.items():
                print(f"  {nombre}: {variable.tipo_dato} - refs: {variable.contador_referencias}")

        # 5) Ejecutar AST con intérprete (SIEMPRE ejecutar, sin importar errores semánticos)
        salida_lines = []

        def output_callback(valor):
            salida_lines.append(str(valor))

        interp = Interprete(output=output_callback, tabla_simbolos=self.tabla_simbolos)

        # CORRECCIÓN: REGISTRAR FUNCIONES PRIMERO
        print("DEBUG: Registrando funciones en el intérprete...")
        funciones_registradas = 0
        for nodo in ast:
            if isinstance(nodo, dict) and nodo.get("nodo") == "FUNCION":
                nombre = nodo["nombre"]
                interp.funciones[nombre] = nodo
                funciones_registradas += 1
                print(f"DEBUG: Función '{nombre}' registrada en intérprete")

        print(f"DEBUG: Total funciones registradas: {funciones_registradas}")
        print(f"DEBUG: Funciones disponibles: {list(interp.funciones.keys())}")

        try:
            # Ejecutar solo sentencias globales
            print("DEBUG: Ejecutando código con intérprete...")
            for nodo in ast:
                if isinstance(nodo, dict) and nodo.get("nodo") not in ["FUNCION", "CLASE", "INTERFAZ"]:
                    print(f"DEBUG: Ejecutando nodo: {nodo.get('nodo')}")
                    interp.ejecutar(nodo)

        except RuntimeErrorInterp as re:
            errores.append(f"Error en tiempo de ejecución: {re}")
        except Exception as ex:
            errores.append(f"Error inesperado en intérprete: {ex}")

        if salida_lines:
            errores.append("SALIDA_INTERPRETE:")
            errores.extend(salida_lines)

        print("DEBUG: ========== RESUMEN DE ERRORES ==========")
        for i in self.reporte_errores.errores:
            print(f"error: {i}")

        return errores

    def _actualizar_tabla_desde_ast_simple(self, ast):
        for nodo in ast:
            if not isinstance(nodo, dict):
                continue

            tipo_n = nodo.get("nodo")

    def _valor_literal_de_nodo_simple(self, nodo_val):
        """
        Extrae valor literal de un nodo AST de manera segura (versión simple)
        """
        if nodo_val is None:
            return None

        if isinstance(nodo_val, dict):
            n = nodo_val.get("nodo")
            if n in ["LIT_INT", "LIT_FLOAT", "LIT_STR", "LIT_BOOL", "LIT_CHAR"]:
                return nodo_val.get("valor")
            elif n == "VAR":
                return f"<ref:{nodo_val.get('id')}>"
            else:
                # Para expresiones complejas, devolver representación
                return f"<expr:{n}>"

        # Si es un valor primitivo directamente
        return nodo_val