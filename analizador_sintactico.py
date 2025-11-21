# archivo: analizador_sintactico.py
from parser import Parser, ParserError
from interprete import Interprete, RuntimeErrorInterp
from analizador_semantico import AnalizadorSemantico


class AnalizadorSintactico:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos

    def analizar(self, tokens):
        print("TOKENS RECIBIDOS POR EL PARSER:")
        for t in tokens:
            print(t)

        errores = []

        print(f"DEBUG: ID de tabla_simbolos en sintactico: {id(self.tabla_simbolos)}")

        # Asegurar EOF al final
        if not tokens or tokens[-1].get("tipo") != "EOF":
            tokens = tokens[:]
            tokens.append({"token": "EOF", "tipo": "EOF", "linea": -1, "columna": -1})

        # 1) Parseo -> AST
        try:
            parser = Parser(tokens, self.tabla_simbolos)
            ast = parser.parse()
            errores.extend(parser.errores)
        except ParserError as e:
            errores.append(f"Error de parser: {e}")
            return errores

        print(f"DEBUG: AST generado con {len(ast)} nodos")

        # 2) Poblar la tabla de símbolos (VERSIÓN SIMPLIFICADA) - PRIMERO
        try:
            self._actualizar_tabla_desde_ast_simple(ast)
            print("DEBUG: Tabla de símbolos actualizada desde AST")
        except Exception as e:
            errores.append(f"Error al actualizar tabla de símbolos: {e}")

        # 3) Análisis Semántico - DESACTIVADO TEMPORALMENTE

        try:
            analizador_semantico = AnalizadorSemantico(self.tabla_simbolos)
            errores_semanticos = analizador_semantico.analizar(ast)

            if errores_semanticos:
                print("DEBUG: Se encontraron errores semánticos:")
                for error_sem in errores_semanticos:
                    print(f"  - {error_sem}")
                    errores.append(f"SEMÁNTICO: {error_sem}")
        except Exception as e:
            print(f"DEBUG: Error durante análisis semántico: {e}")
            # errores.append(f"Error en análisis semántico: {e}")  # Comentado temporalmente


        # 4) Mostrar contenido de la tabla para debug
        print("DEBUG: Contenido de la tabla de símbolos:")
        simbolos = self.tabla_simbolos.obtener_todos()
        for i, simbolo in enumerate(simbolos):
            print(f"  {i}: {simbolo}")

        if not simbolos:
            print("  (vacía)")

        # 5) Ejecutar AST con intérprete
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

        print(f" DEBUG: Total funciones registradas: {funciones_registradas}")
        print(f" DEBUG: Funciones disponibles: {list(interp.funciones.keys())}")

        try:
            # Ejecutar solo sentencias globales
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

        return errores

    def _actualizar_tabla_desde_ast_simple(self, ast):
        for nodo in ast:
            if not isinstance(nodo, dict):
                continue

            tipo_n = nodo.get("nodo")

            """
            # Solo procesar declaraciones de variables globales
            if tipo_n == "DECL_VAR":
                ident = nodo.get("id")
                tipo_dato_token = nodo.get("tipo")

                # Verificar si ya existe
                if not self.tabla_simbolos.buscar(ident):
                    simbolo = {
                        "identificador": ident,
                        "categoria": "variable",
                        "tipo_dato": tipo_dato_token,
                        "ambito": "Global",
                        "direccion": self.tabla_simbolos.obtener_direccion(),
                        "linea": nodo.get("linea", -1),
                        "valor": self._valor_literal_de_nodo_simple(nodo.get("valor")),
                        "estado": "declarado" if nodo.get("valor") is None else "inicializado",
                        "estructura": None,
                        "contador_referencias": 1
                    }
                    self.tabla_simbolos.insertar(simbolo)
                    print(f"DEBUG: Insertada variable global: {ident}")

            # También procesar asignaciones globales
            elif tipo_n == "ASIGNACION":
                ident = nodo.get("id")
                if not self.tabla_simbolos.buscar(ident):
                    simbolo = {
                        "identificador": ident,
                        "categoria": "variable",
                        "tipo_dato": None,
                        "ambito": "Global",
                        "direccion": self.tabla_simbolos.obtener_direccion(),
                        "linea": nodo.get("linea", -1),
                        "valor": self._valor_literal_de_nodo_simple(nodo.get("valor")),
                        "estado": "inicializado",
                        "estructura": None,
                        "contador_referencias": 1
                    }
                    self.tabla_simbolos.insertar(simbolo)
                    print(f"DEBUG: Insertada variable por asignación: {ident}")
        """

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