from tabla_simbolos import TablaSimbolos

class Parser:
    def __init__(self, tokens, tabla_simbolos):
        self.tokens = tokens
        self.i = 0
        self.errores = []
        self.tabla_simbolos = tabla_simbolos  # Usa la misma tabla compartida

    def actual(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return ("EOF", "")

    def consumir(self, tipo):
        if self.actual()[0] == tipo:
            self.i += 1
        else:
            self.errores.append(
                f"Error sintáctico: se esperaba {tipo} pero se encontró {self.actual()[0]}"
            )

    def parse(self):
        while self.actual()[0] != "EOF":
            self.declaracion()
        return self.errores

    def declaracion(self):
        if self.actual()[0] == "TIPO_DATO":
            self.declaracion_variable()
        elif self.actual()[0] == "IDENTIFICADOR":
            self.asignacion()
        else:
            self.errores.append(
                f"Error sintáctico: token inesperado {self.actual()[0]}"
            )
            self.i += 1

    def declaracion_variable(self):
        tipo = self.actual()[1]
        self.consumir("TIPO_DATO")

        if self.actual()[0] == "IDENTIFICADOR":
            nombre = self.actual()[1]
            linea = self.i + 1
            self.consumir("IDENTIFICADOR")

            valor = None
            if self.actual()[0] == "ASIGNACION":
                self.consumir("ASIGNACION")
                valor = self.expresion()

            self.consumir("PUNTO_COMA")

            # Insertar en la tabla de símbolos
            self.tabla_simbolos.insertar({
                "Identificador": nombre,
                "Categoría": "Variable",
                "Tipo de dato": tipo,
                "Línea": linea,
                "Ámbito": "Global",
                "Dirección": self.tabla_simbolos.obtener_direccion(),
                "Valor": valor,
                "Estado": "Inicializado" if valor else "Declarado",
                "Estructura": "-",
                "Contador de referencias": 1
            })
        else:
            self.errores.append("Error sintáctico: se esperaba un identificador.")

    def asignacion(self):
        nombre = self.actual()[1]
        self.consumir("IDENTIFICADOR")

        if self.actual()[0] == "ASIGNACION":
            self.consumir("ASIGNACION")
            valor = self.expresion()
            self.consumir("PUNTO_COMA")

            # Actualizar valor si la variable existe
            simbolo = self.tabla_simbolos.buscar(nombre)
            if simbolo:
                self.tabla_simbolos.actualizar(nombre, "Valor", valor)
                self.tabla_simbolos.actualizar(nombre, "Estado", "Actualizado")
            else:
                self.errores.append(f"Variable '{nombre}' no declarada.")
        else:
            self.errores.append("Error sintáctico: se esperaba '='.")

    def expresion(self):
        # Simplificación: solo acepta números, cadenas o identificadores
        if self.actual()[0] in ["NUMERO", "CADENA", "IDENTIFICADOR"]:
            valor = self.actual()[1]
            self.consumir(self.actual()[0])
            return valor
        else:
            self.errores.append("Error en expresión: se esperaba un valor.")
            return None
