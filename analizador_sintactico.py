# analizador_sintactico.py
from parser import Parser, ParserError
from interprete import Interprete, RuntimeErrorInterp

class AnalizadorSintactico:
    def __init__(self, tabla_simbolos):
        """
        tabla_simbolos: instancia de tu TablaSimbolos (debe exponer insertar_simbolo,
                       buscar_simbolo, obtener_todos, etc.)
        """
        self.tabla_simbolos = tabla_simbolos

    def analizar(self, tokens):
        print("TOKENS RECIBIDOS POR EL PARSER:")
        for t in tokens:
         print(t)
        """
        tokens: lista de dicts [{'token':lexema,'tipo':tipo,'linea':L, 'columna':C}, ...]
        Devuelve: lista de errores sintácticos/semánticos (strings). Lista vacía si no hay.
        """
        errores = []

        # Asegurar EOF al final (Parser espera token tipo "EOF")
        if not tokens or tokens[-1].get("tipo") != "EOF":
            tokens = tokens[:]  # copia superficial
            tokens.append({"token": "EOF", "tipo": "EOF", "linea": -1, "columna": -1})

        # 1) Parseo -> AST
        try:
            parser = Parser(tokens ,self.tabla_simbolos)
            ast = parser.parse()
        except ParserError as e:
            # Parser levanta en el primer error. Devolvemos mensaje útil.
            errores  = parser.errores

        # 2) Recorrer AST para poblar/update tabla de símbolos (declaraciones y asignaciones)
        #try:
        #    self._actualizar_tabla_desde_ast(ast)
        #except Exception as e:
        #    errores.append(f"Error al actualizar tabla de símbolos: {e}")
        #    # No retornamos aún: podríamos intentar ejecutar, pero mejor reportar y parar.
        #    return errores

        # 3) Ejecutar AST con intérprete (capturamos salidas)
        salida_lines = []
        def output_callback(valor):
            # convertir valor a string para mostrar en GUI
            salida_lines.append(str(valor))

        interp = Interprete(output=output_callback)
        try:
            interp.ejecutar_programa(ast)
        except RuntimeErrorInterp as re:
            errores.append(f"Error en tiempo de ejecución: {re}")
        except Exception as ex:
            errores.append(f"Error inesperado en intérprete: {ex}")

        # (Opcional) podríamos devolver la salida como parte de errores con prefijo INFO
        if salida_lines:
            errores.append("SALIDA_INTERPRETE:")
            errores.extend(salida_lines)

        return errores

    # ---------- helpers ----------
    def _actualizar_tabla_desde_ast(self, ast):
        """
        Recorre el AST (lista de nodos) e inserta/actualiza símbolos en la tabla de símbolos.
        Maneja nodos: DECL_VAR, ASIGNACION, (podemos ampliar para funciones)
        """
        for nodo in ast:
            self._procesar_nodo_para_tabla(nodo)

    def _procesar_nodo_para_tabla(self, nodo):
        if nodo is None:
            return

        tipo_n = nodo.get("nodo")
        # Declaración de variable: {"nodo":"DECL_VAR", "tipo": tipo_token, "id":ident, "valor": valorNodo, "linea":L}
        if tipo_n == "DECL_VAR":
            ident = nodo.get("id")
            tipo_dato_token = nodo.get("tipo")  # como aparece en el token (ej. "entero")

            # Buscar si ya existe el símbolo
            try:
                sim = self.tabla_simbolos.buscar_simbolo(ident)
                print("Símbolo encontrado:", sim)
            except Exception:
                sim = None

            if sim is None:
                # No existe -> creamos nuevo símbolo
                simbolo = {
                    "identificador": ident,
                    "categoria": "variable",
                    "tipo_dato": tipo_dato_token,
                    "ambito": "Global",
                    "direccion": None,
                    "linea": nodo.get("linea", -1),
                    "valor": self._valor_literal_de_nodo(nodo.get("valor")),
                    "estado": "declarado" if nodo.get("valor") is None else "inicializado",
                    "estructura": None,
                    "contador_referencias": 1
                }
                self.tabla_simbolos.insertar(simbolo)
                print(f"Símbolo nuevo insertado: {simbolo}")
            else:
                # Ya existe -> actualizamos tipo y/o valor
                if isinstance(sim, dict):
                    sim["tipo_dato"] = tipo_dato_token
                    sim["estado"] = "declarado"

                    if nodo.get("valor") is not None:
                        sim["valor"] = self._valor_literal_de_nodo(nodo.get("valor"))
                        sim["estado"] = "inicializado"
                        sim["contador_referencias"] = sim.get("contador_referencias", 0) + 1
                        print(f"Símbolo actualizado: {sim}")
                else:
                    print(f"Advertencia: símbolo {ident} no es un diccionario válido.")

            return

        # Asignación: {"nodo":"ASIGNACION","id":..., "valor":..., "linea":L}
        if tipo_n == "ASIGNACION":
            ident = nodo.get("id")
            sim = None
            try:
                sim = self.tabla_simbolos.buscar_simbolo(ident)
            except Exception:
                sim = None

            if not sim:
                # Insertar símbolo aunque no declarado (para pruebas); idealmente esto sería un error semántico
                simbolo = {
                    "identificador": ident,
                    "categoria": "IDENTIFICADOR",
                    "tipo_dato": None,
                    "ambito": "Global",
                    "direccion": None,
                    "linea": nodo.get("linea", -1),
                    "valor": self._valor_literal_de_nodo(nodo.get("valor")),
                    "estado": "inicializado",
                    "estructura": None,
                    "contador_referencias": 1
                }
                self.tabla_simbolos.insertar(simbolo)
            else:
                sim["valor"] = self._valor_literal_de_nodo(nodo.get("valor"))
                sim["estado"] = "inicializado"
                sim["contador_referencias"] = sim.get("contador_referencias", 0) + 1
            # procesar subnodos por si contienen declaraciones internas
            self._recorrer_y_procesar(nodo.get("valor"))
            return

        # Bloques/condicionales/bucles -> recorrer contenido
        if tipo_n == "BLOQUE":
            for s in nodo.get("sentencias", []):
                self._procesar_nodo_para_tabla(s)
            return

        if tipo_n in ("SI", "MIENTRAS"):
            # procesar cond y cuerpos
            self._recorrer_y_procesar(nodo.get("cond"))
            then_node = nodo.get("then") or nodo.get("cuerpo")
            if then_node:
                self._procesar_nodo_para_tabla(then_node)
            else:
                # else
                if nodo.get("else"):
                    self._procesar_nodo_para_tabla(nodo.get("else"))
            return

        if tipo_n == "IMPRIMIR":
            # no declarar, pero recorrer la expresión
            self._recorrer_y_procesar(nodo.get("valor"))
            return

        # BIN_OP, VAR, LIT_* ... no crean símbolos, pero pueden contener subnodos
        # por seguridad recorremos campos que sean nodos o listas de nodos
        self._recorrer_y_procesar(nodo)

    def _recorrer_y_procesar(self, posible):
        if posible is None:
            return
        if isinstance(posible, dict):
            # si es nodo AST
            if "nodo" in posible:
                self._procesar_nodo_para_tabla(posible)
            else:
                # recorrer keys
                for v in posible.values():
                    self._recorrer_y_procesar(v)
        elif isinstance(posible, list):
            for item in posible:
                self._recorrer_y_procesar(item)

    def _valor_literal_de_nodo(self, nodo_val):
        """
        Si nodo_val es literal (LIT_INT, LIT_FLOAT, LIT_STR), devuelve su valor primitivo.
        Si no, devuelve la representación en string del nodo para almacenar en la tabla.
        """
        if nodo_val is None:
            return None
        if isinstance(nodo_val, dict):
            n = nodo_val.get("nodo")
            if n == "LIT_INT":
                return nodo_val.get("valor")
            if n == "LIT_FLOAT":
                return nodo_val.get("valor")
            if n == "LIT_STR":
                return nodo_val.get("valor")
            if n == "VAR":
                return f"VAR:{nodo_val.get('id')}"
            # para expresiones compuestas devolvemos una representación
            return f"<expr:{n}>"
        # si es primitivo directamente
        return nodo_val
