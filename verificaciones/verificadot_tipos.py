from .clasificacion_errores import CategoriaError, ReporteErrores

class VerificadorTipos:
    def __init__(self, tabla_simbolos, reporte_errores):
        self.tabla_simbolos = tabla_simbolos
        self.errores = [{
        }]
        self.reporte = reporte_errores
        # Mapeo de tokens de operación a operadores canónicos
        self.op_token_a_simbolo = {
            "MAS": "+", "MENOS": "-", "MULT": "*", "DIV": "/", "MOD": "%",
            "INCREMENTO": "++", "DECREMENTO": "--",
            "IGUAL": "==", "DISTINTO": "!=", "MENOR": "<", "MAYOR": ">", "MENOR_IGUAL": "<=", "MAYOR_IGUAL": ">=",
            "AND": "&&", "OR": "||", "NOT": "!"
        }

    def _inferir_tipo_operacion(self, tipo_izq, tipo_der, operador):
        """Infere el tipo resultante de una operación binaria"""

        # Mapear tipos a formato estándar
        mapeo_tipos = {
            'entero': 'TIPO_ENTERO',
            'flotante': 'TIPO_FLOTANTE',
            'booleano': 'TIPO_BOOLEANO',
            'cadena': 'TIPO_CADENA',
            'caracter': 'TIPO_CARACTER',
            'TIPO_ENTERO': 'TIPO_ENTERO',
            'TIPO_FLOTANTE': 'TIPO_FLOTANTE',
            'TIPO_BOOLEANO': 'TIPO_BOOLEANO',
            'TIPO_CADENA': 'TIPO_CADENA',
            'TIPO_CARACTER': 'TIPO_CARACTER'
        }

        tipo_izq = mapeo_tipos.get(tipo_izq, tipo_izq)
        tipo_der = mapeo_tipos.get(tipo_der, tipo_der)

        print(f"DEBUG_TIPOS: Inferiendo tipo para {tipo_izq} {operador} {tipo_der}")

        # Operaciones aritméticas
        if operador in ['MAS', 'MENOS', 'MULT', 'DIV', 'MOD']:
            if tipo_izq == 'TIPO_CADENA' or tipo_der == 'TIPO_CADENA':
                return 'TIPO_CADENA'  # Concatenación
            elif tipo_izq == 'TIPO_FLOTANTE' or tipo_der == 'TIPO_FLOTANTE':
                return 'TIPO_FLOTANTE'
            elif tipo_izq == 'TIPO_ENTERO' and tipo_der == 'TIPO_ENTERO':
                return 'TIPO_ENTERO'

        # Operaciones de comparación
        elif operador in ['IGUAL', 'DISTINTO', 'MENOR', 'MAYOR', 'MENOR_IGUAL', 'MAYOR_IGUAL']:
            return 'TIPO_BOOLEANO'

        # Operaciones lógicas
        elif operador in ['AND', 'OR']:
            if tipo_izq == 'TIPO_BOOLEANO' and tipo_der == 'TIPO_BOOLEANO':
                return 'TIPO_BOOLEANO'

        print(f"DEBUG_TIPOS: ❌ Operación {operador} no válida entre {tipo_izq} y {tipo_der}")
        return "DESCONOCIDO"

    def normalizar_tipo(self, tipo):
        # Evitar None
        if not tipo:
            return "DESCONOCIDO"

        # Ya viene normalizado
        if isinstance(tipo, str) and tipo.startswith("TIPO_"):
            return tipo

        # Literales del analizador léxico
        literales = {
            "ENTERO_LIT": "TIPO_ENTERO",
            "FLOTANTE_LIT": "TIPO_FLOTANTE",
            "CADENA_LIT": "TIPO_CADENA",
            "CARACTER_LIT": "TIPO_CARACTER",
            "BOOLEANO_LIT": "TIPO_BOOLEANO",
            "LIT_INT": "TIPO_ENTERO",
            "LIT_FLOAT": "TIPO_FLOTANTE",
            "LIT_STR": "TIPO_CADENA",
            "LIT_CHAR": "TIPO_CARACTER",
            "LIT_BOOL": "TIPO_BOOLEANO"
        }
        if tipo in literales:
            return literales[tipo]

        # Palabras reservadas (tipos escritos en el código)
        reservadas = {
            "entero": "TIPO_ENTERO",
            "flotante": "TIPO_FLOTANTE",
            "booleano": "TIPO_BOOLEANO",
            "caracter": "TIPO_CARACTER",
            "cadena": "TIPO_CADENA",
        }
        if tipo in reservadas:
            return reservadas[tipo]

        # Si el tipo viene como el nombre guardado en la tabla (p. ej. "entero" o "TIPO_ENTERO")
        # ya cubierto arriba; si no, devolver desconocido
        return "DESCONOCIDO"

    def _normalizar_operacion(self, operacion):
        """Convierte el token/op (ej. 'MAS') a un símbolo canónico ('+')"""
        if operacion is None:
            return None
        # Si ya es símbolo, devolver tal cual
        if operacion in ['+', '-', '*', '/', '%', '++', '--', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!']:
            return operacion
        # Si es el nombre del token (MAS, IGUAL, AND...), mapearlo
        return self.op_token_a_simbolo.get(operacion, operacion)

    def verificar_compatibilidad(self, tipo1, tipo2, operacion, linea):
        """Verifica si dos tipos son compatibles para una operación"""
        tipo1_norm = self.normalizar_tipo(tipo1)
        tipo2_norm = self.normalizar_tipo(tipo2)
        op = self._normalizar_operacion(operacion)

        # Aritméticas
        if op in ['+', '-', '*', '/', '%', '++', '--']:
            if tipo1_norm in ['TIPO_ENTERO', 'TIPO_FLOTANTE'] and tipo2_norm in ['TIPO_ENTERO', 'TIPO_FLOTANTE']:
                return True
            else:
                self.reporte.agregar_error(CategoriaError.TIPO, f"Operación '{op}' no válida entre {tipo1} y {tipo2}", linea)
                print(f"🔥 DEBUG_TIPOS: Error de tipo en línea {linea}: operación '{op}' entre {tipo1} y {tipo2} no es válida")
                return False

        # Comparaciones
        if op in ['==', '!=', '<', '>', '<=', '>=']:
            if tipo1_norm == tipo2_norm or (tipo1_norm in ['TIPO_ENTERO', 'TIPO_FLOTANTE'] and tipo2_norm in ['TIPO_ENTERO', 'TIPO_FLOTANTE']):
                return True
            else:
                self.reporte.agregar_error(CategoriaError.TIPO, f"Comparación '{op}' no válida entre {tipo1} y {tipo2}", linea)
                print(f"🔥 DEBUG_TIPOS: Error de tipo en línea {linea}: comparación '{op}' entre {tipo1} y {tipo2} no es válida")
                return False

        # Lógicas
        if op in ['&&', '||']:
            if tipo1_norm == 'TIPO_BOOLEANO' and tipo2_norm == 'TIPO_BOOLEANO':
                return True
            else:
                self.reporte.agregar_error(CategoriaError.TIPO, f"Operación lógica '{op}' requiere booleanos", linea)
                print(f"🔥 DEBUG_TIPOS: Error de tipo en línea {linea}: operación lógica '{op}' requiere booleanos")
                return False

        # Negación unaria '!'
        if op == '!':
            return True

        # Concatenación de cadenas (usamos '+' canónico)
        if op == '+':
            if tipo1_norm == 'TIPO_CADENA' and tipo2_norm == 'TIPO_CADENA':
                return True
        return True
    

    def verificar_division_por_cero(self, nodo):
        """Detecta divisiones por cero en tiempo de compilación"""
        if nodo.get('nodo') == 'BIN_OP' and nodo.get('op') in ['DIV', '/', 'MOD', '%']:
            derecha = nodo.get('der')
            # Solo podemos detectar si es un literal cero
            if derecha and isinstance(derecha, dict):
                if derecha.get('nodo') in ['LIT_INT', 'ENTERO_LIT'] and derecha.get('valor') == 0:
                    self.reporte.agregar_error(CategoriaError.EJECUCION, f"División por cero detectada", nodo.get('linea'))
                    print(f"🔥 DEBUG_TIPOS: División por cero detectada en línea {nodo.get('linea')}")
                    return False
                elif derecha.get('nodo') in ['LIT_FLOAT', 'FLOTANTE_LIT'] and derecha.get('valor') == 0.0:
                    self.reporte.agregar_error(CategoriaError.EJECUCION, f"División por cero detectada", nodo.get('linea'))
                    print(f"🔥 DEBUG_TIPOS: División por cero detectada en línea {nodo.get('linea')}")
                    return False
        return True
    
    
    def verificar_conversion_peligrosa(self, tipo_origen, tipo_destino, linea):
        """Detecta conversiones potencialmente peligrosas"""
        tipo_origen_norm = self.normalizar_tipo(tipo_origen)
        tipo_destino_norm = self.normalizar_tipo(tipo_destino)
        
        conversiones_peligrosas = [
            ('TIPO_FLOTANTE', 'TIPO_ENTERO'),  # Pérdida de decimales
            ('TIPO_CADENA', 'TIPO_ENTERO'),    # Posible error de parseo
            ('TIPO_CADENA', 'TIPO_FLOTANTE'),  # Posible error de parseo
        ]
        
        if (tipo_origen_norm, tipo_destino_norm) in conversiones_peligrosas:
            self.reporte.agregar_error(CategoriaError.TIPO, f"Conversión implícita potencialmente peligrosa de {tipo_origen} a {tipo_destino}", linea)
            print(f"🔥 DEBUG_TIPOS: Conversión implícita potencialmente peligrosa de {tipo_origen} a {tipo_destino} en línea {linea}")
            return False
        return True
    
    
    def verificar_asignacion(self, tipo_variable, tipo_valor, linea):
        """Verifica compatibilidad en asignaciones"""
        tipo_var_norm = self.normalizar_tipo(tipo_variable)
        tipo_val_norm = self.normalizar_tipo(tipo_valor)

        # Mismo tipo - siempre válido
        if tipo_var_norm == tipo_val_norm:
            return True

        # Conversiones implícitas permitidas
        if tipo_var_norm == 'TIPO_FLOTANTE' and tipo_val_norm == 'TIPO_ENTERO':
            # Advertencia pero permitido
            self.reporte.agregar_error(CategoriaError.TIPO, f"ADVERTENCIA Línea {linea}: Asignación de entero a flotante - posible pérdida de precisión", linea)
            print(f"🔥 DEBUG_TIPOS: ADVERTENCIA Línea {linea}: Asignación de entero a flotante - posible pérdida de precisión")
            return True

        # Verificar otras conversiones peligrosas
        if not self.verificar_conversion_peligrosa(tipo_valor, tipo_variable, linea):
            return False

        # Si llegamos aquí, es incompatible
        self.reporte.agregar_error(CategoriaError.TIPO, f"Asignación incompatible - variable: {tipo_variable}, valor: {tipo_valor}", linea)
        print(f"🔥 DEBUG_TIPOS: Asignación incompatible - variable: {tipo_variable}, valor: {tipo_valor} en línea {linea}")
        return False
    
    
    def verificar_condicion(self, tipo_cond, linea):
        """Verifica que una condición sea booleana"""
        if tipo_cond != 'TIPO_BOOLEANO':
            self.reporte.agregar_error(CategoriaError.TIPO, f"La condición debe ser booleana", linea)
            print(f"🔥 DEBUG_TIPOS: La condición debe ser booleana en línea {linea}")
            return False
        return True
    



    # ---------- Arreglos ----------
    def verificar_acceso_arreglo(self, nodo_acceso):
        """
        Nodo esperado:
        { 'nodo': 'ACCESO_ARREGLO', 'array': {'nodo': 'VAR','id': 'arr', ...}, 'index': <nodo indice>, 'linea': n }
        Tabla de símbolos: simbolo = tabla_simbolos.buscar('arr') -> debe contener 'tamanio' o 'size' si es estático.
        """
        linea = nodo_acceso.get('linea', 0)
        array_node = nodo_acceso.get('arreglo')
        index_node = nodo_acceso.get('index')

        if not isinstance(array_node, dict):
            self.reporte.agregar_error(CategoriaError.DECLARACION, "Acceso a arreglo inválido (no es un identificador)", linea)
            return 'DESCONOCIDO'

        if array_node.get('nodo') != 'VAR':
            self.reporte.agregar_error(CategoriaError.DECLARACION, "Acceso a arreglo: se esperaba identificador del arreglo", linea)
            return 'DESCONOCIDO'

        nombre = array_node.get('id')
        simbolo = self.tabla_simbolos.buscar(nombre)
        if not simbolo:
            self.reporte.agregar_error(CategoriaError.DECLARACION, f"Arreglo '{nombre}' no declarado", linea)
            return 'DESCONOCIDO'

        # comprobar que sea tipo arreglo (esperamos tipo_dato algo como 'TIPO_ARREGLO' o 'TIPO_<base>[]')
        tipo_dato = simbolo.get('tipo_dato', 'DESCONOCIDO')
        tipo_normal = self.normalizar_tipo(tipo_dato)
        # índice debe ser entero
        tipo_indice = self.obtener_tipo_expresion(index_node)
        if tipo_indice != 'TIPO_ENTERO':
            self.reporte.agregar_error(CategoriaError.TIPO, f"Índice de arreglo debe ser entero, se obtuvo {tipo_indice}", linea)
            # continuar para intentar deducir
        # si índice es literal entero y tabla contiene tamaño, verificar rango
        if isinstance(index_node, dict) and index_node.get('nodo') in ('LIT_INT', 'ENTERO_LIT'):
            idx_val = index_node.get('valor')
            # soportar distintos nombres de campo de tamaño
            tamanio = simbolo.get('tamanio') or simbolo.get('size') or simbolo.get('length')
            if isinstance(tamanio, int):
                if idx_val < 0 or idx_val >= tamanio:
                    self.reporte.agregar_error(CategoriaError.EJECUCION, f"Acceso fuera de límites al arreglo '{nombre}' (índice {idx_val} fuera de [0..{tamanio-1}])", linea)
                    return 'DESCONOCIDO'
        else:
            # índice no literal: advertencia de posible acceso fuera de rango
            self.reporte.agregar_error(CategoriaError.EJECUCION, f"Acceso a arreglo '{nombre}' con índice no literal: posible acceso fuera de límites", linea, severidad="ADVERTENCIA")

        # si todo bien, devolver tipo base del arreglo si lo podemos obtener
        # intentar extraer tipo base de 'TIPO_<BASE>[]' o símbolo.tipo_base
        tipo_base = simbolo.get('tipo_base')
        if tipo_base:
            return self.normalizar_tipo(tipo_base)
        # intentar parsear tipo_dato si tiene '[]'
        if isinstance(tipo_dato, str) and tipo_dato.endswith('[]'):
            base = tipo_dato[:-2]
            return self.normalizar_tipo(base)
        # fallo: desconocido
        return 'DESCONOCIDO'

    # ---------- Unarios ----------
    def verificar_unario(self, nodo):
        """
        Nodo esperado: {'nodo': 'UNARIO', 'op': '!', 'arg': <nodo>, 'linea': n}
        Validar tipos para: !, - (unario), ++, -- (unario si aparece)
        """
        op = self._normalizar_operacion(nodo.get('op'))
        arg = nodo.get('arg')
        linea = nodo.get('linea', 0)

        tipo_arg = self.obtener_tipo_expresion(arg)

        if op == '!':
            if tipo_arg != 'TIPO_BOOLEANO':
                self.reporte.agregar_error(CategoriaError.TIPO, f"Operador '!' requiere operando booleano, se obtuvo {tipo_arg}", linea)
                return 'DESCONOCIDO'
            return 'TIPO_BOOLEANO'

        if op == '-':
            if tipo_arg not in ['TIPO_ENTERO', 'TIPO_FLOTANTE']:
                self.reporte.agregar_error(CategoriaError.TIPO, f"Operador unario '-' requiere operando numérico, se obtuvo {tipo_arg}", linea)
                return 'DESCONOCIDO'
            return tipo_arg

        if op in ['++', '--']:
            # deben aplicarse a variables (lvalue) y ser numéricos
            if not isinstance(arg, dict) or arg.get('nodo') != 'VAR':
                self.reporte.agregar_error(CategoriaError.TIPO, f"Operador '{op}' requiere una variable (lvalue)", linea)
                return 'DESCONOCIDO'
            if tipo_arg not in ['TIPO_ENTERO', 'TIPO_FLOTANTE']:
                self.reporte.agregar_error(CategoriaError.TIPO, f"Operador '{op}' requiere tipo numérico, se obtuvo {tipo_arg}", linea)
                return 'DESCONOCIDO'
            return tipo_arg

        # si no es reconocido
        return 'DESCONOCIDO'

    # ---------- Obtener tipo de expresión (central) ----------

    def obtener_tipo_expresion(self, nodo):
        """Obtiene el tipo de una expresión - VERSIÓN CORREGIDA"""
        if nodo is None:
            return "DESCONOCIDO"

        tipo_nodo = nodo.get('nodo')

        # Literales
        if tipo_nodo == 'LIT_INT':
            return 'TIPO_ENTERO'
        elif tipo_nodo == 'LIT_FLOAT':
            return 'TIPO_FLOTANTE'
        elif tipo_nodo == 'LIT_STR':
            return 'TIPO_CADENA'
        elif tipo_nodo == 'LIT_BOOL':
            return 'TIPO_BOOLEANO'
        elif tipo_nodo == 'LIT_CHAR':
            return 'TIPO_CARACTER'

        # Variables - 🔥 CORRECCIÓN CRÍTICA
        elif tipo_nodo == 'VAR':
            nombre = nodo.get('id')
            print(f"DEBUG_TIPOS: Buscando tipo de variable '{nombre}'")

            # Buscar PRIMERO en estructura extendida
            if hasattr(self.tabla_simbolos, 'variables_extendidas'):
                if nombre in self.tabla_simbolos.variables_extendidas:
                    tipo = self.tabla_simbolos.variables_extendidas[nombre].tipo_dato
                    print(f"DEBUG_TIPOS: ✅ Variable '{nombre}' encontrada en extendida - tipo: {tipo}")
                    return tipo

            if hasattr(self.tabla_simbolos, 'constantes_extendidas'):
                if nombre in self.tabla_simbolos.constantes_extendidas:
                    tipo = self.tabla_simbolos.constantes_extendidas[nombre].tipo_dato
                    print(f"DEBUG_TIPOS: ✅ Constante '{nombre}' encontrada en extendida - tipo: {tipo}")
                    return tipo

            # Buscar en estructura antigua
            simbolo = self.tabla_simbolos.buscar(nombre)
            if simbolo:
                tipo = simbolo.get('tipo_dato', 'DESCONOCIDO')
                print(f"DEBUG_TIPOS: ✅ Variable '{nombre}' encontrada en antigua - tipo: {tipo}")
                return tipo

            print(f"DEBUG_TIPOS: ❌ Variable '{nombre}' NO encontrada en ninguna estructura")
            return "DESCONOCIDO"

        # Operaciones binarias
        elif tipo_nodo == 'BIN_OP':
            try:
                tipo_izq = self.obtener_tipo_expresion(nodo.get('izq'))
                tipo_der = self.obtener_tipo_expresion(nodo.get('der'))
                op = nodo.get('op')

                print(f"DEBUG_TIPOS: Operación {op} entre {tipo_izq} y {tipo_der}")

                # Si alguno es desconocido, retornar desconocido
                if tipo_izq == "DESCONOCIDO" or tipo_der == "DESCONOCIDO":
                    return "DESCONOCIDO"

                # Lógica de inferencia de tipos
                return self._inferir_tipo_operacion(tipo_izq, tipo_der, op)
            except Exception as e:
                print(f"DEBUG_TIPOS: Error en operación binaria: {e}")
                return "DESCONOCIDO"

        # Llamadas a función
        elif tipo_nodo == 'LLAMADA_FUNCION':
            nombre_funcion = nodo.get('id')
            print(f"DEBUG_TIPOS: Llamada a función '{nombre_funcion}'")

            # Buscar función en tabla extendida
            if hasattr(self.tabla_simbolos, 'funciones_extendidas'):
                if nombre_funcion in self.tabla_simbolos.funciones_extendidas:
                    tipo_retorno = self.tabla_simbolos.funciones_extendidas[nombre_funcion].tipo_retorno
                    print(f"DEBUG_TIPOS: ✅ Función '{nombre_funcion}' encontrada - tipo retorno: {tipo_retorno}")
                    return tipo_retorno

            # Buscar en estructura antigua
            funcion = self.tabla_simbolos.buscar(nombre_funcion)
            if funcion and funcion.get('categoria') == 'funcion':
                tipo_retorno = funcion.get('tipo_dato', 'TIPO_VACIO')
                print(f"DEBUG_TIPOS: ✅ Función '{nombre_funcion}' encontrada en antigua - tipo: {tipo_retorno}")
                return tipo_retorno

            print(f"DEBUG_TIPOS: ❌ Función '{nombre_funcion}' no encontrada")
            return "DESCONOCIDO"

        # Expresiones entre paréntesis
        elif tipo_nodo in ['PAREN_IZQ', 'PAREN_DER']:
            return self.obtener_tipo_expresion(nodo.get('expr'))

        return "DESCONOCIDO"