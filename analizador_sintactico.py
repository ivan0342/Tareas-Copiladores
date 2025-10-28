import tkinter as tk
from tkinter import ttk, messagebox
from analizador_lexico import AnalizadorLexico
from tabla_simbolos import TablaSimbolos


class AnalizadorSintactico:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.errores_sintacticos = []

    def analizar(self, tokens):
        indice = 0
        while indice < len(tokens):
            tok = tokens[indice]

            # Declaración de variable
            if tok["token"] in ["entero", "flotante", "cadena", "booleano"]:
                tipo_actual = tok["token"]
                indice += 1
                if indice < len(tokens):
                    sig = tokens[indice]
                    if sig["tipo"] == "Identificador":
                        simbolo = self.tabla_simbolos.buscar_simbolo(sig["token"])
                        if simbolo:
                            simbolo["tipo_dato"] = tipo_actual
                            simbolo["estado"] = "declarado"
                        else:
                            self.tabla_simbolos.insertar_simbolo({
                                "identificador": sig["token"],
                                "categoria": "Identificador",
                                "tipo_dato": tipo_actual,
                                "ambito": "global",
                                "linea": sig["linea"],
                                "valor": None,
                                "estado": "declarado",
                                "estructura": None,
                                "contador_referencias": 0
                            })
                        indice += 1
                        # Asignación opcional
                        if indice < len(tokens) and tokens[indice]["token"] == "=":
                            indice += 1
                            if indice < len(tokens):
                                valor_tok = tokens[indice]
                                simbolo = self.tabla_simbolos.buscar_simbolo(sig["token"])
                                simbolo["valor"] = valor_tok["token"]
                                simbolo["estado"] = "inicializado"
                                simbolo["contador_referencias"] += 1
                                indice += 1
                        # ; obligatorio
                        if indice < len(tokens) and tokens[indice]["token"] == ";":
                            indice += 1
                        else:
                            self.errores_sintacticos.append(
                                f"Error sintáctico en línea {sig['linea']}: se esperaba ';'"
                            )
                    else:
                        self.errores_sintacticos.append(
                            f"Error sintáctico en línea {sig['linea']}: se esperaba un identificador"
                        )
                continue

            # Asignación fuera de declaración
            elif tok["tipo"] == "Identificador":
                simbolo = self.tabla_simbolos.buscar_simbolo(tok["token"])
                if simbolo:
                    indice_siguiente = indice + 1
                    if indice_siguiente < len(tokens) and tokens[indice_siguiente]["token"] == "=":
                        indice_siguiente += 1
                        if indice_siguiente < len(tokens):
                            valor_tok = tokens[indice_siguiente]
                            simbolo["valor"] = valor_tok["token"]
                            simbolo["estado"] = "inicializado"
                            simbolo["contador_referencias"] += 1
                            indice = indice_siguiente + 1
                            continue
                indice += 1
            else:
                indice += 1

        return self.errores_sintacticos


