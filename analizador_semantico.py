#analizador_semantico.py
from verificaciones.verificadot_tipos import VerificadorTipos
from verificaciones.Validador_funciones import ValidadorFunciones
from verificaciones.clasificacion_errores import CategoriaError, ReporteErrores
from verificaciones.validador_incializacion import ValidadorInicializacion


class AnalizadorSemantico:
    
    def __init__(self, tabla_simbolos, reporte_errores):

        self.errores = []
        self.reporte = reporte_errores
        self.tipo_funcion_actual = None
        self.tabla_simbolos = tabla_simbolos
        self.verificador_tipos = VerificadorTipos(tabla_simbolos, reporte_errores)
        self.validador_funciones = ValidadorFunciones(tabla_simbolos, self.verificador_tipos, reporte_errores)
        self.validador_inicializacion = ValidadorInicializacion(tabla_simbolos, reporte_errores)
    
    def analizar(self, ast):
        """Realiza el análisis semántico completo del AST"""
        
        for nodo in ast:
            self._visitar_nodo(nodo)
        
        # 🔥 DEBUG: Imprimir todos los errores encontrados
        print(f"🔥 DEBUG_SEMANTICO: Se encontraron {len(self.reporte.errores)} errores")
        for error in self.reporte.errores:
            print(f"  - {error}")
        
        return self.reporte.errores
    
    def _visitar_nodo(self, nodo):
        """Visita un nodo del AST y realiza las validaciones semánticas"""
        if not isinstance(nodo, dict):
            return
        
        tipo_nodo = nodo.get('nodo')
        
        if tipo_nodo == 'DECL_VAR':
            self._visitar_declaracion_variable(nodo)
        elif tipo_nodo == 'ASIGNACION':
            self._visitar_asignacion(nodo)
        elif tipo_nodo == 'BIN_OP':
            self._visitar_operacion_binaria(nodo)
        elif tipo_nodo == 'FUNCION':
            self._visitar_declaracion_funcion(nodo)
        elif tipo_nodo == 'LLAMADA_FUNCION':
            self._visitar_llamada_funcion(nodo)
        elif tipo_nodo == 'RETORNAR':
            self._visitar_retorno(nodo)
        elif tipo_nodo == 'SI':
            self._visitar_condicional(nodo)
        elif tipo_nodo == 'BLOQUE':
            self._visitar_bloque(nodo)
        elif tipo_nodo == 'VAR':
            self._visitar_variable(nodo)
            
                
    def _visitar_declaracion_variable(self, nodo):
        """Valida declaración de variable"""
        nombre = nodo['id']
        tipo_declarado = nodo['tipo']
        valor = nodo.get('valor')
        
        # Si el valor es una llamada a función, validar la llamada
        if valor and isinstance(valor, dict) and valor.get('nodo') == 'LLAMADA_FUNCION':
            # Validar la llamada a función
            self._visitar_llamada_funcion(valor)
        # Verificar inicialización
        if valor:
            tipo_valor = self.verificador_tipos.obtener_tipo_expresion(valor)
            if not self.verificador_tipos.verificar_asignacion(tipo_declarado, tipo_valor, nodo.get('linea', 0)):
                self.errores.append(f"Línea {nodo.get('linea')}: Tipo incompatible en inicialización de '{nombre}'")
                
                self.reporte.agregar_error(CategoriaError.TIPO,
                                           f"Inicialización incompatible en '{nombre}'",
                                           nodo.get('linea', 0))
                print(f"🔥 ERROR: Inicialización incompatible en '{nombre}' en línea {nodo.get('linea', 0)}")
        if self.validador_inicializacion and valor:
            self.validador_inicializacion.verificar_variable_no_inicializada(nombre, nodo.get('linea', 0))
            
            
    def _visitar_asignacion(self, nodo):
        nombre = nodo['id']
        valor = nodo['valor']
        linea = nodo.get('linea', 0)

        simbolo = self.tabla_simbolos.buscar(nombre)
        if not simbolo:
            self.reporte.agregar_error(CategoriaError.DECLARACION,
                                       f"Variable '{nombre}' no declarada",
                                       linea)
            return

        # constante no modificable
        if self.validador_inicializacion:
            self.validador_inicializacion.verificar_modificacion_constante(nombre, linea)

        # verificación de tipos
        tipo_variable = simbolo.get('tipo_dato')
        tipo_valor = self.verificador_tipos.obtener_tipo_expresion(valor)

        if not self.verificador_tipos.verificar_asignacion(tipo_variable, tipo_valor, linea):
            self.reporte.agregar_error(CategoriaError.TIPO,
                                       f"Asignación incompatible en '{nombre}'",
                                       linea)
            print(f"🔥 ERROR: Asignación incompatible en '{nombre}' en línea {linea}"  )
    
    
    def _visitar_operacion_binaria(self, nodo):
        """Valida una operación binaria"""
        tipo_izq = self.verificador_tipos.obtener_tipo_expresion(nodo['izq'])
        tipo_der = self.verificador_tipos.obtener_tipo_expresion(nodo['der'])
        
        self.verificador_tipos.verificar_compatibilidad(
            tipo_izq, tipo_der, nodo['op'], nodo.get('linea', 0)
        )
    
    def _visitar_declaracion_funcion(self, nodo):
        print("ENTRREEEE A LA FUNCION");
        """Valida declaración de función"""
        self.funcion_actual = nodo.get('nombre')
        self.tipo_funcion_actual = nodo.get('tipo', 'TIPO_VACIO')
        
        print(f"🔥 DEBUG_SEMANTICO: Analizando función '{self.funcion_actual}' con tipo retorno '{self.tipo_funcion_actual}'")
        
        # Entrar al ámbito de la función
        ambito_funcion = f"funcion:{self.funcion_actual}"
        self.tabla_simbolos.entrar_ambito(ambito_funcion)
        
        # 🔥 CORRECCIÓN: Solo validar, no insertar
        if not self.validador_funciones.validar_declaracion_funcion(nodo):
            # Si hay errores en la validación, no procesar el cuerpo
            self.tabla_simbolos.salir_ambito()
            self.funcion_actual = None
            self.tipo_funcion_actual = None
            return
        
        # Visitar el cuerpo de la función
        if nodo.get('cuerpo'):
            self._visitar_nodo(nodo['cuerpo'])
        
        # Salir del ámbito
        self.tabla_simbolos.salir_ambito()
        self.funcion_actual = None
        self.tipo_funcion_actual = None
        
    def _visitar_llamada_funcion(self, nodo):
        print("enreeeeeeeeee");
        """Valida llamada a función"""
        self.validador_funciones.validar_llamada_funcion(nodo)
    
    def _visitar_retorno(self, nodo):
        """Valida sentencia return"""
        if self.tipo_funcion_actual:
            self.validador_funciones.validar_retorno(nodo, self.tipo_funcion_actual)
    
    def _visitar_condicional(self, nodo):
        print("holaaa")
        linea = nodo.get('linea', 0)
        print(nodo['cond']);
        tipo_cond = self.verificador_tipos.obtener_tipo_expresion(nodo['cond'])
        if tipo_cond != 'TIPO_BOOLEANO':
            self.reporte.agregar_error(CategoriaError.TIPO,
                                       "La condición del 'si' debe ser booleana",
                                       linea)
            print(f"🔥 ERROR: La condición del 'si' debe ser booleana en línea {linea}")

        if nodo.get('SINO'):
            self._visitar_nodo(nodo['SINO'])

    
    def _visitar_bloque(self, nodo):
        """Valida un bloque de código"""
        self.tabla_simbolos.entrar_ambito("bloque")
        for sentencia in nodo.get('sentencias', []):
            self._visitar_nodo(sentencia)
        self.tabla_simbolos.salir_ambito()
    
    def _visitar_variable(self, nodo):
        nombre = nodo['id']
        linea = nodo.get('linea', 0)

        simbolo = self.tabla_simbolos.buscar(nombre)
        if not simbolo:
            self.reporte.agregar_error(CategoriaError.DECLARACION,
                                       f"Variable '{nombre}' no declarada",
                                       linea)
            print(f"🔥 ERROR: Variable '{nombre}' no declarada en línea {linea}")