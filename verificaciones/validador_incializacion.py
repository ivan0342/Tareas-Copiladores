# validador_inicializacion.py
from .clasificacion_errores import CategoriaError, ReporteErrores
from tabla_simbolos import TablaSimbolos 
   
class ValidadorInicializacion:
    def __init__(self, tabla_simbolos, reporte_errores):
        self.tabla_simbolos = tabla_simbolos
        self.errores = []
        self.reporte = reporte_errores
    
    def verificar_variable_no_inicializada(self, nombre, linea):
        """Detecta uso de variables no inicializadas"""
        simbolo = self.tabla_simbolos.buscar(nombre)
        if simbolo and simbolo.get('estado') == 'declarado' and simbolo.get('valor') is None:
            self.reporte.agregar_error(CategoriaError.INICIALIZACION, f"Variable '{nombre}' no inicializada", linea)
            print(f"🔥 ERROR: Variable '{nombre}' no inicializada en línea {linea}")
            return False
        return True
    
    def verificar_modificacion_constante(self, nombre, linea):
        """Detecta intento de modificar constantes"""
        simbolo = self.tabla_simbolos.buscar(nombre)
        if simbolo and simbolo.get('categoria') == 'constante':
            self.errores.append(f"Línea {linea}: No se puede modificar la constante '{nombre}'")
            self.reporte.agregar_error(CategoriaError.INICIALIZACION, f"No se puede modificar la constante '{nombre}'", linea)
            print(f"🔥 ERROR: No se puede modificar la constante '{nombre}' en línea {linea}")
            return False
        return True