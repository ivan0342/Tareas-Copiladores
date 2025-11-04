# analizador_sintactico.py
from parser import Parser, ParserError
from interprete import Interprete, RuntimeErrorInterp
import importlib

class AnalizadorSintactico:
    def __init__(self, tabla_simbolos):
        """
        tabla_simbolos: instancia compartida de TablaSimbolos (debe exponer
                        insertar / insertar_simbolo, buscar_simbolo / buscar,
                        obtener_todos / obtener_tabla, actualizar).
        """
        self.tabla_simbolos = tabla_simbolos

    # ---------- helpers para adaptarse a distintas implementaciones de TablaSimbolos ----------
    def _tabla_insertar(self, simbolo):
        """Intenta insertar usando distintos nombres de método posibles."""
        if hasattr(self.tabla_simbolos, "insertar"):
            return self.tabla_simbolos.insertar(simbolo)
        if hasattr(self.tabla_simbolos, "insertar_simbolo"):
            return self.tabla_simbolos.insertar_simbolo(simbolo)
        raise AttributeError("TablaSimbolos no tiene método insertar/insertar_simbolo")

    def _tabla_buscar(self, identificador):
        if hasattr(self.tabla_simbolos, "buscar_simbolo"):
            return self.tabla_simbolos.buscar_simbolo(identificador)
        if hasattr(self.tabla_simbolos, "buscar"):
            return self.tabla_simbolos.buscar(identificador)
        return None

    def _tabla_actualizar(self, identificador, campo, valor):
        # Muchos diseños usan un método actualizar(identificador, valor) o actualizar(simbolo)
        # Intentamos varios enfoques de forma defensiva.
        if hasattr(self.tabla_simbolos, "actualizar"):
            try:
                # intentar actualizar(identificador, valor) (si existe esa firma)
                return self.tabla_simbolos.actualizar(identificador, valor)
            except TypeError:
                # quizás actualizar recibe (simbolo_dict)
                simbolo = self._tabla_buscar(identificador)
                if simbolo is not None:
                    simbolo[campo] = valor
                    # si tabla ofrece guardar/replace, no asumimos firma: solo modificamos el dict
                    return True
                return False
        else:
            simbolo = self._tabla_buscar(identificador)
            if simbolo is not None:
                simbolo[campo] = valor
                return True
            return False

    def _tabla_obtener_todos(self):
        if hasattr(self.tabla_simbolos, "obtener_todos"):
            return self.tabla_simbolos.obtener_todos()
        if hasattr(self.tabla_simbolos, "obtener_tabla"):
            return self.tabla_simbolos.obtener_tabla()
        # fallback: intentar exponer atributos internos
        if hasattr(self.tabla_simbolos, "memoria") or hasattr(self.tabla_simbolos, "overflow"):
            memoria = getattr(self.tabla_simbolos, "memoria", []) or []
            overflow = getattr(self.tabla_simbolos, "overflow", []) or []
            return memoria + overflow
        return []

    # ---------- método principal ----------
    def analizar(self, tokens):
        """
        tokens: lista de dicts [{'token':lexema,'tipo':tipo,'linea':L, 'columna':C}, ...]
        Devuelve: lista de errores sintácticos/semánticos (strings). Lista vacía si no hay.
        """
        errores = []

        # Asegurar EOF al final (Parser puede esperar token tipo "EOF")
        if not tokens or tokens[-1].get("tipo") != "EOF":
            tokens = tokens[:]  # copia superficial para no mutar la original
            tokens.append({"token": "EOF", "tipo": "EOF", "linea": -1, "columna": -1})

        # 1) Parseo -> AST
        try:
            # Intentamos pasar la tabla al Parser si su constructor lo acepta.
            try:
                parser = Parser(tokens, self.tabla_simbolos)
            except TypeError:
                # Parser no acepta tabla en constructor -> usar sólo tokens
                parser = Parser(tokens)
            ast = parser.parse()
        except ParserError as e:
            # Parser levanta en el primer error. Formateamos el mensaje para cumplir requisitos.
            msg = str(e)
            # Si el parser incluye línea/columna en el mensaje, lo dejamos; sino lo normalizamos:
            if "línea" not in msg and "linea" not in msg:
                msg = f"Error sintáctico: {msg}"
            errores.append(msg)
            return errores
        except Exception as e:
            errores.append(f"Error inesperado durante parsing: {e}")
            return errores

        # 2) Recorrer AST para poblar/update tabla de símbolos (declaraciones y asignaciones)
        try:
            self._actualizar_tabla_desde_ast(ast)
        except Exception as e:
            errores.append(f"Error al actualizar tabla de símbolos: {e}")
            return errores

        # 3) Ejecutar AST con intérprete (capturamos salidas)
        salida_lines = []
        def output_callback(valor):
            salida_lines.append(str(valor))

        # IMPORTANTE: asegurarnos de que el intérprete use la misma instancia de tabla.
        # El módulo 'interprete' suele tener una referencia global 'tabla' importada desde tabla_simbolos.
        # Para sincronizar, parcheamos el atributo 'tabla' del módulo interprete antes de instanciar.
        try:
            import interprete as interprete_mod  # módulo
            # asignar la instancia compartida
            setattr(interprete_mod, "tabla", self.tabla_simbolos)
        except Exception:
            # si falla, no es crítico: intentamos continuar, pero el intérprete podría usar otra tabla.
            pass

        interp = Interprete(output=output_callback)
        try:
            interp.ejecutar_programa(ast)
        except RuntimeErrorInterp as re:
            errores.append(f"Error en tiempo de ejecución: {re}")
        except Exception as ex:
            errores.append(f"Error inesperado en intérprete: {ex}")

        # (Opcional) devolver salida como INFO al final
        if salida_lines:
            errores.append("SALIDA_INTERPRETE:")
            errores.extend(salida_lines)

        return errores

    # ---------- helpers para poblar la tabla desde el AST ----------
    def _actualizar_tabla_desde_ast(self, ast):
        """
        Recorre el AST (lista de nodos) e inserta/actualiza símbolos en la tabla de símbolos.
        Maneja nodos: DECL_VAR, ASIGNACION, BLOQUE, SI, MIENTRAS, IMPRIMIR, etc.
        """
        for nodo in ast:
            self._procesar_nodo_para_tabla(nodo)

    def _procesar_nodo_para_tabla(self, nodo):
        if nodo is None:
            return

        if not isinstance(nodo, dict):
            # si el AST tiene elementos primitivos (improbable) -> ignorar
            return

        tipo_n = nodo.get("nodo")
        # Declaración de variable: {"nodo":"DECL_VAR", "tipo": tipo_token, "id":ident, "valor": valorNodo, "linea":L}
        if tipo_n == "DECL_VAR":
            ident = nodo.get("id")
            tipo_dato_token = nodo.get("tipo")  # ej. "entero"
            sim = None
            try:
                sim = self._tabla_buscar(ident)
            except Exception:
                sim = None

            if sim:
                # Actualizamos tipo y estado
                sim["tipo_dato"] = tipo_dato_token
                sim["estado"] = "declarado"
            else:
                simbolo = {
                    "identificador": ident,
                    "categoria": "IDENTIFICADOR",
                    "tipo_dato": tipo_dato_token,
                    "ambito": "Global",
                    "direccion": None,
                    "linea": nodo.get("linea", -1),
                    "valor": None,
                    "estado": "declarado",
                    "estructura": None,
                    "contador_referencias": 0
                }
                # insertar con método compatible
                self._tabla_insertar(simbolo)

            # Si hay un valor inicial (nodo "valor"), tratarlo (no forzamos tipos aquí)
            if nodo.get("valor") is not None:
                sim2 = self._tabla_buscar(ident)
                if sim2:
                    sim2["valor"] = self._valor_literal_de_nodo(nodo["valor"])
                    sim2["estado"] = "inicializado"
                    sim2["contador_referencias"] = sim2.get("contador_referencias", 0) + 1
            return

        # Asignación: {"nodo":"ASIGNACION","id":..., "valor":..., "linea":L}
        if tipo_n == "ASIGNACION":
            ident = nodo.get("id")
            sim = None
            try:
                sim = self._tabla_buscar(ident)
            except Exception:
                sim = None

            valor_repr = self._valor_literal_de_nodo(nodo.get("valor"))
            if not sim:
                # Insertar símbolo aunque no declarado (se puede considerar semántico)
                simbolo = {
                    "identificador": ident,
                    "categoria": "IDENTIFICADOR",
                    "tipo_dato": None,
                    "ambito": "Global",
                    "direccion": None,
                    "linea": nodo.get("linea", -1),
                    "valor": valor_repr,
                    "estado": "inicializado",
                    "estructura": None,
                    "contador_referencias": 1
                }
                self._tabla_insertar(simbolo)
            else:
                # actualizar valor/estado/contador
                # preferimos usar método actualizar si existe
                updated = False
                try:
                    updated = self._tabla_actualizar(ident, "valor", valor_repr)
                except Exception:
                    updated = False

                if not updated:
                    sim["valor"] = valor_repr
                    sim["estado"] = "inicializado"
                    sim["contador_referencias"] = sim.get("contador_referencias", 0) + 1

            # recorrer subnodos por si contienen declaraciones internas
            self._recorrer_y_procesar(nodo.get("valor"))
            return

        # BLOQUE
        if tipo_n == "BLOQUE":
            for s in nodo.get("sentencias", []):
                self._procesar_nodo_para_tabla(s)
            return

        # SI / MIENTRAS (condiciones y cuerpos)
        if tipo_n in ("SI", "MIENTRAS"):
            # procesar condición
            self._recorrer_y_procesar(nodo.get("cond"))
            then_node = nodo.get("then") or nodo.get("cuerpo")
            if then_node:
                self._procesar_nodo_para_tabla(then_node)
            if nodo.get("else"):
                self._procesar_nodo_para_tabla(nodo.get("else"))
            return

        # IMPRIMIR
        if tipo_n == "IMPRIMIR":
            self._recorrer_y_procesar(nodo.get("valor"))
            return

        # Otros nodos: BIN_OP, VAR, LIT_* ... no crean símbolos, pero recorremos por seguridad
        self._recorrer_y_procesar(nodo)

    def _recorrer_y_procesar(self, posible):
        if posible is None:
            return
        if isinstance(posible, dict):
            if "nodo" in posible:
                # Es un nodo AST => procesarlo
                self._procesar_nodo_para_tabla(posible)
            else:
                for v in posible.values():
                    self._recorrer_y_procesar(v)
        elif isinstance(posible, list):
            for item in posible:
                self._recorrer_y_procesar(item)

    def _valor_literal_de_nodo(self, nodo_val):
        """
        Si nodo_val es literal (LIT_INT, LIT_FLOAT, LIT_STR), devuelve su valor primitivo.
        Si es VAR devuelve "VAR:<id>". Si es expresión compuesta, devuelve una representación.
        """
        if nodo_val is None:
            return None
        if isinstance(nodo_val, dict):
            n = nodo_val.get("nodo")
            if n in ("LIT_INT", "ENTERO_LIT"):
                return nodo_val.get("valor")
            if n in ("LIT_FLOAT", "FLOTANTE_LIT"):
                return nodo_val.get("valor")
            if n in ("LIT_STR", "CADENA_LIT"):
                return nodo_val.get("valor")
            if n == "VAR":
                return f"VAR:{nodo_val.get('id')}"
            # expresion compuesta
            return f"<expr:{n}>"
        # primitivo directo
        return nodo_val
