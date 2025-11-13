from tabla_simbolos import TablaSimbolos

class ParserError(Exception):
    pass

class Parser:
    def __init__(self, tokens, tabla_simbolos):
        self.tokens = tokens
        self.i = 0
        self.errores = []
        self.tabla_simbolos = tabla_simbolos
        self.ast = []  # árbol sintáctico abstracto

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
                print(
                    f"[Error sintáctico] Se esperaba '{tipo_esperado}', pero se encontró '{actual['tipo']}' en línea {actual['linea']}")
            else:
                print(f"[Error sintáctico] Se esperaba '{tipo_esperado}', pero se llegó al final del archivo.")
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
        return self.ast



    # -------------------------------------------------------
    # DECISIONES PRINCIPALES
    # -------------------------------------------------------
    def declaracion_o_sentencia(self):
        actual = self.actual()
        tipo = actual["tipo"]

        # --- Declaración de función o variable ---
        if tipo in ("TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_CADENA", "VACIO"):
            # Verificar que haya tokens siguientes
            if self.i + 2 < len(self.tokens):
                sig1 = self.tokens[self.i + 1]["tipo"]
                sig2 = self.tokens[self.i + 2]["tipo"]

                # Si viene IDENTIFICADOR + PAREN_IZQ -> es función
                if sig1 == "IDENTIFICADOR" and sig2 == "PAREN_IZQ":
                    return self.declaracion_funcion()
                else:
                    return self.declaracion_variable()
            else:
                return self.declaracion_variable()

        # --- Clase ---
        elif tipo == "CLASE":
            return self.declaracion_clase()

        # --- Condicional ---
        elif tipo == "SI":
            return self.condicional()

        # --- Bucle ---
        elif tipo == "MIENTRAS":
            return self.bucle_mientras()

        # --- Imprimir ---
        elif tipo == "IMPRIMIR":
            return self.imprimir_sentencia()

        # --- Bloque ---
        elif tipo == "LLAVE_IZQ":
            return self.bloque()

        # --- Asignación o llamada ---
        elif tipo == "IDENTIFICADOR":
            return self.asignacion()
    
        # --- Caso por defecto ---
        else:
            self.errores.append(
                f"Token inesperado '{actual['tipo']}' en línea {actual['linea']}"
            )
            self.i += 1
            return None

    # -------------------------------------------------------
    # DECLARACIÓN DE VARIABLES
    # -------------------------------------------------------
    def declaracion_variable(self):
        tipo_token = self.match(self.actual()["tipo"])
        tipo = tipo_token["token"] if tipo_token else "desconocido"

        if self.actual()["tipo"] == "IDENTIFICADOR":
            nombre = self.match("IDENTIFICADOR")["token"]
            linea = self.actual()["linea"]
            valor = None

            if self.actual()["tipo"] == "ASIGNACION":
                self.match("ASIGNACION")
                valor = self.expresion()

            self.match("PUNTO_Y_COMA")

            simbolo = {
                "identificador": nombre,
                "categoria": "variable",
                "tipo_dato": tipo,
                "linea": linea,
                "ambito": "Global",
                "direccion": self.tabla_simbolos.direccion_actual,
                "valor": valor,
                "estado": "inicializado" if valor else "declarado",
                "estructura": "-",
                "contador_referencias": 1
            }
            self.tabla_simbolos.insertar(simbolo)

            return {"nodo": "DECL_VAR", "tipo": tipo, "id": nombre, "valor": valor, "linea": linea}
        else:
            self.errores.append("Error: se esperaba un identificador en la declaración de variable.")
            return None

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
                self.errores.append(f"Variable '{nombre}' no declarada.")

            return {"nodo": "ASIGNACION", "id": nombre, "valor": valor, "linea": self.actual()["linea"]}
        else:
            self.errores.append(f"Error: se esperaba '=' después de {nombre}")
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

    # -------------------------------------------------------
    # BUCLE MIENTRAS
    # -------------------------------------------------------
    def bucle_mientras(self):
        self.match("MIENTRAS")
        self.match("PAREN_IZQ")
        cond = self.expresion()
        self.match("PAREN_DER")
        cuerpo = self.bloque()
        return {"nodo": "MIENTRAS", "cond": cond, "cuerpo": cuerpo}

    # -------------------------------------------------------
    # IMPRIMIR
    # -------------------------------------------------------
    def imprimir_sentencia(self):
        self.match("IMPRIMIR")
        self.match("PAREN_IZQ")
        expr = self.expresion()
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
        return nodo

    def exp_mul(self):
        nodo = self.factor()
        while self.actual()["tipo"] in ("MULT", "DIV", "MOD"):
            op = self.match(self.actual()["tipo"])
            rhs = self.factor()
            nodo = {"nodo": "BIN_OP", "op": op["tipo"], "izq": nodo, "der": rhs}
        return nodo

    def factor(self):
        tok = self.actual()
        if tok["tipo"] == "ENTERO_LIT":
            self.match("ENTERO_LIT")
            return {"nodo": "LIT_INT", "valor": int(tok["token"])}
        if tok["tipo"] == "FLOTANTE_LIT":
            self.match("FLOTANTE_LIT")
            return {"nodo": "LIT_FLOAT", "valor": float(tok["token"])}
        if tok["tipo"] == "CADENA_LIT":
            self.match("CADENA_LIT")
            return {"nodo": "LIT_STR", "valor": tok["token"].strip('"')}
        if tok["tipo"] == "BOOLEANO_LIT":
            self.match("BOOLEANO_LIT")
            return {"nodo": "LIT_BOOL", "valor": tok["token"] == "true"}
        if tok["tipo"] == "IDENTIFICADOR":
            self.match("IDENTIFICADOR")
            return {"nodo": "VAR", "id": tok["token"]}
        if tok["tipo"] == "PAREN_IZQ":
            self.match("PAREN_IZQ")
            nodo = self.expresion()
            self.match("PAREN_DER")
            return nodo
        raise ParserError(f"Factor inválido en línea {tok['linea']}: {tok['token']}")

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

        while self.actual()["tipo"] != "LLAVE_DER":
            if self.actual()["tipo"] in (
                "TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_CADENA"):
                if (self.tokens[self.i + 1]["tipo"] == "IDENTIFICADOR"
                        and self.tokens[self.i + 2]["tipo"] == "PAREN_IZQ"):
                    metodos.append(self.metodo_de_clase())
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
            "TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_CADENA", "TIPO_BOOLEANO", "TIPO_CARACTER"
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
        tipo = self.match(self.actual()["tipo"])["token"]  # tipo retorno
        nombre = self.match("IDENTIFICADOR")["token"]

        self.match("PAREN_IZQ")
        parametros = []

        if self.actual()["tipo"] != "PAREN_DER":
            while True:
                tipo_param = self.match(self.actual()["tipo"])["token"]
                id_token = self.match("IDENTIFICADOR")
                if id_token is None:
                    self.error("Se esperaba un identificador en los parámetros de la función")
                    return None
                id_param = id_token["token"]

                parametros.append((tipo_param, id_param))
                if self.actual()["tipo"] != "COMA":
                    break
                self.match("COMA")

        self.match("PAREN_DER")

        # Entrar ámbito función
        self.tabla_simbolos.entrar_ambito(f"func:{nombre}")

        for tipo_param, id_param in parametros:
            self.tabla_simbolos.insertar({
                "identificador": id_param,
                "categoria": "parámetro",
                "tipo_dato": tipo_param,
                "estado": "inicializado",
                "ambito": self.tabla_simbolos.ambito_actual(),
                "valor": None
            })

        bloque_func = self.bloque()

        self.tabla_simbolos.salir_ambito()

        simbolo = {
            "identificador": nombre,
            "categoria": "función",
            "tipo_dato": tipo,
            "valor": parametros,
            "estado": "definida",
            "ambito": "Global",
            "estructura": "Función"
        }
        self.tabla_simbolos.insertar(simbolo)

        return {"nodo": "FUNCION", "nombre": nombre, "params": parametros, "cuerpo": bloque_func}

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