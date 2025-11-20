#analizador_semantico.py
from verificaciones.verificadot_tipos import VerificadorTipos
from verificaciones.Validador_funciones import ValidadorFunciones

class AnalizadorSemantico:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.verificador_tipos = VerificadorTipos(tabla_simbolos)
        self.validador_funciones = ValidadorFunciones(tabla_simbolos, self.verificador_tipos)
        self.errores = []
        self.funcion_actual = None
        self.tipo_funcion_actual = None
    
    def analizar(self, ast):
        """Realiza el análisis semántico completo del AST"""
        self.errores = []
        self.tabla_simbolos.limpiar_errores()
        self.verificador_tipos.errores = []
        self.validador_funciones.errores = []
        
        for nodo in ast:
            self._visitar_nodo(nodo)
        
        # Recolectar todos los errores
        self.errores.extend(self.tabla_simbolos.obtener_errores_semanticos())
        self.errores.extend(self.verificador_tipos.errores)
        self.errores.extend(self.validador_funciones.errores)
        
        return self.errores
    
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
        
        # Verificar inicialización
        if valor:
            tipo_valor = self.verificador_tipos.obtener_tipo_expresion(valor)
            if not self.verificador_tipos.verificar_asignacion(tipo_declarado, tipo_valor, nodo.get('linea', 0)):
                self.errores.append(f"Línea {nodo.get('linea')}: Tipo incompatible en inicialización de '{nombre}'")
    
    def _visitar_asignacion(self, nodo):
        """Valida una asignación"""
        nombre = nodo['id']
        valor = nodo['valor']
        
        # Verificar que la variable exista
        if not self.tabla_simbolos.verificar_declaracion(nombre, nodo.get('linea', 0)):
            return
        
        # Verificar tipos
        simbolo = self.tabla_simbolos.buscar(nombre)
        if simbolo:
            tipo_variable = simbolo.get('tipo_dato')
            tipo_valor = self.verificador_tipos.obtener_tipo_expresion(valor)
            
            if not self.verificador_tipos.verificar_asignacion(tipo_variable, tipo_valor, nodo.get('linea', 0)):
                self.errores.append(f"Línea {nodo.get('linea')}: Asignación incompatible en '{nombre}'")
    
    def _visitar_operacion_binaria(self, nodo):
        """Valida una operación binaria"""
        tipo_izq = self.verificador_tipos.obtener_tipo_expresion(nodo['izq'])
        tipo_der = self.verificador_tipos.obtener_tipo_expresion(nodo['der'])
        
        self.verificador_tipos.verificar_compatibilidad(
            tipo_izq, tipo_der, nodo['op'], nodo.get('linea', 0)
        )
    
    def _visitar_declaracion_funcion(self, nodo):
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
        """Valida llamada a función"""
        self.validador_funciones.validar_llamada_funcion(nodo)
    
    def _visitar_retorno(self, nodo):
        """Valida sentencia return"""
        if self.tipo_funcion_actual:
            self.validador_funciones.validar_retorno(nodo, self.tipo_funcion_actual)
    
    def _visitar_condicional(self, nodo):
        """Valida condicional"""
        tipo_cond = self.verificador_tipos.obtener_tipo_expresion(nodo['cond'])
        if tipo_cond != 'TIPO_BOOLEANO':
            self.errores.append(f"Línea {nodo.get('linea')}: La condición debe ser booleana")
        
        self._visitar_nodo(nodo['then'])
        if nodo.get('else'):
            self._visitar_nodo(nodo['else'])
    
    def _visitar_bloque(self, nodo):
        """Valida un bloque de código"""
        self.tabla_simbolos.entrar_ambito("bloque")
        for sentencia in nodo.get('sentencias', []):
            self._visitar_nodo(sentencia)
        self.tabla_simbolos.salir_ambito()