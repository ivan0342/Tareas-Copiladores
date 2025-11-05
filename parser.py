# archivo: parser.py
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

    def actual(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        else:
            return {"tipo": "EOF", "token": "EOF", "linea": -1, "columna": -1}

    def match(self, tipo_esperado):
        tok = self.actual()
        if tok["tipo"] == tipo_esperado:
            self.i += 1
            return tok
        else:
            self.errores.append(
                f"Error sintáctico en línea {tok['linea']}: se esperaba {tipo_esperado}, se encontró {tok['tipo']} ('{tok['token']}')"
            )
            self.i += 1
            return None

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
        tipo = self.actual()["tipo"]
        if tipo in ("TIPO_ENTERO", "TIPO_FLOTANTE", "TIPO_BOOLEANO", "TIPO_CARACTER", "TIPO_CADENA"):
            return self.declaracion_variable()
        elif tipo == "IDENTIFICADOR":
            return self.asignacion()
        elif tipo == "SI":
            return self.condicional()
        elif tipo == "MIENTRAS":
            return self.bucle_mientras()
        elif tipo == "IMPRIMIR":
            return self.imprimir_sentencia()
        elif tipo == "LLAVE_IZQ":
            return self.bloque()
        else:
            self.errores.append(f"Token inesperado '{self.actual()['tipo']}' en línea {self.actual()['linea']}")
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
