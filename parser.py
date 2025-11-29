#parser.py
from tabla_simbolos import TablaSimbolos
from verificaciones.clasificacion_errores import CategoriaError, ReporteErrores
from verificaciones.verificadot_tipos import VerificadorTipos
from verificaciones.validador_incializacion import ValidadorInicializacion
class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens, tabla_simbolos, reporte_errores):
        self.tokens = tokens
        self.i = 0
        self.errores = []
        self.tabla_simbolos = tabla_simbolos
        self.ast = []  # árbol sintáctico abstracto
        self.reporte = reporte_errores
        self.verificador_tipos = VerificadorTipos(tabla_simbolos, reporte_errores)
        self.validador_inicializacion = ValidadorInicializacion(tabla_simbolos, reporte_errores)

    def error(self, mensaje):
        tok = self.actual()
        self.errores.append(f"{mensaje} en línea {tok['linea']}")
        raise ParserError(mensaje)

    def match_multiple(self, *tipos):
        if self.i < len(self.tokens) and self.tokens[self.i]["tipo"] in tipos:
            token = self.tokens[self.i]
            self.i += 1
            return token
        return None

    def actual(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        else:
            return {"tipo": "EOF", "token": "EOF", "linea": -1, "columna": -1}

    def match(self, tipo_esperado):
        if self.check(tipo_esperado):
            token = self.tokens[self.i]
            self.i += 1
            return token
        else:
            # Manejo de error: devuelve None pero registra el problema
            if self.i < len(self.tokens):
                actual = self.tokens[self.i]
                print(f"[Error sintáctico] Se esperaba '{tipo_esperado}', pero se encontró '{actual['tipo']}' en línea {actual['linea']}")
                self.errores.append(f"Se esperaba '{tipo_esperado}', pero se encontró '{actual['tipo']}' en línea {actual['linea']}")
            else:
                print(f"[Error sintáctico] Se esperaba '{tipo_esperado}', pero se llegó al final del archivo.")
                self.errores.append(f"Se esperaba '{tipo_esperado}', pero se llegó al final del archivo.")
            return None

    def check(self, tipo_esperado):
        if self.i >= len(self.tokens):
            return False
        return self.tokens[self.i]["tipo"] == tipo_esperado

    def parse(self):
        while self.actual()["tipo"] != "EOF":            
            try:
                nodo = self.declaracion_o_sentencia()
                if nodo:
                    self.ast.append(nodo)
            except ParserError as e:
                self.errores.append(str(e))
                self.i += 1
            print(self.ast)
        return self.ast



    # -------------------------------------------------------
    # DECISIONES PRINCIPALES
    # -------------------------------------------------------
    def declaracion_o_sentencia(self):
        actual = self.actual()
        tipo = actual["tipo"]

        # --- Importar, Exportar, Usar ---
        if tipo == "IMPORTAR":
            return self.declaracion_importar()
        elif tipo == "EXPORTAR":
            return self.declaracion_exportar()
        elif tipo == "USAR":
            return self.declaracion_usar()

        # --- Constante ---
        elif tipo == "CONSTANTE":
            return self.declaracion_constante()

        # --- Declaración de función o variable ---
        elif tipo in ("TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_CADENA", "TIPO_VACIO"):
            if self.i + 2 < len(self.tokens):
                sig1 = self.tokens[self.i + 1]["tipo"]
                sig2 = self.tokens[self.i + 2]["tipo"]
                if sig1 == "IDENTIFICADOR" and sig2 == "PAREN_IZQ":
                    return self.declaracion_funcion()
                else:
                    return self.declaracion_variable()
            else:
                return self.declaracion_variable()

        # --- Declaración de variable con tipo clase (IDENTIFICADOR + IDENTIFICADOR) ---
        elif tipo == "IDENTIFICADOR" and self._es_declaracion_clase():
            return self.declaracion_variable_con_clase()

        # --- Clase ---
        elif tipo == "CLASE":
            return self.declaracion_clase()
        # --- Interfaz ---
        elif tipo == "INTERFAZ":
            return self.declaracion_interfaz()
        # --- Condicional ---
        elif tipo == "SI":
            return self.condicional()

        # --- Bucle ---
        elif tipo == "MIENTRAS":
            return self.bucle_mientras()

        # --- Imprimir ---
        elif tipo == "IMPRIMIR":
            return self.imprimir_sentencia()

        # --- Sentencias de control ---
        elif tipo == "ROMPER":
            return self.sentencia_romper()
        elif tipo == "CONTINUAR":
            return self.sentencia_continuar()
        elif tipo == "RETORNAR":
            return self.sentencia_retornar()

        # --- Bloque ---
        elif tipo == "LLAVE_IZQ":
            return self.bloque()

        # --- Asignación o llamada ---
        elif tipo == "IDENTIFICADOR":
            return self.asignacion_o_llamada()

        elif tipo == "SEGUN":
            return self.sentencia_segun()

        elif tipo == "PARA":
            return self.bucle_para()

        elif tipo == "HACER":
            return self.bucle_hacer_mientras()

        elif tipo == "INTENTAR":
            return self.manejo_errores()

        # --- Caso por defecto ---
        else:
            print(f"[Error sintáctico] Token inesperado '{actual['tipo']}' en línea {actual['linea']}")
            self.errores.append(
                f"[Error sintáctico] Token inesperado '{actual['tipo']}' en línea {actual['linea']}"
            )
            self.i += 1
            return None

    def _es_declaracion_clase(self):
        """Determina si es una declaración de variable con tipo de clase"""
        if self.i + 1 < len(self.tokens):
            siguiente = self.tokens[self.i + 1]
            # Patrón: IDENTIFICADOR (clase) + IDENTIFICADOR (nombre variable)
            return siguiente["tipo"] == "IDENTIFICADOR"
        return False

    def declaracion_variable_con_clase(self):
        """Maneja declaraciones como: Persona p = nuevo Persona();"""
        tipo_clase = self.match("IDENTIFICADOR")["token"]
        nombre = self.match("IDENTIFICADOR")["token"]
        linea = self.actual()["linea"]
        valor = None

        # Si hay asignación
        if self.actual()["tipo"] == "ASIGNACION":
            self.match("ASIGNACION")
            if self.actual()["tipo"] not in ("PUNTO_Y_COMA", "EOF"):
                try:
                    valor = self.expresion()
                except Exception as e:
                    self.errores.append(f"[Error sintáctico] Error al analizar expresión en variable '{nombre}': {e}")
                    # Sincronizar
                    while self.actual()["tipo"] != "PUNTO_Y_COMA" and self.actual()["tipo"] != "EOF":
                        self.i += 1

        # Verificar punto y coma
        if not self.check("PUNTO_Y_COMA"):
            self.errores.append(f"[Error sintáctico] Error: falta ';' en declaración de '{nombre}'")
            while self.actual()["tipo"] != "PUNTO_Y_COMA" and self.actual()["tipo"] != "EOF":
                self.i += 1

        if self.check("PUNTO_Y_COMA"):
            self.match("PUNTO_Y_COMA")

        # Insertar en tabla de símbolos
        simbolo = {
            "identificador": nombre,
            "categoria": "variable",
            "tipo_dato": tipo_clase,  # Usar el nombre de la clase como tipo
            "linea": linea,
            "ambito": "Global",
            "direccion": self.tabla_simbolos.obtener_direccion(),
            "valor": self._obtener_valor_literal(valor) if valor else None,
            "estado": "inicializado" if valor else "declarado",
            "estructura": "-",
            "contador_referencias": 1
        }
        try:
            self.tabla_simbolos.insertar(simbolo)
        except Exception as e:
            print(f"Error al insertar símbolo {nombre}: {e}")

        return {"nodo": "DECL_VAR", "tipo": tipo_clase, "id": nombre, "valor": valor, "linea": linea}

    # -------------------------------------------------------

    def declaracion_importar(self):
        self.match("IMPORTAR")
        nombre = self.match("IDENTIFICADOR")["token"]
        self.match("PUNTO_Y_COMA")
        return {"nodo": "IMPORTAR", "modulo": nombre}

    def declaracion_exportar(self):
        self.match("EXPORTAR")
        nombre = self.match("IDENTIFICADOR")["token"]
        self.match("PUNTO_Y_COMA")
        return {"nodo": "EXPORTAR", "elemento": nombre}

    def declaracion_usar(self):
        self.match("USAR")
        nombre = self.match("IDENTIFICADOR")["token"]
        self.match("PUNTO_Y_COMA")
        return {"nodo": "USAR", "biblioteca": nombre}

    def declaracion_constante(self):
        print("DEBUG: Procesando declaración de constante")
        
        self.match("CONSTANTE")
        tipo_token = self.match(self.actual()["tipo"])
        tipo = tipo_token["token"]
        nombre = self.match("IDENTIFICADOR")["token"]
        self.match("ASIGNACION")
        valor = self.expresion()
        self.match("PUNTO_Y_COMA")

        print(f"DEBUG: Procesando constante '{nombre}' = {valor}")

        
        # CORREGIR: Usar insertar_variable_extendida para constante
        if hasattr(self.tabla_simbolos, 'insertar_variable_extendida'):
            # Extraer valor literal
            valor_literal = None
            if valor is not None:
                if isinstance(valor, dict) and valor.get("nodo") in ["LIT_INT", "LIT_FLOAT", "LIT_STR", "LIT_BOOL",
                                                                     "LIT_CHAR"]:
                    valor_literal = valor.get("valor")
                    print(f"DEBUG: Valor literal extraído: {valor_literal}")

            success = self.tabla_simbolos.insertar_variable_extendida(
                nombre, tipo, self.actual()["linea"],
                es_constante=True, valor=valor_literal
            )
            print(f"DEBUG: Constante '{nombre}' insertada: {success}")

            # VERIFICAR INMEDIATAMENTE
            if hasattr(self.tabla_simbolos, 'constantes_extendidas'):
                const_verificada = nombre in self.tabla_simbolos.constantes_extendidas
                print(f"DEBUG: Constante '{nombre}' en constantes_extendidas: {const_verificada}")
                if const_verificada:
                    print(f"DEBUG: Valor almacenado: {self.tabla_simbolos.constantes_extendidas[nombre].valor}")
        
        simbolo = {
            "identificador": nombre,
            "categoria": "constante",  # 🔥 Esto es crucial
            "tipo_dato": tipo,
            "linea": self.actual()["linea"],
            "ambito": "Global",
            "direccion": self.tabla_simbolos.obtener_direccion(),
            "valor": valor,
            "estado": "inicializado",
            "estructura": "-",
            "contador_referencias": 1,
            }
        self.tabla_simbolos.insertar(simbolo)
        print(f"DEBUG: Constante '{nombre}' insertada en tabla antigua")

        return {"nodo": "CONSTANTE", "tipo": tipo, "id": nombre, "valor": valor, "linea": self.actual()["linea"]}

    # -------------------------------------------------------

    def asignacion_o_llamada(self):
        print("ENTREEEE A ASIGNACION O LLAMADA");
        nombre = self.match("IDENTIFICADOR")["token"]
        linea = self.actual()["linea"]

        # Si es llamada a función/método
        if self.actual()["tipo"] == "PAREN_IZQ":
            self.match("PAREN_IZQ")
            args = []
            if self.actual()["tipo"] != "PAREN_DER":
                args.append(self.expresion())
                while self.actual()["tipo"] == "COMA":
                    self.match("COMA")
                    args.append(self.expresion())
            self.match("PAREN_DER")
            self.match("PUNTO_Y_COMA")

            # ✅ PROCESAR REFERENCIAS EN ARGUMENTOS
            for arg in args:
                if isinstance(arg, dict):
                    self._procesar_referencias_en_expresion(arg)

            return {"nodo": "LLAMADA_FUNCION", "id": nombre, "args": args, "linea": linea}

        # Si es asignación
        elif self.actual()["tipo"] == "ASIGNACION":
            self.match("ASIGNACION")
            valor = self.expresion()
            self.match("PUNTO_Y_COMA")

            # ✅ PROCESAR REFERENCIAS EN EL VALOR DE ASIGNACIÓN
            if valor is not None:
                self._procesar_referencias_en_expresion(valor)

            # Actualizar tabla de símbolos
            if hasattr(self.tabla_simbolos, 'buscar_variable_extendida'):
                variable = self.tabla_simbolos.buscar_variable_extendida(nombre)
                if variable:
                    # Extraer valor literal para la tabla
                    valor_literal = None
                    if valor is not None:
                        if isinstance(valor, dict) and valor.get("nodo") in ["LIT_INT", "LIT_FLOAT", "LIT_STR",
                                                                             "LIT_BOOL", "LIT_CHAR"]:
                            valor_literal = valor.get("valor")
                    variable.valor = valor_literal
            else:
                simbolo = self.tabla_simbolos.buscar(nombre)
                if simbolo:
                    self.tabla_simbolos.actualizar(nombre, valor)
                    simbolo["estado"] = "actualizado"

            return {"nodo": "ASIGNACION", "id": nombre, "valor": valor, "linea": linea}

        else:
            self.errores.append(f"[Error sintáctico] Se esperaba '=' o '(' después de {nombre}")
            return None

        # ----------------------------------------------

    def sentencia_romper(self):
        self.match("ROMPER")
        self.match("PUNTO_Y_COMA")
        return {"nodo": "ROMPER"}

    def sentencia_continuar(self):
        self.match("CONTINUAR")
        self.match("PUNTO_Y_COMA")
        return {"nodo": "CONTINUAR"}

    def sentencia_retornar(self):
        self.match("RETORNAR")
        valor = None
        if self.actual()["tipo"] != "PUNTO_Y_COMA":
            valor = self.expresion()
        self.match("PUNTO_Y_COMA")
        return {"nodo": "RETORNAR", "valor": valor}

    # -------------------------------------------------------
    # DECLARACIÓN DE VARIABLES
    # -------------------------------------------------------
    def declaracion_variable(self):
        tipo_token = self.match(self.actual()["tipo"])
        tipo = tipo_token["token"] if tipo_token else "desconocido"
        linea = tipo_token["linea"]

        # Verificar si el siguiente token es IDENTIFICADOR
        if self.actual()["tipo"] != "IDENTIFICADOR":
            self.errores.append(
                f"[Error sintáctico] Error: se esperaba un identificador después del tipo '{tipo}' en línea {self.actual()['linea']}.")
            print(
                f"[Error sintáctico] Se esperaba un identificador después del tipo '{tipo}' en línea {self.actual()['linea']}.")
            # Intentamos sincronizar saltando hasta el siguiente ';' para no romper el análisis
            while self.actual()["tipo"] != "PUNTO_Y_COMA" and self.actual()["tipo"] != "EOF":
                self.i += 1
            if self.check("PUNTO_Y_COMA"):
                self.match("PUNTO_Y_COMA")
            return None

        # Si hay identificador, seguimos normalmente
        nombre = self.match("IDENTIFICADOR")["token"]
        valor = None

        # Si hay signo de asignación, procesar la expresión
        if self.actual()["tipo"] == "ASIGNACION":
            self.match("ASIGNACION")

            # Verificar que haya una expresión válida después del =
            if self.actual()["tipo"] in ("PUNTO_Y_COMA", "EOF"):
                self.errores.append(
                    f"[Error sintáctico] Error: falta una expresión después del signo '=' en la variable '{nombre}' (línea {linea}).")
                print(
                    f"[Error sintáctico] Error: falta una expresión después del signo '=' en la variable '{nombre}' (línea {linea}).")
            else:
                try:
                    # Usar expresion() para analizar el valor
                    valor = self.expresion()

                    # ✅ PROCESAR REFERENCIAS EN LA EXPRESIÓN
                    if valor is not None:
                        self._procesar_referencias_en_expresion(valor)

                except Exception as e:
                    self.errores.append(f"[Error sintáctico] Error al analizar expresión en variable '{nombre}': {e}")
                    print(f"[Error sintáctico] Error al analizar expresión en variable '{nombre}': {e}")
                    # Sincronizar
                    while self.actual()["tipo"] != "PUNTO_Y_COMA" and self.actual()["tipo"] != "EOF":
                        self.i += 1

        # Verificar que la declaración termine con ';'
        if not self.check("PUNTO_Y_COMA"):
            self.errores.append(
                f"[Error sintáctico] Error: falta ';' al final de la declaración de la variable '{nombre}' (línea {linea}).")
            print(
                f"[Error sintáctico] Error: falta ';' al final de la declaración de la variable '{nombre}' (línea {linea}).")
            # Intentamos sincronizar hasta el siguiente ';' o EOF
            while self.actual()["tipo"] != "PUNTO_Y_COMA" and self.actual()["tipo"] != "EOF":
                self.i += 1

        if self.check("PUNTO_Y_COMA"):
            self.match("PUNTO_Y_COMA")

        if nombre and "desconocido" not in tipo:
            simbolo = {
                "identificador": nombre,
                "categoria": "variable",
                "tipo_dato": tipo,
                "linea": linea,
                "ambito": "Global",
                "direccion": self.tabla_simbolos.obtener_direccion(),
                "valor": self._obtener_valor_literal(valor) if valor else None,
                "estado": "inicializado" if valor else "declarado",
                "estructura": "-",
                "contador_referencias": 0  # 🔥 Iniciar en 0, se incrementará después
            }
            try:
                self.tabla_simbolos.insertar(simbolo)
                print(f"🔥 DEBUG: Variable '{nombre}' insertada via insertar()")
            except Exception as e:
                print(f"Error al insertar símbolo {nombre}: {e}")

        return {"nodo": "DECL_VAR", "tipo": tipo, "id": nombre, "valor": valor, "linea": linea}

    def _obtener_valor_literal(self, nodo):
        """Extrae el valor literal de un nodo AST para la tabla de símbolos"""
        if nodo is None:
            return None
        if isinstance(nodo, dict):
            if nodo.get("nodo") == "LIT_INT":
                return nodo.get("valor")
            elif nodo.get("nodo") == "LIT_FLOAT":
                return nodo.get("valor")
            elif nodo.get("nodo") == "LIT_STR":
                return nodo.get("valor")
            elif nodo.get("nodo") == "LIT_BOOL":
                return nodo.get("valor")
            elif nodo.get("nodo") == "LIT_CHAR":
                return nodo.get("valor")
            elif nodo.get("nodo") == "VAR":
                return f"<ref:{nodo.get('id')}>"
            else:
                # Para expresiones complejas, devolver representación
                return f"<expr:{nodo.get('nodo')}>"
        return str(nodo)

    # -------------------------------------------------------
    # ASIGNACIÓN
    # -------------------------------------------------------
    def asignacion(self):
        nombre = self.match("IDENTIFICADOR")["token"]

        if self.actual()["tipo"] == "ASIGNACION":
            self.match("ASIGNACION")
            valor = self.expresion()
            self.match("PUNTO_Y_COMA")

            simbolo = self.tabla_simbolos.buscar(nombre)
            if simbolo:
                self.tabla_simbolos.actualizar(nombre, valor)
                simbolo["estado"] = "actualizado"
            else:
                self.errores.append(f"[Error sintáctico] Variable '{nombre}' no declarada.")
                print(f"[Error sintáctico] Variable '{nombre}' no declarada.")

            return {"nodo": "ASIGNACION", "id": nombre, "valor": valor, "linea": self.actual()["linea"]}
        else:
            self.errores.append(f"[Error sintáctico] Error: se esperaba '=' después de {nombre}")
            print(f"[Error sintáctico] Error: se esperaba '=' después de {nombre}")
            return None

    # -------------------------------------------------------
    # CONDICIONAL (SI ... SINO)
    # -------------------------------------------------------
    def condicional(self):
        self.match("SI")
        self.match("PAREN_IZQ")
        condicion = self.expresion()
        self.match("PAREN_DER")
        bloque_then = self.bloque()
        bloque_else = None

        if self.actual()["tipo"] == "SINO":
            self.match("SINO")
            bloque_else = self.bloque()

        return {"nodo": "SI", "cond": condicion, "then": bloque_then, "else": bloque_else}

    def sentencia_segun(self):
        self.match("SEGUN")
        self.match("PAREN_IZQ")
        expr = self.expresion()
        self.match("PAREN_DER")
        self.match("LLAVE_IZQ")

        casos = []
        defecto = None

        while self.actual()["tipo"] != "LLAVE_DER" and self.actual()["tipo"] != "EOF":
            if self.actual()["tipo"] == "CASO":
                self.match("CASO")
                valor = self.expresion()
                self.match("DOS_PUNTOS")
                sentencias = []
                while self.actual()["tipo"] not in ("CASO", "DEFECTO", "LLAVE_DER", "EOF"):
                    sentencias.append(self.declaracion_o_sentencia())
                casos.append({"valor": valor, "sentencias": sentencias})
            elif self.actual()["tipo"] == "DEFECTO":
                self.match("DEFECTO")
                self.match("DOS_PUNTOS")
                sentencias = []
                while self.actual()["tipo"] not in ("LLAVE_DER", "EOF"):
                    sentencias.append(self.declaracion_o_sentencia())
                defecto = sentencias
                break
            else:
                self.error(f"Token inesperado en 'segun': {self.actual()['tipo']}")

        self.match("LLAVE_DER")

        return {"nodo": "SEGUN", "expr": expr, "casos": casos, "defecto": defecto}
    # -------------------------------------------------------
    # BUCLES
    # -------------------------------------------------------
    def bucle_mientras(self):
        self.match("MIENTRAS")
        self.match("PAREN_IZQ")
        cond = self.expresion()
        self.match("PAREN_DER")
        cuerpo = self.bloque()
        return {"nodo": "MIENTRAS", "cond": cond, "cuerpo": cuerpo}
    
    def bucle_para(self):
        self.match("PARA")
        self.match("PAREN_IZQ")

        # --- Inicialización ---
        init = None
        if self.actual()["tipo"] in ("TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_CADENA"):
            init = self.declaracion_variable()
        elif self.actual()["tipo"] == "IDENTIFICADOR":
            init = self.asignacion()
        else:
            # si no hay nada antes del primer ';'
            self.match("PUNTO_Y_COMA")

        # --- Condición ---
        cond = None
        if self.actual()["tipo"] != "PUNTO_Y_COMA":
            cond = self.expresion()
        self.match("PUNTO_Y_COMA")

        # --- Incremento ---
        inc = None
        if self.actual()["tipo"] != "PAREN_DER":
            if self.actual()["tipo"] == "IDENTIFICADOR":
                id_token = self.match("IDENTIFICADOR")
                if self.actual()["tipo"] in ("ASIGNACION", "INCREMENTO", "DECREMENTO"):
                    op_token = self.match(self.actual()["tipo"])

                    if op_token["tipo"] == "ASIGNACION":
                        valor = self.expresion()
                        inc = {
                            "nodo": "ASIGNACION",
                            "id": id_token,
                            "op": op_token,
                            "valor": valor
                        }
                    else:
                        # incremento o decremento tipo i++ o i--
                        inc = {
                            "nodo": "UNARIO",
                            "id": id_token,
                            "op": op_token
                        }
                else:
                    # caso raro: solo identificador sin operador
                    inc = {"nodo": "IDENTIFICADOR", "token": id_token}
            else:
                inc = self.expresion()

        self.match("PAREN_DER")

        # --- Cuerpo del bucle ---
        cuerpo = self.bloque()

        return {
            "nodo": "PARA",
            "init": init,
            "cond": cond,
            "inc": inc,
            "cuerpo": cuerpo
        }

    def bucle_hacer_mientras(self):
        self.match("HACER")
        cuerpo = self.bloque()
        self.match("MIENTRAS")
        self.match("PAREN_IZQ")
        cond = self.expresion()
        self.match("PAREN_DER")
        self.match("PUNTO_Y_COMA")
        return {"nodo": "HACERMIENTRAS", "cond": cond, "cuerpo": cuerpo}



    # -------------------------------------------------------
    # IMPRIMIR
    # -------------------------------------------------------
    def imprimir_sentencia(self):
        self.match("IMPRIMIR")
        self.match("PAREN_IZQ")
        expr = self.expresion()

        # ✅ PROCESAR REFERENCIAS EN LA EXPRESIÓN DE IMPRIMIR
        if expr is not None:
            self._procesar_referencias_en_expresion(expr)
            print(f"DEBUG: Procesadas referencias en imprimir")

        self.match("PAREN_DER")
        self.match("PUNTO_Y_COMA")
        return {"nodo": "IMPRIMIR", "valor": expr}
    # -------------------------------------------------------
    # BLOQUES { ... }
    # -------------------------------------------------------
    def bloque(self):
        self.match("LLAVE_IZQ")
        sentencias = []
        while self.actual()["tipo"] != "LLAVE_DER" and self.actual()["tipo"] != "EOF":
            sentencias.append(self.declaracion_o_sentencia())
        self.match("LLAVE_DER")
        return {"nodo": "BLOQUE", "sentencias": sentencias}

    # -------------------------------------------------------
    # EXPRESIONES (jerarquía de operadores)
    # -------------------------------------------------------
    def expresion(self):
        return self.exp_or()

    def exp_or(self):
        nodo = self.exp_and()
        while self.actual()["tipo"] == "OR":
            op = self.match("OR")
            rhs = self.exp_and()
            nodo = {"nodo": "BIN_OP", "op": op["tipo"], "izq": nodo, "der": rhs}
        return nodo

    def exp_and(self):
        nodo = self.exp_rel()
        while self.actual()["tipo"] == "AND":
            op = self.match("AND")
            rhs = self.exp_rel()
            nodo = {"nodo": "BIN_OP", "op": op["tipo"], "izq": nodo, "der": rhs}
        return nodo

    def exp_rel(self):
        nodo = self.exp_sum()
        while self.actual()["tipo"] in ("IGUAL", "DISTINTO", "MENOR", "MAYOR", "MENOR_IGUAL", "MAYOR_IGUAL"):
            op = self.match(self.actual()["tipo"])
            rhs = self.exp_sum()
            nodo = {"nodo": "BIN_OP", "op": op["tipo"], "izq": nodo, "der": rhs}
        return nodo

    def exp_sum(self):
        nodo = self.exp_mul()
        while self.actual()["tipo"] in ("MAS", "MENOS"):
            op = self.match(self.actual()["tipo"])
            rhs = self.exp_mul()
            nodo = {"nodo": "BIN_OP", "op": op["tipo"], "izq": nodo, "der": rhs}

            # CORREGIR: Incrementar contadores de variables en expresiones binarias
            #self._incrementar_referencias_en_expresion(nodo)

        return nodo

    def exp_mul(self):
        nodo = self.factor()
        while self.actual()["tipo"] in ("MULT", "DIV", "MOD"):
            op = self.match(self.actual()["tipo"])
            rhs = self.factor()
            nodo = {"nodo": "BIN_OP", "op": op["tipo"], "izq": nodo, "der": rhs}
        return nodo

    def _incrementar_referencias_en_expresion(self, nodo_expresion):
        """Recorre una expresión e incrementa contadores de variables usadas"""
        if not isinstance(nodo_expresion, dict):
            return

        if nodo_expresion.get("nodo") == "VAR":
            nombre = nodo_expresion.get("id")
            if hasattr(self.tabla_simbolos, 'buscar_variable_extendida'):
                variable = self.tabla_simbolos.buscar_variable_extendida(nombre)
                if variable:
                    variable.contador_referencias += 1
                    print(f"DEBUG: Referencia en expresión a '{nombre}' - contador: {variable.contador_referencias}")

        # Recursivamente procesar subexpresiones
        if "izq" in nodo_expresion:
            self._incrementar_referencias_en_expresion(nodo_expresion["izq"])
        if "der" in nodo_expresion:
            self._incrementar_referencias_en_expresion(nodo_expresion["der"])
        if "valor" in nodo_expresion and isinstance(nodo_expresion["valor"], dict):
            self._incrementar_referencias_en_expresion(nodo_expresion["valor"])

    def factor(self):
        tok = self.actual()

        # Literales numéricos
        if tok["tipo"] == "ENTERO_LIT":
            self.match("ENTERO_LIT")
            return {"nodo": "LIT_INT", "valor": int(tok["token"])}

        if tok["tipo"] == "FLOTANTE_LIT":
            self.match("FLOTANTE_LIT")
            return {"nodo": "LIT_FLOAT", "valor": float(tok["token"])}

        if tok["tipo"] == "CADENA_LIT":
            self.match("CADENA_LIT")
            return {"nodo": "LIT_STR", "valor": tok["token"].strip('"')}

        if tok["tipo"] == "CARACTER_LIT":
            self.match("CARACTER_LIT")
            valor_caracter = tok["token"].strip("'") if "'" in tok["token"] else tok["token"]
            return {"nodo": "LIT_CHAR", "valor": valor_caracter}

        if tok["tipo"] == "BOOLEANO_LIT":
            self.match("BOOLEANO_LIT")
            valor_lower = tok["token"].lower()
            valor_bool = valor_lower in ("verdadero", "true")
            return {"nodo": "LIT_BOOL", "valor": valor_bool}

        # Identificador o llamada a función
        if tok["tipo"] == "IDENTIFICADOR":
            nombre = tok["token"]
            self.match("IDENTIFICADOR")

            # ✅ INCREMENTAR CONTADOR DE REFERENCIAS
            if hasattr(self.tabla_simbolos, 'buscar_variable_extendida'):
                variable = self.tabla_simbolos.buscar_variable_extendida(nombre)
                if variable:
                    variable.contador_referencias += 1
                    print(f"DEBUG: Referencia a '{nombre}' - contador: {variable.contador_referencias}")

            # Si sigue un paréntesis, es una llamada a función
            if self.check("PAREN_IZQ"):
                self.match("PAREN_IZQ")
                argumentos = []

                if not self.check("PAREN_DER"):
                    argumentos.append(self.expresion())
                    while self.check("COMA"):
                        self.match("COMA")
                        argumentos.append(self.expresion())

                self.match("PAREN_DER")
                return {"nodo": "LLAMADA_FUNCION", "id": nombre, "args": argumentos}

            # Si no hay paréntesis, es solo una variable
            return {"nodo": "VAR", "id": nombre}

        # En el método factor(), añade después del caso de identificador:
        if tok["tipo"] == "NUEVO":
            self.match("NUEVO")
            clase = self.match("IDENTIFICADOR")["token"]
            self.match("PAREN_IZQ")
            args = []
            if self.actual()["tipo"] != "PAREN_DER":
                args.append(self.expresion())
                while self.actual()["tipo"] == "COMA":
                    self.match("COMA")
                    args.append(self.expresion())
            self.match("PAREN_DER")
            return {"nodo": "NUEVO", "clase": clase, "args": args}

        # Expresión entre paréntesis
        if tok["tipo"] == "PAREN_IZQ":
            self.match("PAREN_IZQ")
            nodo = self.expresion()
            self.match("PAREN_DER")
            return nodo

        # Si nada coincide
        raise ParserError(f"Factor inválido en línea {tok['linea']}: {tok['token']}")


    # -------------------------------------------------------

    def buscar_nodo(self, nodo):
            pass
        
    def _procesar_referencias_en_expresion(self, nodo):
        """Recorre una expresión e incrementa contadores de variables usadas - CORREGIDO"""
        if not isinstance(nodo, dict):
            return

        tipo_nodo = nodo.get("nodo")
        print(f"DEBUG: Procesando nodo: {tipo_nodo}")
        print("nodo completo:  ", nodo)


                
        if nodo.get("nodo") == "BIN_OP":
            lado_izq = nodo.get("izq")
            lado_izq = lado_izq.get("nodo")
            lado_der= nodo.get("der")
            lado_der= lado_der.get("nodo")
            
            if lado_izq == "VAR":
                nombre = nodo.get("izq").get("id")
                lado_izq = self.tabla_simbolos.buscar(nombre)
                if not lado_izq:
                    self.reporte.agregar_error(CategoriaError.DECLARACION, f"Variable '{nombre}' no declarada", self.actual()['linea'])
                    return
                lado_izq = lado_izq.get("tipo_dato")
            if lado_der == "VAR":   
                nombre = nodo.get("der").get("id")
                lado_der = self.tabla_simbolos.buscar(nombre)
                if not lado_der:
                    self.reporte.agregar_error(CategoriaError.DECLARACION, f"Variable '{nombre}' no declarada", self.actual()['linea'])
                    return
                lado_der = lado_der.get("tipo_dato")

            self.verificador_tipos.verificar_compatibilidad(lado_izq, lado_der, nodo.get("op"), self.actual()['linea'])

          # Si es una variable, incrementar contador
        if tipo_nodo == "VAR":
            nombre = nodo.get("id")
            #en el caso de que la variable sea un parametro local, no se incrementa el contador
            if self.tabla_simbolos.buscar(nombre):
                posibleParametro = self.tabla_simbolos.buscar(nombre)
                print("posible parametro: ", posibleParametro.get("categoria"))
                if posibleParametro.get("categoria") == "parametro" and posibleParametro.get("estado") != "declarado":
                    print(f"DEBUG: La variable '{nombre}' es un parámetro local, no se incrementa el contador.")
                    pass# No incrementar contador para parámetros locales
                
                elif posibleParametro.get("valor") == None:
                    self.validador_inicializacion.verificar_variable_no_inicializada(nombre, self.actual()['linea'])
                    pass# No incrementar contador para parámetros no inicializados
                    
            elif hasattr(self.tabla_simbolos, 'buscar_variable_extendida'):
                variable = self.tabla_simbolos.buscar_variable_extendida(nombre)
                if variable:
                    #variable.contador_referencias += 1
                    print(f"DEBUG: ✅ Referencia a '{nombre}' - contador: {variable.contador_referencias}")

                    # CORRECCIÓN: Sincronizar con estructura antigua
                    #simbolo_antiguo = self.tabla_simbolos.buscar(nombre)
                    #if simbolo_antiguo:
                    #    if "contador_referencias" not in simbolo_antiguo:
                    #        simbolo_antiguo["contador_referencias"] = 0
                    #    simbolo_antiguo["contador_referencias"] += 1
                else:
                    print(f"DEBUG: Variable '{nombre}' no encontrada en tabla extendida")
                    print("hola")
                    self.reporte.agregar_error(CategoriaError.DECLARACION, f"Variable '{nombre}' no declarada", self.actual()['linea'])

        elif tipo_nodo == "LLAMADA_FUNCION":
            nombre_funcion = nodo.get("id")
            print(f"DEBUG:  Validando llamada a función '{nombre_funcion}' en expresión")

            # Validar que la función existe
            if hasattr(self.tabla_simbolos, 'buscar'):
                funcion = self.tabla_simbolos.buscar(nombre_funcion)
                if not funcion or funcion.get('categoria') != 'funcion':
                    print(f"DEBUG:  Función '{nombre_funcion}' no encontrada en tabla de símbolos")
                    self.reporte.agregar_error(CategoriaError.DECLARACION, f"Función '{nombre_funcion}' no declarada", self.actual()['linea'])
                else:
                    print(f"DEBUG:  Función '{nombre_funcion}' encontrada en tabla de símbolos")
        # Procesar recursivamente subexpresiones
        if "izq" in nodo:
            self._procesar_referencias_en_expresion(nodo["izq"])
        if "der" in nodo:
            self._procesar_referencias_en_expresion(nodo["der"])
        if "valor" in nodo and isinstance(nodo["valor"], dict):
            self._procesar_referencias_en_expresion(nodo["valor"])
        if "cond" in nodo and isinstance(nodo["cond"], dict):
            self._procesar_referencias_en_expresion(nodo["cond"])
        if "args" in nodo:
            for arg in nodo["args"]:
                if isinstance(arg, dict):
                    self._procesar_referencias_en_expresion(arg)

    # -------------------------------------------------------
    # DEFINICION DE CLASES
    # -------------------------------------------------------

    def declaracion_clase(self):
        self.match("CLASE")
        token_nombre = self.match("IDENTIFICADOR")
        nombre = token_nombre["token"]
        linea = token_nombre["linea"]

        base = None
        if self.actual()["tipo"] == "HEREDA":
            self.match("HEREDA")
            base = self.match("IDENTIFICADOR")["token"]

        self.match("LLAVE_IZQ")

        # Entrar al ámbito de clase
        self.tabla_simbolos.entrar_ambito(f"clase:{nombre}")

        atributos = []
        metodos = []

        while self.actual()["tipo"] != "LLAVE_DER" and self.actual()["tipo"] != "EOF":
            # Reconocer tanto atributos como métodos
            if self.actual()["tipo"] in (
                    "TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER",
                    "TIPO_CADENA", "TIPO_VACIO"):

                # Mirar adelante para determinar si es método o atributo
                if self.i + 2 < len(self.tokens):
                    sig1 = self.tokens[self.i + 1]["tipo"]
                    sig2 = self.tokens[self.i + 2]["tipo"]

                    if sig1 == "IDENTIFICADOR" and sig2 == "PAREN_IZQ":
                        metodos.append(self.metodo_de_clase())
                    else:
                        atributos.append(self.declaracion_variable())
                else:
                    atributos.append(self.declaracion_variable())
            else:
                self.error(f"Token inesperado dentro de la clase: {self.actual()['token']}")

        self.match("LLAVE_DER")
        self.tabla_simbolos.salir_ambito()

        simbolo = {
            "identificador": nombre,
            "categoria": "clase",
            "tipo_dato": "-",
            "linea": linea,
            "ambito": "Global",
            "direccion": None,
            "valor": f"Hereda: {base}" if base else "Clase base",
            "estado": "definida",
            "estructura": "Clase",
            "contador_referencias": 0
        }
        self.tabla_simbolos.insertar(simbolo)

        return {"nodo": "CLASE", "nombre": nombre, "base": base, "atributos": atributos, "metodos": metodos}


    def metodo_de_clase(self):
        # Tipo de retorno
        tipo_token = self.match_multiple(
            "TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_CADENA", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_VACIO"
        )
        if tipo_token is None:
            self.error("Se esperaba un tipo de dato en la declaración del método")
        tipo = tipo_token["token"]

        # Nombre del método
        nombre = self.match("IDENTIFICADOR")["token"]

        # Parámetros
        self.match("PAREN_IZQ")
        params = self.parametros()
        self.match("PAREN_DER")

        # Cuerpo del método
        cuerpo = self.bloque()

        return {
            "nodo": "METODO",
            "nombre": nombre,
            "tipo": tipo,
            "params": params,
            "cuerpo": cuerpo
        }

    # -------------------------------------------------------
    # FUNCIONES
    # -------------------------------------------------------

    def declaracion_funcion(self):
        tipo_token = self.match(self.actual()["tipo"])
        tipo = tipo_token["token"] if tipo_token else "TIPO_VACIO"
        linea = tipo_token["linea"] if tipo_token else self.actual()["linea"]
        
        nombre_token = self.match("IDENTIFICADOR")
        if not nombre_token:
            self.error("Se esperaba nombre de función")
            return None
        nombre = nombre_token["token"]

        self.match("PAREN_IZQ")
        parametros = []

        if self.actual()["tipo"] != "PAREN_DER":
            while True:
                tipo_param_token = self.match_multiple("TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_CADENA")
                if not tipo_param_token:
                    self.error("Tipo de parámetro inválido")
                    break
                    
                tipo_param = tipo_param_token["token"]
                nombre_param_token = self.match("IDENTIFICADOR")
                if not nombre_param_token:
                    self.error("Se esperaba nombre de parámetro")
                    break
                    
                nombre_param = nombre_param_token["token"]
                parametros.append((tipo_param, nombre_param))
                
                if self.actual()["tipo"] != "COMA":
                    break
                self.match("COMA")

        self.match("PAREN_DER")

        # CORRECCIÓN: Insertar función SOLO UNA VEZ
        # Verificar si ya existe antes de insertar
        funcion_existente = self.tabla_simbolos.buscar(nombre)
        if not funcion_existente:
            simbolo_funcion = {
                "identificador": nombre,
                "categoria": "funcion",
                "tipo_dato": tipo,
                "parametros": parametros,
                "linea": linea,
                "ambito": "Global",
                "direccion": self.tabla_simbolos.obtener_direccion(),
                "valor": None,
                "retornar": True,
                "estado": "declarada",
                "estructura": "Funcion",
                "contador_referencias": 0
            }
            try:
                self.tabla_simbolos.insertar(simbolo_funcion)
                print(f"DEBUG: Insertada función '{nombre}' en tabla de símbolos")
            except Exception as e:
                print(f"Error al insertar función {nombre}: {e}")

        # Entrar al ámbito de la función
        self.tabla_simbolos.entrar_ambito(f"funcion:{nombre}")

        # CORRECCIÓN: Insertar parámetros SOLO si no existen
        for tipo_param, nombre_param in parametros:
            param_existente = self.tabla_simbolos.buscar_en_ambito_actual(nombre_param)
            if not param_existente:
                simbolo_param = {
                    "identificador": nombre_param,
                    "categoria": "parametro",
                    "tipo_dato": tipo_param,
                    "linea": linea,
                    "ambito": self.tabla_simbolos.ambito_actual(),
                    "direccion": self.tabla_simbolos.obtener_direccion(),
                    "valor": None,
                    "retornar": True,
                    "estado": "declarado",
                    "estructura": None,
                    "contador_referencias": 0
                }
                try:
                    self.tabla_simbolos.insertar(simbolo_param)
                    print(f"DEBUG: Insertado parámetro '{nombre_param}' en ámbito de función")
                except Exception as e:
                    print(f"Error al insertar parámetro {nombre_param}: {e}")

        # Parsear cuerpo de la función
        bloque_func = self.bloque()

        # Salir del ámbito
        self.tabla_simbolos.salir_ambito()

        # CORRECCIÓN: ELIMINAR la segunda inserción de función que estaba aquí
        return {
            "nodo": "FUNCION", 
            "nombre": nombre, 
            "tipo": tipo, 
            "params": parametros, 
            "cuerpo": bloque_func,
            "linea": linea
        }
        
    def parametros(self):
        params = []
        if self.actual()["tipo"] in ("TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_CADENA"):
            while True:
                tipo = self.match(self.actual()["tipo"])["token"]
                nombre = self.match("IDENTIFICADOR")["token"]
                params.append((tipo, nombre))
                if self.actual()["tipo"] != "COMA":
                    break
                self.match("COMA")
        return params
    
    def llamada_funcion(self):
        nombre = self.match("IDENTIFICADOR")["token"]
        # CORREGIR: Incrementar contador de llamadas a función
        if hasattr(self.tabla_simbolos, 'buscar_funcion_extendida'):
            funcion = self.tabla_simbolos.buscar_funcion_extendida(nombre)
            if funcion:
                funcion.contador_llamadas += 1
                print(f"DEBUG: Llamada a función '{nombre}' - contador: {funcion.contador_llamadas}")

        self.match("PAREN_IZQ")
        args = []

        if self.actual()["tipo"] != "PAREN_DER":
            args.append(self.expresion())
            while self.actual()["tipo"] == "COMA":
                self.match("COMA")
                args.append(self.expresion())

        self.match("PAREN_DER")

        return {"nodo": "LLAMADA_FUNCION", "nombre": nombre, "args": args}

    #Manejo de errores
    
    def manejo_errores(self):
        self.match("INTENTAR")
        try_bloque = self.bloque()

        self.match("CAPTURAR")
        self.match("PAREN_IZQ")
        error_var = self.match("IDENTIFICADOR")["token"]
        self.match("PAREN_DER")

        catch_bloque = self.bloque()

        return {
            "nodo": "INTENTAR",
            "try": try_bloque,
            "error_var": error_var,
            "catch": catch_bloque
        }

    # -------------------------------------------------------
    # DEFINICION DE INTERFAZ
    # -------------------------------------------------------
    def declaracion_interfaz(self):
        self.match("INTERFAZ")
        token_nombre = self.match("IDENTIFICADOR")
        nombre = token_nombre["token"]
        linea = token_nombre["linea"]

        self.match("LLAVE_IZQ")
        metodos = []

        while self.actual()["tipo"] != "LLAVE_DER" and self.actual()["tipo"] != "EOF":
            if self.actual()["tipo"] in (
                "TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO",
                "TIPO_CARACTER", "TIPO_CADENA", "TIPO_VACIO"
            ):
                metodos.append(self.metodo_interfaz())
            else:
                self.error(f"Token inesperado dentro de la interfaz: {self.actual()['token']}")

        self.match("LLAVE_DER")

        simbolo = {
            "identificador": nombre,
            "categoria": "interfaz",
            "tipo_dato": "-",
            "linea": linea,
            "ambito": "Global",
            "valor": "Interfaz definida",
            "estado": "definida",
            "estructura": "Interfaz"
        }
        self.tabla_simbolos.insertar(simbolo)

        return {"nodo": "INTERFAZ", "nombre": nombre, "metodos": metodos}


    def metodo_interfaz(self):
        tipo = self.match(self.actual()["tipo"])["token"]
        nombre = self.match("IDENTIFICADOR")["token"]

        self.match("PAREN_IZQ")
        parametros = []
        if self.actual()["tipo"] != "PAREN_DER":
            while True:
                tipo_param = self.match(self.actual()["tipo"])["token"]
                id_token = self.match("IDENTIFICADOR")
                id_param = id_token["token"]
                parametros.append((tipo_param, id_param))
                if self.actual()["tipo"] != "COMA":
                    break
                self.match("COMA")
        self.match("PAREN_DER")

        # Permitir métodos sin cuerpo (terminados en ;)
        if self.check("PUNTO_Y_COMA"):
            self.match("PUNTO_Y_COMA")
            return {"nodo": "METODO_INTERFAZ", "nombre": nombre, "tipo": tipo, "params": parametros}

        # Si no hay punto y coma, intentar leer un bloque (aunque no es usual en interfaz)
        cuerpo = []
        if self.check("LLAVE_IZQ"):
            cuerpo = self.bloque()

        return {"nodo": "METODO_INTERFAZ", "nombre": nombre, "tipo": tipo, "params": parametros, "cuerpo": cuerpo}
