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
        self.ventana.geometry("800x700")

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

    def mostrar_resultados_errores(self, errores_lex, errores_sint):
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

        # Mostrar ventanas automáticamente
        self.mostrar_resultados_errores(errores_lex, errores_sint)
        self.mostrar_tabla_tokens(tokens)

        # También mostrar tabla de símbolos actualizada
        self.mostrar_tabla()

    def mostrar_tabla(self):
        if not self.tabla_simbolos:
            messagebox.showinfo("Aviso", "No hay tabla de símbolos disponible.")
            return

        ventana_tabla = tk.Toplevel(self.ventana)
        ventana_tabla.title("Tabla de Símbolos")
        ventana_tabla.geometry("700x500")

        tabla = ttk.Treeview(ventana_tabla, columns=(
            "Identificador", "Categoria", "Tipo_dato", "Linea", "Ambito",
            "Direccion", "Valor", "Estado", "Estructura", "Contador"
        ), show="headings")

        for col in tabla["columns"]:
            tabla.heading(col, text=col)
        tabla.column("Identificador", width=120)
        tabla.column("Categoria", width=100)
        tabla.column("Tipo_dato", width=100)
        tabla.column("Linea", width=50)
        tabla.column("Ambito", width=100)
        tabla.column("Direccion", width=80)
        tabla.column("Valor", width=150)
        tabla.column("Estado", width=100)
        tabla.column("Estructura", width=100)
        tabla.column("Contador", width=80)

        tabla.pack(fill="both", expand=True)

        for s in self.tabla_simbolos.obtener_todos():
            tabla.insert("", tk.END, values=(
                s.get("identificador", ""),
                s.get("categoria", ""),
                s.get("tipo_dato", ""),
                s.get("linea", ""),
                s.get("ambito", ""),
                s.get("direccion", ""),
                s.get("valor", ""),
                s.get("estado", ""),
                s.get("estructura", ""),
                s.get("contador_referencias", 0)
            ))

    def ejecutar(self):
        self.ventana.mainloop()


if __name__ == "__main__":
    app = Interfaz()
    app.ejecutar()
