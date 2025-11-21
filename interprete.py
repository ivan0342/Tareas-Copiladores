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
        for nodo in ast:
            if isinstance(nodo, dict) and nodo.get("nodo") == "FUNCION":
                nombre = nodo["nombre"]
                self.funciones[nombre] = nodo
                print(f"DEBUG: Pre-registrada función '{nombre}'")
        resultado = None
        for nodo in ast:
            resultado = self.ejecutar(nodo)
        return resultado


    def ejecutar(self, nodo):
        if nodo is None:
            return None

        tipo = nodo.get("nodo")
        if tipo == "LLAMADA_FUNCION":
            nombre_funcion = nodo["id"]
            args_nodos = nodo.get("args", [])
            linea = nodo.get("linea", 0)
            
            print(f"DEBUG: Llamando función '{nombre_funcion}' con {len(args_nodos)} argumentos")
            
            # Verificar que la función existe
            if nombre_funcion not in self.funciones:
                raise RuntimeErrorInterp(f"Función '{nombre_funcion}' no definida (línea {linea})")
            
            # Evaluar argumentos
            args_evaluados = []
            for arg in args_nodos:
                args_evaluados.append(self.ejecutar(arg))
            
            print(f"DEBUG: Argumentos evaluados: {args_evaluados}")
            
            # Llamar a la función
            resultado = self.llamar_funcion(nombre_funcion, args_evaluados, linea)
            print(f"DEBUG: Función '{nombre_funcion}' retornó: {resultado}")
            return resultado
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

        # En el método ejecutar(), caso "VAR":
        if tipo == "VAR":
            name = nodo["id"]
            print(f"DEBUG: Buscando variable '{name}'")

            # Buscar en memoria local primero
            if name in self.memoria:
                valor = self.memoria[name]
                print(f"DEBUG: Encontrada en memoria local: {valor}")
                return valor

            # ✅ BUSCAR EN TABLA EXTENDIDA PRIMERO
            if self.tabla_simbolos:
                # Buscar en variables extendidas
                variable_ext = None

                # Buscar en variables normales
                if hasattr(self.tabla_simbolos,
                           'variables_extendidas') and name in self.tabla_simbolos.variables_extendidas:
                    variable_ext = self.tabla_simbolos.variables_extendidas[name]

                # Buscar en constantes
                elif hasattr(self.tabla_simbolos,
                             'constantes_extendidas') and name in self.tabla_simbolos.constantes_extendidas:
                    variable_ext = self.tabla_simbolos.constantes_extendidas[name]

                if variable_ext:
                    valor = variable_ext.valor
                    print(f"DEBUG: Encontrada en tabla extendida: {valor}")

                    # También almacenar en memoria local para acceso futuro
                    self.memoria[name] = valor
                    return valor

                # Fallback: Buscar en la estructura antigua
                simbolo = self.tabla_simbolos.buscar(name)
                if simbolo:
                    # Usar cualquier campo que pueda contener el valor
                    valor = simbolo.get("valor") or simbolo.get("Valor")
                    print(f"DEBUG: Encontrada en tabla antigua: {valor}")

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

        # -------------------------
        # OPERACIONES BINARIAS
        # -------------------------
        if tipo == "BIN_OP":
            op = nodo.get("op")
            # Ejecutar subexpresiones
            izq_val = self.ejecutar(nodo.get("izq")) if nodo.get("izq") is not None else None
            der_val = self.ejecutar(nodo.get("der")) if nodo.get("der") is not None else None

            print(f"DEBUG: Evaluando BIN_OP {op} con izq={izq_val} der={der_val}")

            # Operadores aritméticos (los tokens del parser son MAS, MENOS, MULT, DIV, MOD)
            if op in ("MAS", "+"):
                # Si alguna es string, concatenar
                if isinstance(izq_val, str) or isinstance(der_val, str):
                    return str(izq_val) + str(der_val)
                # Sumar con coerción int/float
                if isinstance(izq_val, float) or isinstance(der_val, float):
                    return (izq_val or 0) + (der_val or 0)
                return (izq_val or 0) + (der_val or 0)

            if op in ("MENOS", "-"):
                return (izq_val or 0) - (der_val or 0)

            if op in ("MULT", "*"):
                return (izq_val or 0) * (der_val or 0)

            if op in ("DIV", "/"):
                try:
                    return (izq_val or 0) / (der_val or 0)
                except ZeroDivisionError:
                    raise RuntimeErrorInterp(f"División por cero en expresión (línea {nodo.get('linea')})")

            if op in ("MOD", "%"):
                try:
                    return (izq_val or 0) % (der_val or 0)
                except Exception:
                    raise RuntimeErrorInterp(f"Error en módulo en expresión (línea {nodo.get('linea')})")

            # Comparaciones
            if op in ("IGUAL", "=="):
                return izq_val == der_val
            if op in ("DISTINTO", "!="):
                return izq_val != der_val
            if op in ("MENOR", "<"):
                return izq_val < der_val
            if op in ("MAYOR", ">"):
                return izq_val > der_val
            if op in ("MENOR_IGUAL", "<="):
                return izq_val <= der_val
            if op in ("MAYOR_IGUAL", ">="):
                return izq_val >= der_val

            # Lógicos
            if op in ("AND", "&&"):
                return bool(izq_val) and bool(der_val)
            if op in ("OR", "||"):
                return bool(izq_val) or bool(der_val)

            # Si no conocemos el operador, devolver None
            return None

        # -------------------------
        # UNARIOS (p. ej. i++ / i--)
        # -------------------------
        if tipo == "UNARIO":
            # 'id' puede ser un token dict o un string
            id_field = nodo.get("id")
            if isinstance(id_field, dict):
                nombre = id_field.get("token")
            else:
                nombre = id_field

            op_token = nodo.get("op")
            op_tipo = op_token.get("tipo") if isinstance(op_token, dict) else (op_token or "")

            # Obtener valor actual
            valor_actual = self.memoria.get(nombre, None)
            if valor_actual is None:
                # intentar recuperar desde tabla de símbolos
                if self.tabla_simbolos:
                    simbolo = self.tabla_simbolos.buscar(nombre)
                    if simbolo:
                        valor_actual = simbolo.get("valor")
            if valor_actual is None:
                raise RuntimeErrorInterp(f"Variable '{nombre}' no inicializada para operador unario.")

            if op_tipo in ("INCREMENTO", "++"):
                nuevo = valor_actual + 1
                self.memoria[nombre] = nuevo
                if self.tabla_simbolos:
                    self.tabla_simbolos.actualizar(nombre, nuevo)
                return nuevo

            if op_tipo in ("DECREMENTO", "--"):
                nuevo = valor_actual - 1
                self.memoria[nombre] = nuevo
                if self.tabla_simbolos:
                    self.tabla_simbolos.actualizar(nombre, nuevo)
                return nuevo

            return None

        # -------------------------
        # CREACIÓN/DEF FUNCIONES/CLASES/LLAMADAS
        # -------------------------
        if tipo == "NUEVO":
            return self.crear_objeto(nodo["clase"], nodo.get("args", []))

        if tipo == "FUNCION":
            nombre = nodo["nombre"]
            self.funciones[nombre] = nodo
            print(f"DEBUG: Registrada función '{nombre}' en intérprete")
            return None


        if tipo == "RETORNAR":
            valor = self.ejecutar(nodo["valor"]) if nodo.get("valor") is not None else None
            raise ReturnSignal(valor)

        if tipo == "CLASE":
            nombre = nodo["nombre"]
            self.clases[nombre] = nodo
            return None

        if tipo == "LLAMADA_METODO":
            obj = self.memoria.get(nodo["obj"])
            if obj is None:
                raise RuntimeErrorInterp(f"Objeto '{nodo['obj']}' no encontrado.")
            clase = self.clases.get(obj.get("__clase__"))
            metodo = None
            if clase:
                # buscar método por nombre
                for m in clase.get("metodos", []):
                    if m.get("nombre") == nodo["metodo"]:
                        metodo = m
                        break
            if metodo is None:
                raise RuntimeErrorInterp(f"Método '{nodo['metodo']}' no encontrado en clase {obj.get('__clase__')}.")
            args = [obj] + [self.ejecutar(a) for a in nodo.get("args", [])]
            return self.llamar_funcion(metodo["nombre"], args)

        if tipo == "MANEJO_ERRORES" or tipo == "INTENTAR":
            try:
                self.ejecutar(nodo.get("try") or nodo.get("intento"))
            except RuntimeErrorInterp as e:
                error_var = nodo.get("error") if nodo.get("error") else nodo.get("error_var")
                if isinstance(error_var, dict):
                    error_var = error_var.get("token")
                self.memoria[error_var] = str(e)
                self.ejecutar(nodo.get("catch") or nodo.get("captura"))
            return None

        # Si no se reconoce el nodo:
        print(f"DEBUG: Nodo no manejado en intérprete: {tipo}")
        return None

    def llamar_funcion(self, nombre, args, linea=None):
        print(f"🔥 DEBUG_LLAMADA_FUNCION: Buscando función '{nombre}'")
        print(f"🔥 DEBUG_LLAMADA_FUNCION: Funciones disponibles: {list(self.funciones.keys())}")
        
        if nombre not in self.funciones:
            raise RuntimeErrorInterp(f"Función '{nombre}' no definida (línea {linea})")

        funcion = self.funciones[nombre]
        print(f"🔥 DEBUG_LLAMADA_FUNCION: Función '{nombre}' encontrada, parámetros: {funcion.get('params', [])}")

        entorno_anterior = self.memoria
        self.memoria = self.memoria.copy()

        parametros = funcion.get("params", [])
        print(f"DEBUG_LLAMADA_FUNCION: Parámetros esperados: {parametros}")
        print(f"DEBUG_LLAMADA_FUNCION: Argumentos recibidos: {args}")

        # Asignar argumentos a parámetros
        for (tipo_param, nombre_param), valor_arg in zip(parametros, args):
            self.memoria[nombre_param] = valor_arg
            print(f"DEBUG_LLAMADA_FUNCION: Asignado {nombre_param} = {valor_arg}")

        try:
            resultado = self.ejecutar(funcion["cuerpo"])
            print(f"DEBUG_LLAMADA_FUNCION: Función '{nombre}' ejecutada, resultado: {resultado}")
        except ReturnSignal as r:
            resultado = r.valor
            print(f"DEBUG_LLAMADA_FUNCION: Función '{nombre}' retornó: {resultado}")
        except Exception as e:
            print(f"DEBUG_LLAMADA_FUNCION: Error en función '{nombre}': {e}")
            raise
        finally:
            self.memoria = entorno_anterior

        return resultado


    def crear_objeto(self, nombre_clase, args):
        if nombre_clase not in self.clases:
            raise RuntimeErrorInterp(f"Clase '{nombre_clase}' no declarada")

        clase = self.clases[nombre_clase]

        # Crear instancia
        obj = {"__clase__": nombre_clase}

        # Inicializar atributos
        for attr in clase.get("atributos", []):
            obj[attr.get("id")] = None

        # Llamar constructor si existe
        if nombre_clase in self.funciones:
            self.llamar_funcion(nombre_clase, [obj] + [self.ejecutar(a) for a in args])

        return obj
