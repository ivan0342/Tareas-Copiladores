# archivo: interprete.py

from tabla_simbolos import tabla

class RuntimeErrorInterp(Exception):
    pass

class ReturnSignal(Exception):
    def __init__(self, valor):
        self.valor = valor

class Interprete:
    def __init__(self, output=print):
        self.memoria = {}
        self.output = output
        self.funciones = {}
        self.clases = {}

        # Inicializar memoria con variables globales
        for simbolo in tabla.obtener_todos():
            if simbolo.get("categoria") == "variable" and simbolo.get("ambito") == "Global":
                self.memoria[simbolo["identificador"]] = simbolo.get("valor")


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
            # Buscar en memoria local
            if name in self.memoria:
                return self.memoria[name]

            # Buscar en la tabla de símbolos global si no está en memoria
            simbolo = tabla.buscar(name)
            if simbolo:
                return simbolo.get("Valor") or simbolo.get("valor")

            # Si no está en ninguno, error
            raise RuntimeErrorInterp(f"Símbolo '{name}' no encontrado en la tabla.")

        if tipo == "NUEVO":
            return self.crear_objeto(nodo["clase"], nodo["args"])

        if tipo == "FUNCION":
            nombre = nodo["nombre"]
            self.funciones[nombre] = nodo
            return None

        if tipo == "RETORNAR":
            valor = self.ejecutar(nodo["valor"])
            raise ReturnSignal(valor)

        if tipo == "CLASE":
            nombre = nodo["nombre"]
            self.clases[nombre] = nodo
            return None

        if tipo == "LLAMADA_METODO":
            obj = self.memoria[nodo["obj"]]
            clase = self.clases[obj["__clase__"]]
            metodo = clase["metodos"][nodo["metodo"]]
            args = [obj] + [self.ejecutar(a) for a in nodo["args"]]
            return self.llamar_funcion(metodo["nombre"], args)
        
        if tipo == "MANEJO_ERRORES":
            try:
                self.ejecutar(nodo["intento"])
            except RuntimeErrorInterp as e:
                # Crear variable del error en memoria
                error_var = nodo["error"]["token"] if isinstance(nodo["error"], dict) else nodo["error"]
                self.memoria[error_var] = str(e)
                self.ejecutar(nodo["captura"])
            return None


    def llamar_funcion(self, nombre, args_nodos):
        if nombre not in self.funciones:
            raise RuntimeErrorInterp(f"Función no declarada: {nombre}")

        funcion = self.funciones[nombre]

        # Creamos un nuevo entorno local
        entorno_anterior = self.memoria
        self.memoria = self.memoria.copy()

        # Pasar parámetros
        parametros = funcion["params"]
        args = [self.ejecutar(a) for a in args_nodos]

        for (tipo, id_param), valor in zip(parametros, args):
            self.memoria[id_param] = valor

        try:
            self.ejecutar(funcion["cuerpo"])
        except ReturnSignal as r:
            resultado = r.valor
        else:
            resultado = None

        # Restaurar entorno
        self.memoria = entorno_anterior
        return resultado

    def crear_objeto(self, nombre_clase, args):
        if nombre_clase not in self.clases:
            raise RuntimeErrorInterp(f"Clase '{nombre_clase}' no declarada")

        clase = self.clases[nombre_clase]

        # Crear instancia
        obj = {"__clase__": nombre_clase}

        # Inicializar atributos
        for attr in clase["atributos"]:
            obj[attr["id"]] = None

        # Llamar constructor si existe
        if nombre_clase in self.funciones:
            self.llamar_funcion(nombre_clase, [obj] + [self.ejecutar(a) for a in args])

        return obj
