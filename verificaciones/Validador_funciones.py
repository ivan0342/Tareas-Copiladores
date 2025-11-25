#validador_funciones.py
from .clasificacion_errores import CategoriaError, ReporteErrores

class ValidadorFunciones:
    def __init__(self, tabla_simbolos, verificador_tipos, reporte_errores):
        self.tabla_simbolos = tabla_simbolos
        self.verificador_tipos = verificador_tipos
        self.errores = []
        self.reporte = reporte_errores
    
    def validar_declaracion_funcion(self, nodo_funcion):
        """Valida la declaración de una función - SOLO VALIDA, NO INSERTA"""
        nombre = nodo_funcion.get('nombre')
        parametros = nodo_funcion.get('params', [])
        tipo_retorno = nodo_funcion.get('tipo', 'TIPO_VACIO')
        linea = nodo_funcion.get('linea', 0)
        
        if not nombre:
            return False
        
        #  CORRECCIÓN: Solo verificar si existe, no insertar
        simbolo_existente = self.tabla_simbolos.buscar(nombre)
        if simbolo_existente and simbolo_existente.get('categoria') == 'funcion':
            # La función ya existe, eso está bien - no es un error
            pass
        elif self.tabla_simbolos.buscar_en_ambito_actual(nombre):
            self.errores.append(f"Línea {linea}: Identificador '{nombre}' ya declarado en este ámbito")
            self.reporte.agregar_error(CategoriaError.FUNCION, f"Identificador '{nombre}' ya declarado en este ámbito", linea)
            print(f"🔥 ERROR_FUNCION: Identificador '{nombre}' ya declarado en este ámbito en línea {linea}")
            return False
        
        # Validar parámetros (solo verificar duplicados en la declaración)
        nombres_parametros = set()
        for tipo_param, nombre_param in parametros:
            if nombre_param in nombres_parametros:
                self.errores.append(f"Línea {linea}: Parámetro duplicado '{nombre_param}' en función '{nombre}'")
                self.reporte.agregar_error(CategoriaError.FUNCION, f"Parámetro duplicado '{nombre_param}' en función '{nombre}'", linea)
                print(f"🔥 ERROR_FUNCION: Parámetro duplicado '{nombre_param}' en función '{nombre}' en línea {linea}")
                return False
            nombres_parametros.add(nombre_param)
        
        #  CORRECCIÓN: NO insertar la función aquí - ya fue insertada por el parser
        return True

    
    def validar_llamada_funcion(self, nodo_llamada):
        """Valida una llamada a función"""
        nombre_funcion = nodo_llamada.get('id')
        argumentos = nodo_llamada.get('args', [])
        linea = nodo_llamada.get('linea', 0)
        
        # Buscar la función

        simbolo_funcion = self.tabla_simbolos.buscar(nombre_funcion)
        print(f"🔥 DEBUG_LLAMADA: Símbolo encontrado: {simbolo_funcion}")

        if not simbolo_funcion or simbolo_funcion.get('categoria') != 'funcion':
            self.reporte.agregar_error(CategoriaError.FUNCION, f"Función '{nombre_funcion}' no declarada", linea)
            print(f"🔥 ERROR: Función '{nombre_funcion}' no declarada en línea {linea}")
            return False
        
        # Verificar número de parámetros
        parametros_esperados = simbolo_funcion.get('parametros', [])
        if len(argumentos) != len(parametros_esperados):
            self.errores.append(f"Línea {linea}: Número incorrecto de argumentos en llamada a '{nombre_funcion}'. Esperados: {len(parametros_esperados)}, obtenidos: {len(argumentos)}")
            self.reporte.agregar_error(CategoriaError.FUNCION, f"Número incorrecto de argumentos en llamada a '{nombre_funcion}'. Esperados: {len(parametros_esperados)}, obtenidos: {len(argumentos)}", linea)
            print(f"🔥 ERROR: Número incorrecto de argumentos en llamada a '{nombre_funcion}' en línea {linea}")
            return False
        
        # Verificar tipos de parámetros
        for i, (arg, (tipo_esperado, _)) in enumerate(zip(argumentos, parametros_esperados)):
            tipo_actual = self.verificador_tipos.obtener_tipo_expresion(arg)
            if not self.verificador_tipos.verificar_asignacion(tipo_esperado, tipo_actual, linea):
                self.errores.append(f"Línea {linea}: Tipo incorrecto en argumento {i+1} de '{nombre_funcion}'. Esperado: {tipo_esperado}, obtenido: {tipo_actual}")
                self.reporte.agregar_error(CategoriaError.TIPO, f"Tipo incorrecto en argumento {i+1} de '{nombre_funcion}'. Esperado: {tipo_esperado}, obtenido: {tipo_actual}", linea)
                print(f"🔥 ERROR: Tipo incorrecto en argumento {i+1} de '{nombre_funcion}' en línea {linea}")
        
        return len(self.errores) == 0
    
    def validar_retorno(self, nodo_retorno, tipo_funcion_actual):
        """Valida una sentencia return"""
        # 🔥 NORMALIZAR TIPO DE FUNCIÓN
        tipo_funcion_normalizado = self.verificador_tipos.normalizar_tipo(tipo_funcion_actual)
        
        valor_retorno = nodo_retorno.get('valor')
        
        if tipo_funcion_normalizado == 'TIPO_VACIO' and valor_retorno is not None:
            linea = nodo_retorno.get('linea', 0)
            self.errores.append(f"Línea {linea}: Función void no puede retornar un valor")
            self.reporte.agregar_error(CategoriaError.FUNCION, f"Función void no puede retornar un valor", linea)
            print(f"🔥 ERROR: Función void no puede retornar un valor en línea {linea}")
            return False
            
        if tipo_funcion_normalizado != 'TIPO_VACIO' and valor_retorno is None:
            linea = nodo_retorno.get('linea', 0)
            self.errores.append(f"Línea {linea}: Función debe retornar un valor")
            self.reporte.agregar_error(CategoriaError.FUNCION, f"Función debe retornar un valor", linea)
            print(f"🔥 ERROR: Función debe retornar un valor en línea {linea}"  )
            return False
            
        if valor_retorno and tipo_funcion_normalizado != 'TIPO_VACIO':
            tipo_retorno = self.verificador_tipos.obtener_tipo_expresion(valor_retorno)
            if not self.verificador_tipos.verificar_asignacion(tipo_funcion_normalizado, tipo_retorno, nodo_retorno.get('linea', 0)):
                linea = nodo_retorno.get('linea', 0)
                self.errores.append(f"Línea {linea}: Tipo de retorno incompatible. Esperado: {tipo_funcion_normalizado}, obtenido: {tipo_retorno}")
                self.reporte.agregar_error(CategoriaError.TIPO, f"Tipo de retorno incompatible. Esperado: {tipo_funcion_normalizado}, obtenido: {tipo_retorno}", linea)
                print(f"🔥 ERROR: Tipo de retorno incompatible en línea {linea}. Esperado: {tipo_funcion_normalizado}, obtenido: {tipo_retorno}")
                return False
        
        return True