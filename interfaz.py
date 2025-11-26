# archivo: interfaz.py
import tkinter as tk
from tkinter import ttk, messagebox
from analizador_lexico import AnalizadorLexico
from tabla_simbolos import TablaSimbolos
from analizador_sintactico import AnalizadorSintactico
from parser import Parser, ParserError


class Interfaz:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Analizador Léxico")
        self.ventana.geometry("1000x700")  # Un poco más ancha para los nuevos campos

        # Tabla de símbolos con desbordamiento
        self.tabla_simbolos = TablaSimbolos(capacidad_bytes=100, archivo_backup="tabla_overflow.json")

        # Analizador léxico con tabla de símbolos
        self.analizador = AnalizadorLexico(tabla_simbolos=self.tabla_simbolos)
        self.analizador_sintactico = AnalizadorSintactico(tabla_simbolos=self.tabla_simbolos)

        self.crear_interfaz()

    def crear_interfaz(self):
        frame_editor = ttk.LabelFrame(self.ventana, text="Editor de código")
        frame_editor.pack(fill="both", expand=True, padx=10, pady=10)

        self.text_area = tk.Text(frame_editor, wrap=tk.WORD, font=("Consolas", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)

        boton_analizar = ttk.Button(self.ventana, text="Compilar", command=self.analizar_texto)
        boton_analizar.pack(pady=10)

        boton_tabla = ttk.Button(self.ventana, text="Ver tabla de símbolos", command=self.mostrar_tabla)
        boton_tabla.pack(pady=10)

    def mostrar_resultados_errores(self, errores_lex, errores_sint, errores_semanticos):
        ventana_resultados = tk.Toplevel(self.ventana)
        ventana_resultados.title("Resultados del Análisis")
        ventana_resultados.geometry("900x700")

        # Crear notebook (pestañas)
        notebook = ttk.Notebook(ventana_resultados)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 1: Errores
        frame_errores = ttk.Frame(notebook)
        notebook.add(frame_errores, text="🚨 Errores")

        # Errores léxicos
        frame_lex = ttk.LabelFrame(frame_errores, text="Errores Léxicos")
        frame_lex.pack(fill="both", expand=True, padx=5, pady=5)

        area_errores_lex = tk.Text(frame_lex, wrap=tk.WORD, font=("Consolas", 10), fg="red")
        area_errores_lex.pack(fill="both", expand=True, padx=5, pady=5)

        if errores_lex:
            for e in errores_lex:
                area_errores_lex.insert(tk.END, f"Línea {e['linea']}: {e['tipo']} - '{e['token']}'\n")
        else:
            area_errores_lex.insert(tk.END, "✅ No se encontraron errores léxicos\n")
        area_errores_lex.config(state="disabled")
        
         # Pestaña 2: Errores semanticos
        frame_errore_semanticos = ttk.Frame(notebook)
        notebook.add(frame_errore_semanticos, text="🚨 Errores SEMANTICOS")

        # Errores léxicos
        frame_semanticos = ttk.LabelFrame(frame_errore_semanticos, text="Errores Semánticos")
        frame_semanticos.pack(fill="both", expand=True, padx=5, pady=5)

        area_errores_sem = tk.Text(frame_semanticos, wrap=tk.WORD, font=("Consolas", 10), fg="red")
        area_errores_sem.pack(fill="both", expand=True, padx=5, pady=5)

        if errores_semanticos:
            for e in errores_semanticos:
                area_errores_sem.insert(tk.END, f"{e}\n")
        else:
            area_errores_sem.insert(tk.END, "✅ No se encontraron errores semánticos\n")
        area_errores_sem.config(state="disabled")
        
        

        # Pestaña 2: Salida del Intérprete
        frame_salida = ttk.Frame(notebook)
        notebook.add(frame_salida, text="📊 Salida")

        area_salida = tk.Text(frame_salida, wrap=tk.WORD, font=("Consolas", 11),
                              bg="black", fg="white")
        area_salida.pack(fill="both", expand=True, padx=10, pady=10)

        scroll_salida = ttk.Scrollbar(frame_salida, command=area_salida.yview)
        area_salida.configure(yscrollcommand=scroll_salida.set)
        scroll_salida.pack(side="right", fill="y")
        


        # Procesar salida del intérprete
        salida_interprete = []
        errores_reales = []

        if errores_sint:
            for e in errores_sint:
                if isinstance(e, str) and e.startswith("SALIDA_INTERPRETE:"):
                    salida_interprete = errores_sint[errores_sint.index(e) + 1:]
                    break
                else:
                    errores_reales.append(e)

        
        # Mostrar en pestaña de salida
        if salida_interprete:
            area_salida.insert(tk.END, "=== EJECUCIÓN EXITOSA ===\n\n")
            for i, linea in enumerate(salida_interprete, 1):
                area_salida.insert(tk.END, f"[{i}] {linea}\n")
            area_salida.insert(tk.END, f"\n🎉 Programa ejecutado correctamente\n")
            area_salida.insert(tk.END, f"📋 Total de líneas de salida: {len(salida_interprete)}")
        else:
            area_salida.insert(tk.END, "=== SIN SALIDA ===\n\n")
            area_salida.insert(tk.END, "El programa no generó salida o no se ejecutó.\n\n")
            if errores_reales:
                area_salida.insert(tk.END, "Se encontraron errores durante el análisis:\n")
                for error in errores_reales:
                    area_salida.insert(tk.END, f"• {error}\n")

        area_salida.config(state="disabled")

    def mostrar_tabla_tokens(self, tokens):
        ventana_tokens = tk.Toplevel(self.ventana)
        ventana_tokens.title("Tabla de Tokens")
        ventana_tokens.geometry("600x400")

        frame_tree = ttk.Frame(ventana_tokens)
        frame_tree.pack(fill="both", expand=True)

        tabla_tokens = ttk.Treeview(frame_tree, columns=("Token", "Tipo", "Línea"), show="headings")
        tabla_tokens.heading("Token", text="Token")
        tabla_tokens.heading("Tipo", text="Tipo de token")
        tabla_tokens.heading("Línea", text="Línea")
        tabla_tokens.pack(side="left", fill="both", expand=True)

        scroll_tokens = ttk.Scrollbar(frame_tree, orient="vertical", command=tabla_tokens.yview)
        tabla_tokens.configure(yscrollcommand=scroll_tokens.set)
        scroll_tokens.pack(side="right", fill="y")

        # Insertar tokens
        for token in tokens:
            tabla_tokens.insert("", tk.END, values=(token["token"], token["tipo"], token["linea"]))

    def analizar_texto(self):
        texto = self.text_area.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showinfo("Aviso", "No hay texto para analizar.")
            return

        # Limpiar tabla de símbolos antes del análisis
        self.tabla_simbolos.memoria = []
        self.tabla_simbolos.overflow = []

        tokens, errores_lex = self.analizador.tokenize(texto)

        # Usar el analizador sintáctico que ya incluye el parser
        errores_sint = self.analizador_sintactico.analizar(tokens)
        
        errores_semanticos = self.analizador_sintactico.reporte_errores.errores
        # Mostrar ventanas automáticamente
        self.mostrar_resultados_errores(errores_lex, errores_sint, errores_semanticos)
        self.mostrar_tabla_tokens(tokens)

        # También mostrar tabla de símbolos actualizada
        self.mostrar_tabla()

    def mostrar_tabla(self):
        if not self.tabla_simbolos:
            messagebox.showinfo("Aviso", "No hay tabla de símbolos disponible.")
            return

        ventana_tabla = tk.Toplevel(self.ventana)
        ventana_tabla.title("Tabla de Símbolos - Información Extendida")
        ventana_tabla.geometry("1200x600")  # Más ancha para los nuevos campos

        # Crear notebook para diferentes vistas
        notebook = ttk.Notebook(ventana_tabla)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 1: Vista Completa
        frame_completo = ttk.Frame(notebook)
        notebook.add(frame_completo, text="Vista Completa")

        # Tabla con TODOS los campos (antiguos + nuevos)
        tabla = ttk.Treeview(frame_completo, columns=(
            "Identificador", "Categoria", "Tipo_dato", "Linea", "Ambito",
            "Direccion", "Valor", "Estado", "Estructura", "Contador",
            # NUEVOS CAMPOS:
            "Tamaño_bytes", "Es_constante", "Modificable", "Referencias", "Vivo"
        ), show="headings", height=20)

        # Configurar columnas
        columnas = [
            ("Identificador", 100),
            ("Categoria", 80),
            ("Tipo_dato", 90),
            ("Linea", 50),
            ("Ambito", 80),
            ("Direccion", 80),
            ("Valor", 120),
            ("Estado", 80),
            ("Estructura", 80),
            ("Contador", 70),
            # NUEVOS CAMPOS:
            ("Tamaño_bytes", 70),
            ("Es_constante", 80),
            ("Modificable", 80),
            ("Referencias", 80),
            ("Vivo", 50)
        ]

        for col, width in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=width)

        # Scrollbar
        scroll = ttk.Scrollbar(frame_completo, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)

        tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Poblar tabla con datos de la estructura extendida
        self._poblar_tabla_extendida(tabla)

        # Pestaña 2: Estadísticas
        frame_stats = ttk.Frame(notebook)
        notebook.add(frame_stats, text="Estadísticas")

        # Área de texto para estadísticas
        texto_stats = tk.Text(frame_stats, wrap=tk.WORD, font=("Consolas", 10), height=15)
        texto_stats.pack(fill="both", expand=True, padx=10, pady=10)

        # Generar estadísticas
        stats = self._generar_estadisticas()
        texto_stats.insert(tk.END, stats)
        texto_stats.config(state="disabled")

        # Pestaña 3: Análisis Optimización
        frame_opt = ttk.Frame(notebook)
        notebook.add(frame_opt, text="Análisis Optimización")

        # Área de texto para análisis
        texto_opt = tk.Text(frame_opt, wrap=tk.WORD, font=("Consolas", 10), height=15)
        texto_opt.pack(fill="both", expand=True, padx=10, pady=10)

        # Generar análisis de optimización
        analisis = self._generar_analisis_optimizacion()
        texto_opt.insert(tk.END, analisis)
        texto_opt.config(state="disabled")

    def _poblar_tabla_extendida(self, tabla):
        """Pobla la tabla con datos de la estructura extendida"""
        # USAR SOLO LA ESTRUCTURA EXTENDIDA

        # Variables normales
        for nombre, variable in self.tabla_simbolos.variables_extendidas.items():
            tabla.insert("", tk.END, values=(
                nombre,
                "variable",
                variable.tipo_dato,
                variable.linea_declaracion,
                variable.ambito,
                variable.direccion_relativa or "N/A",
                variable.valor,
                variable.estado,
                "-",
                variable.contador_referencias,
                # NUEVOS CAMPOS:
                variable.tamanio_bytes,
                "No",  # No es constante
                "Sí",  # Modificable
                variable.contador_referencias,
                "Sí" if variable.vivo else "No"
            ))

        # Constantes
        for nombre, constante in self.tabla_simbolos.constantes_extendidas.items():
            tabla.insert("", tk.END, values=(
                nombre,
                "constante",
                constante.tipo_dato,
                constante.linea_declaracion,
                constante.ambito,
                constante.direccion_relativa or "N/A",
                constante.valor,
                constante.estado,
                "-",
                constante.contador_referencias,
                # NUEVOS CAMPOS:
                constante.tamanio_bytes,
                "Sí",  # Es constante
                "No",  # No modificable
                constante.contador_referencias,
                "Sí" if constante.vivo else "No"
            ))

        # ✅ IGNORAR COMPLETAMENTE LA ESTRUCTURA ANTIGUA
        print(
            f"DEBUG: Tabla poblada con {len(self.tabla_simbolos.variables_extendidas)} variables y {len(self.tabla_simbolos.constantes_extendidas)} constantes")

    def _generar_estadisticas(self):
        """Genera estadísticas de la tabla de símbolos"""
        stats_text = "=== ESTADÍSTICAS DE LA TABLA DE SÍMBOLOS ===\n\n"

        # ✅ USAR SOLO ESTRUCTURA EXTENDIDA
        variables = len(self.tabla_simbolos.variables_extendidas)
        constantes = len(self.tabla_simbolos.constantes_extendidas)
        funciones = len(self.tabla_simbolos.funciones_extendidas)
        clases = len(self.tabla_simbolos.clases_extendidas)

        stats_text += f"📊 CONTEO DE SÍMBOLOS:\n"
        stats_text += f"• Variables: {variables}\n"
        stats_text += f"• Constantes: {constantes}\n"
        stats_text += f"• Funciones: {funciones}\n"
        stats_text += f"• Clases: {clases}\n"
        stats_text += f"• Total: {variables + constantes + funciones + clases}\n\n"

        # Uso de memoria
        uso_memoria = self.tabla_simbolos.obtener_uso_memoria_extendido()
        stats_text += f"💾 USO DE MEMORIA:\n"
        stats_text += f"• Memoria utilizada: {uso_memoria['memoria_utilizada_bytes']} bytes\n"
        stats_text += f"• Capacidad total: {uso_memoria['capacidad_total_bytes']} bytes\n"
        stats_text += f"• Porcentaje de uso: {uso_memoria['porcentaje_uso']}\n\n"

        # Variables por ámbito
        stats_text += f"🏷️ VARIABLES POR ÁMBITO:\n"
        for ambito, count in uso_memoria['variables_por_ambito'].items():
            stats_text += f"• {ambito}: {count} variables\n"

        return stats_text

    def _generar_analisis_optimizacion(self):
        """Genera análisis para optimización CORREGIDO"""
        analisis_text = "=== ANÁLISIS PARA OPTIMIZACIÓN ===\n\n"

        # ✅ DEBUG DETALLADO: Mostrar contadores actuales CORREGIDO
        analisis_text += "🔍 CONTADORES DE REFERENCIAS ACTUALES:\n"

        # Variables normales - CORREGIDO: Usar estructura extendida
        for nombre, variable in self.tabla_simbolos.variables_extendidas.items():
            analisis_text += f"  • {nombre}: {variable.contador_referencias} referencias\n"

        # Constantes
        for nombre, constante in self.tabla_simbolos.constantes_extendidas.items():
            analisis_text += f"  • {nombre} (constante): {constante.contador_referencias} referencias\n"

        analisis_text += "\n"

        # Variables no utilizadas (basado en contador == 0) - CORREGIDO
        no_utilizadas = []
        for nombre, variable in self.tabla_simbolos.variables_extendidas.items():
            if variable.contador_referencias == 0:
                no_utilizadas.append(nombre)

        analisis_text += f"🚫 VARIABLES NO UTILIZADAS: {len(no_utilizadas)}\n"
        if no_utilizadas:
            for var in no_utilizadas:
                info = self.tabla_simbolos.variables_extendidas.get(var)
                if info:
                    analisis_text += f"  • {var} - {info.tipo_dato} ({info.tamanio_bytes} bytes)\n"
        else:
            analisis_text += "  ✓ No hay variables no utilizadas\n"

        analisis_text += "\n"

        # Variables muertas
        muertas = self.tabla_simbolos.obtener_variables_muertas_extendidas()
        analisis_text += f"💀 VARIABLES MUERTAS: {len(muertas)}\n"
        if muertas:
            for var in muertas:
                info = self.tabla_simbolos.variables_extendidas.get(var)
                if info:
                    analisis_text += f"  • {var} - Referencias: {info.contador_referencias}\n"
        else:
            analisis_text += "  ✓ No hay variables muertas\n"

        analisis_text += "\n💡 RECOMENDACIONES:\n"

        if no_utilizadas:
            analisis_text += "• Eliminar variables no utilizadas para ahorrar memoria\n"
        if muertas:
            analisis_text += "• Reutilizar variables muertas para optimizar memoria\n"

        uso_memoria = self.tabla_simbolos.obtener_uso_memoria_extendido()
        if float(uso_memoria['porcentaje_uso'].replace('%', '')) > 70:
            analisis_text += "• Alto uso de memoria - considerar optimización\n"

        if not no_utilizadas and not muertas:
            analisis_text += "• El código está bien optimizado en términos de uso de variables\n"

        return analisis_text

#---------------------------------------------------------------

    def ejecutar(self):
        self.ventana.mainloop()


if __name__ == "__main__":
    app = Interfaz()
    app.ejecutar()