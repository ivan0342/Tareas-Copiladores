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
    def obtener_tipo_expresion(self, nodo , linea):
        """Determina el tipo de una expresión AST y reporta errores relevantes."""
        if not isinstance(nodo, dict):
            return 'DESCONOCIDO'

        tipo_nodo = nodo.get('nodo')

        # Literales
        if tipo_nodo in ('LIT_INT', 'ENTERO_LIT'):
            return 'TIPO_ENTERO'
        if tipo_nodo in ('LIT_FLOAT', 'FLOTANTE_LIT'):
            return 'TIPO_FLOTANTE'
        if tipo_nodo in ('LIT_STR', 'CADENA_LIT'):
            return 'TIPO_CADENA'
        if tipo_nodo in ('LIT_BOOL', 'BOOLEANO_LIT'):
            return 'TIPO_BOOLEANO'
        if tipo_nodo in ('LIT_CHAR', 'CARACTER_LIT'):
            return 'TIPO_CARACTER'

        # Variable: buscar en tabla
        if tipo_nodo == 'VAR':
            nombre = nodo.get('id')
            simbolo = self.tabla_simbolos.buscar(nombre)
            if simbolo:
                return self.normalizar_tipo(simbolo.get('tipo_dato', 'DESCONOCIDO'))
            else:
                self.reporte.agregar_error(CategoriaError.DECLARACION, f"Variable '{nombre}' no declarada", linea)
                return 'DESCONOCIDO'

        # Acceso a arreglo
        if tipo_nodo == 'ACCESO_ARREGLO':
            return self.verificar_acceso_arreglo(nodo)

        # Llamada a función / método
        if tipo_nodo in ('LLAMADA_FUNCION', 'LLAMADA_METODO'):
            id_func = nodo.get('id') or nodo.get('nombre')
            simbolo = self.tabla_simbolos.buscar(id_func) if id_func else None
            linea = nodo.get('linea', 0)
            if simbolo:
                # detectar funciones obsoletas si el símbolo lo indica
                if simbolo.get('obsoleta'):
                    self.reporte.agregar_error(CategoriaError.EJECUCION, f"Uso de función obsoleta '{id_func}'", linea, severidad="ADVERTENCIA")
                return self.normalizar_tipo(simbolo.get('tipo_dato', 'DESCONOCIDO'))
            else:
                self.reporte.agregar_error(CategoriaError.DECLARACION, f"Función '{id_func}' no declarada", linea)
                return 'DESCONOCIDO'

        # Operación unaria
        if tipo_nodo == 'UNARIO':
            return self.verificar_unario(nodo)

        # Operación binaria
        if tipo_nodo == 'BIN_OP':
            izq = nodo.get('izq')
            der = nodo.get('der')
            linea = nodo.get('linea', 0)
            op = self._normalizar_operacion(nodo.get('op'))

            # obtener tipos de subexpresiones
            tipo_izq = self.obtener_tipo_expresion(izq) if izq is not None else None
            tipo_der = self.obtener_tipo_expresion(der) if der is not None else None

            # operandos faltantes
            if tipo_izq is None or tipo_der is None:
                self.reporte.agregar_error(CategoriaError.TIPO, f"Operador '{op}' con operandos faltantes", linea)
                return 'DESCONOCIDO'

            # verificar compatibilidad
            if not self.verificar_compatibilidad(tipo_izq, tipo_der, op, linea):
                return 'DESCONOCIDO'

            # detectar división por cero literal
            if op in ['/', 'DIV', '%', 'MOD']:
                self.verificar_division_por_cero(nodo)

            # resultado según operación
            if op in ['+', '-', '*', '/', '%']:
                if 'TIPO_FLOTANTE' in (tipo_izq, tipo_der):
                    return 'TIPO_FLOTANTE'
                return 'TIPO_ENTERO'
            if op in ['==', '!=', '<', '>', '<=', '>=', '&&', '||']:
                return 'TIPO_BOOLEANO'

            return 'DESCONOCIDO'

        # Otros nodos no manejados
        return 'DESCONOCIDO'