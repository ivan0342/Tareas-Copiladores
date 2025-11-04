# archivo: interprete.py

from tabla_simbolos import tabla

class RuntimeErrorInterp(Exception):
    pass

class Interprete:
    def __init__(self, output=print):
        self.memoria = {}
        self.output = output

    def ejecutar_programa(self, ast):
        resultado = None
        for nodo in ast:
            resultado = self.ejecutar(nodo)
        return resultado

    def ejecutar(self, nodo):
        tipo = nodo.get("nodo")

        # -------------------------
        # DECLARACIONES Y ASIGNACIÓN
        # -------------------------
        if tipo == "DECL_VAR":
            val = None
            if nodo.get("valor") is not None:
                val = self.ejecutar(nodo["valor"])
            self.memoria[nodo["id"]] = val
            tabla.actualizar(nodo["id"], val)  # ✅
            return None


        if tipo == "ASIGNACION":
            val = self.ejecutar(nodo["valor"])
            if nodo["id"] not in self.memoria:
                raise RuntimeErrorInterp(
                    f"Variable no declarada: {nodo['id']} (línea {nodo.get('linea')})"
                )
            self.memoria[nodo["id"]] = val
            return val

        # -------------------------
        # IMPRIMIR
        # -------------------------
        if tipo == "IMPRIMIR":
            v = self.ejecutar(nodo["valor"])
            self.output(v)
            return None

        # -------------------------
        # CONDICIONAL
        # -------------------------
        if tipo == "SI":
            cond = self.ejecutar(nodo["cond"])
            if cond:
                return self.ejecutar(nodo["then"])
            elif nodo.get("else"):
                return self.ejecutar(nodo["else"])
            return None

        # -------------------------
        # BUCLE MIENTRAS
        # -------------------------
        if tipo == "MIENTRAS":
            while self.ejecutar(nodo["cond"]):
                self.ejecutar(nodo["cuerpo"])
            return None

        # -------------------------
        # BLOQUE
        # -------------------------
        if tipo == "BLOQUE":
            for s in nodo["sentencias"]:
                self.ejecutar(s)
            return None

        # -------------------------
        # LITERALES Y VARIABLES
        # -------------------------
        if tipo in ["LIT_INT", "LIT_FLOAT", "LIT_STR"]:
            return nodo["valor"]

        if tipo == "VAR":
            name = nodo["id"]
            if name not in self.memoria:
                raise RuntimeErrorInterp(f"Variable no declarada: {name}")
            return self.memoria[name]