# archivo: interprete.py

from tabla_simbolos import tabla


class RuntimeErrorInterp(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, valor):
        self.valor = valor


class Interprete:
    def __init__(self, output=print, tabla_simbolos=None):
        self.memoria = {}
        self.output = output
        self.funciones = {}
        self.clases = {}
        self.tabla_simbolos = tabla_simbolos or tabla  # Usar la tabla proporcionada o la global

        # Inicializar memoria con variables globales desde la tabla de símbolos
        if self.tabla_simbolos:
            for simbolo in self.tabla_simbolos.obtener_todos():
                if simbolo.get("categoria") == "variable" and simbolo.get("ambito") == "Global":
                    identificador = simbolo.get("identificador") or simbolo.get("Identificador")
                    valor = simbolo.get("valor") or simbolo.get("Valor")
                    if identificador:
                        self.memoria[identificador] = valor
                        print(f"DEBUG: Inicializada variable global '{identificador}' = {valor}")

    def ejecutar_programa(self, ast):
        resultado = None
        for nodo in ast:
            resultado = self.ejecutar(nodo)
        return resultado

    def ejecutar(self, nodo):
        if nodo is None:
            return None

        tipo = nodo.get("nodo")

        # -------------------------
        # DECLARACIONES Y ASIGNACIÓN
        # -------------------------
        if tipo == "DECL_VAR":
            val = None
            if nodo.get("valor") is not None:
                val = self.ejecutar(nodo["valor"])

            nombre = nodo["id"]
            self.memoria[nombre] = val

            # Actualizar también en la tabla de símbolos
            if self.tabla_simbolos:
                simbolo_existente = self.tabla_simbolos.buscar(nombre)
                if simbolo_existente:
                    self.tabla_simbolos.actualizar(nombre, val)
                else:
                    # Si no existe, crear uno nuevo
                    nuevo_simbolo = {
                        "identificador": nombre,
                        "categoria": "variable",
                        "tipo_dato": nodo.get("tipo"),
                        "valor": val,
                        "estado": "inicializado" if val is not None else "declarado",
                        "ambito": "Global",
                        "linea": nodo.get("linea", -1)
                    }
                    self.tabla_simbolos.insertar(nuevo_simbolo)

            print(f"DEBUG: Declarada variable '{nombre}' = {val}")
            return None

        if tipo == "ASIGNACION":
            val = self.ejecutar(nodo["valor"])
            nombre = nodo["id"]

            if nombre not in self.memoria:
                # Buscar en la tabla de símbolos
                if self.tabla_simbolos:
                    simbolo = self.tabla_simbolos.buscar(nombre)
                    if simbolo:
                        # La variable existe en la tabla pero no en memoria local
                        self.memoria[nombre] = val
                        self.tabla_simbolos.actualizar(nombre, val)
                        print(f"DEBUG: Asignada variable existente '{nombre}' = {val}")
                        return val

                raise RuntimeErrorInterp(
                    f"Variable no declarada: {nombre} (línea {nodo.get('linea')})"
                )

            self.memoria[nombre] = val

            # Actualizar también en tabla de símbolos
            if self.tabla_simbolos:
                self.tabla_simbolos.actualizar(nombre, val)

            print(f"DEBUG: Asignada variable '{nombre}' = {val}")
            return val

        # -------------------------
        # IMPRIMIR
        # -------------------------
        if tipo == "IMPRIMIR":
            v = self.ejecutar(nodo["valor"])
            self.output(v)
            print(f"DEBUG: Imprimir: {v}")
            return None

        # -------------------------
        # CONDICIONAL
        # -------------------------
        if tipo == "SI":
            cond = self.ejecutar(nodo["cond"])
            print(f"DEBUG: Condición SI: {cond}")
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
        if tipo in ["LIT_INT", "LIT_FLOAT", "LIT_STR", "LIT_BOOL", "LIT_CHAR"]:
            return nodo["valor"]

        if tipo == "VAR":
            name = nodo["id"]
            print(f"DEBUG: Buscando variable '{name}'")

            # Buscar en memoria local primero
            if name in self.memoria:
                valor = self.memoria[name]
                print(f"DEBUG: Encontrada en memoria local: {valor}")
                return valor

            # Buscar en la tabla de símbolos global
            if self.tabla_simbolos:
                simbolo = self.tabla_simbolos.buscar(name)
                if simbolo:
                    # Usar cualquier campo que pueda contener el valor
                    valor = simbolo.get("valor") or simbolo.get("Valor")
                    print(f"DEBUG: Encontrada en tabla de símbolos: {valor}")

                    if valor is not None:
                        # También almacenar en memoria local para acceso futuro
                        self.memoria[name] = valor
                        return valor
                    else:
                        # Si no hay valor, usar un valor por defecto según el tipo
                        tipo_dato = simbolo.get("tipo_dato") or simbolo.get("Tipo de dato")
                        if tipo_dato in ["entero", "TIPO_ENTERO", "int"]:
                            return 0
                        elif tipo_dato in ["flotante", "TIPO_FLOTANTE", "float"]:
                            return 0.0
                        elif tipo_dato in ["booleano", "TIPO_BOOLEANO", "bool"]:
                            return False
                        elif tipo_dato in ["cadena", "TIPO_CADENA", "string"]:
                            return ""
                        elif tipo_dato in ["caracter", "TIPO_CARACTER", "char"]:
                            return ' '
                        else:
                            return None

            # Si no está en ninguno, error
            raise RuntimeErrorInterp(f"Símbolo '{name}' no encontrado en la tabla.")

        # ... (el resto del código se mantiene igual)

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
