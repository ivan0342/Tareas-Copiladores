class VerificadorTipos:
    def __init__(self, tabla_simbolos):
        self.tabla_simbolos = tabla_simbolos
        self.errores = []

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
                self.errores.append(f"Línea {linea}: Operación '{op}' no válida entre {tipo1} y {tipo2}")
                return False

        # Comparaciones
        if op in ['==', '!=', '<', '>', '<=', '>=']:
            if tipo1_norm == tipo2_norm or (tipo1_norm in ['TIPO_ENTERO', 'TIPO_FLOTANTE'] and tipo2_norm in ['TIPO_ENTERO', 'TIPO_FLOTANTE']):
                return True
            else:
                self.errores.append(f"Línea {linea}: Comparación '{op}' no válida entre {tipo1} y {tipo2}")
                return False

        # Lógicas
        if op in ['&&', '||']:
            if tipo1_norm == 'TIPO_BOOLEANO' and tipo2_norm == 'TIPO_BOOLEANO':
                return True
            else:
                self.errores.append(f"Línea {linea}: Operación lógica '{op}' requiere booleanos")
                return False

        # Negación unaria '!'
        if op == '!':
            return True

        # Concatenación de cadenas (usamos '+' canónico)
        if op == '+':
            if tipo1_norm == 'TIPO_CADENA' and tipo2_norm == 'TIPO_CADENA':
                return True
            # si no son cadenas, puede ser suma aritmética (ya tratada arriba)
            # si llegamos aquí, no es válida para cadenas
            # no añadimos error aquí porque pudo entrar por otra rama

        # Por defecto permitir (pero mejor no confiar)
        return True

    def verificar_asignacion(self, tipo_variable, tipo_valor, linea):
        """Verifica compatibilidad en asignaciones"""
        tipo_var_norm = self.normalizar_tipo(tipo_variable)
        tipo_val_norm = self.normalizar_tipo(tipo_valor)

        if tipo_var_norm == tipo_val_norm:
            return True

        # Conversiones implícitas permitidas
        if tipo_var_norm == 'TIPO_FLOTANTE' and tipo_val_norm == 'TIPO_ENTERO':
            return True

        # Permitir asignar de referencia <ref:...> a variables si se maneja por otra lógica (no aquí)
        self.errores.append(f"Línea {linea}: Asignación incompatible - variable: {tipo_variable}, valor: {tipo_valor}")
        return False

    def obtener_tipo_expresion(self, nodo):
        """Determina el tipo de una expresión AST"""
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
                        self.errores.append(f"Línea {nodo.get('linea', 0)}: Variable '{nombre}' no declarada")
                        return 'DESCONOCIDO'

        # Llamada a función: idealmente deberías consultar la tabla de símbolos para el tipo de retorno
        if tipo_nodo == 'LLAMADA_FUNCION' or tipo_nodo == 'LLAMADA_METODO':
            # Intentar buscar la función en la tabla
            id_func = nodo.get('id') or nodo.get('nombre')
            simbolo = self.tabla_simbolos.buscar(id_func) if id_func else None
            if simbolo:
                return self.normalizar_tipo(simbolo.get('tipo_dato', 'DESCONOCIDO'))
            return 'DESCONOCIDO'

        # Operación binaria/unaria
        if tipo_nodo == 'BIN_OP' or tipo_nodo == 'UNARIO':
            # obtener tipos de subexpresiones
            izq = nodo.get('izq')
            der = nodo.get('der')

            tipo_izq = self.obtener_tipo_expresion(izq) if izq is not None else None
            tipo_der = self.obtener_tipo_expresion(der) if der is not None else None

            # Normalizar la operación (acepta tokens como 'MAS' o símbolos '+')
            op = self._normalizar_operacion(nodo.get('op'))

            # Verificar compatibilidad (si no hay lado izquierdo o derecho, tratar según operador)
            if not self.verificar_compatibilidad(tipo_izq, tipo_der, op, nodo.get('linea', 0)):
                return 'DESCONOCIDO'

            # Determinar tipo resultante según la operación canónica
            if op in ['+', '-', '*', '/', '%']:
                if 'TIPO_FLOTANTE' in (tipo_izq, tipo_der):
                    return 'TIPO_FLOTANTE'
                return 'TIPO_ENTERO'
            if op in ['==', '!=', '<', '>', '<=', '>=', '&&', '||']:
                return 'TIPO_BOOLEANO'

            # Si es concatenación o algo más: usar reglas específicas si existen
            return 'DESCONOCIDO'

        return 'DESCONOCIDO'
