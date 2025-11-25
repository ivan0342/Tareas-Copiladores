#calsificacion_errores.py
from enum import Enum

class CategoriaError(Enum):
    TIPO = "Error de Tipo"
    DECLARACION = "Error de Declaración"
    INICIALIZACION = "Error de Inicialización"
    FUNCION = "Error de Función"
    EJECUCION = "Error de Ejecución Potencial"


class ErrorSemantico:
    def __init__(self, categoria: CategoriaError, mensaje: str, linea: int, severidad="ERROR"):
        self.categoria = categoria
        self.mensaje = mensaje
        self.linea = linea
        self.severidad = severidad

    def __str__(self):
        return f"{self.categoria.value} en línea {self.linea}: {self.mensaje}"


class ReporteErrores:
    def __init__(self):
        self.errores = []

    def agregar_error(self, categoria: CategoriaError, mensaje: str, linea: int, severidad="ERROR"):
        self.errores.append(ErrorSemantico(categoria, mensaje, linea, severidad))
        print("TODOS LOS ERROREEEEEEEEEEES")
        for i, error in enumerate(self.errores):
            print(f"🔥 ERROR REGISTRADO:{i} {error}")

    def obtener_errores_por_categoria(self, categoria: CategoriaError):
        return [e for e in self.errores if e.categoria == categoria]

    def generar_reporte_completo(self):
        """Genera un diccionario con los errores organizados por categoría."""
        reporte = {}
        for categoria in CategoriaError:
            reporte[categoria.value] = self.obtener_errores_por_categoria(categoria)
        return reporte

    def tiene_errores(self):
        return len(self.errores) > 0

    def limpiar(self):
        self.errores.clear()
