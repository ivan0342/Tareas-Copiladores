import tkinter as tk
from tkinter import ttk, messagebox
from analizador_lexico import AnalizadorLexico
from tabla_simbolos import TablaSimbolos
from analizador_sintactico import AnalizadorSintactico

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

        boton_analizar = ttk.Button(self.ventana, text="Copilar", command=self.analizar_texto)
        boton_analizar.pack(pady=10)
        
        # Botón Ver tabla de símbolos
        boton_tabla = ttk.Button(self.ventana, text="Ver tabla de símbolos", command=self.mostrar_tabla)
        boton_tabla.pack(pady=10)

    def mostrar_resultados(self):
        ventana_resultados = tk.Toplevel(self.ventana)
        ventana_resultados.title("Resultados")
        ventana_resultados.geometry("800x500")

        lado_der = ttk.LabelFrame(ventana_resultados, text="Tabla de tokens")
        lado_der.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        lado_izq = ttk.LabelFrame(ventana_resultados, text="Errores léxicos")
        lado_izq.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # Treeview para mostrar tokens (no sobrescribe self.tabla_simbolos)
        self.tabla_tokens_tree = ttk.Treeview(lado_der, columns=("Token", "Tipo", "Línea"), show="headings")
        self.tabla_tokens_tree.heading("Token", text="Token")
        self.tabla_tokens_tree.heading("Tipo", text="Tipo de token")
        self.tabla_tokens_tree.heading("Línea", text="Línea")
        self.tabla_tokens_tree.pack(fill="both", expand=True)

        self.area_errores = tk.Text(lado_izq, wrap=tk.WORD, font=("Consolas", 12), fg="red")
        self.area_errores.pack(fill="both", expand=True)

    def analizar_texto(self):
        texto = self.text_area.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showinfo("Aviso", "No hay texto para analizar.")
            return

        tokens, errores = self.analizador.analizar(texto)

        self.mostrar_resultados()

        # Mostrar tokens en Treeview
        for token in tokens:
            self.tabla_tokens_tree.insert(
                "", tk.END,
                values=(token["token"], token["tipo"], token["linea"])
            )

        # Mostrar errores
        if errores:
            for e in errores:
                self.area_errores.insert(
                    tk.END,
                    f"[Línea {e['linea']}, {e['tipo']}: '{e['token']}'\n"
                )
        else:
            self.area_errores.insert(tk.END, "No se encontraron errores léxicos.\n")
            
        
         # Analizador sintáctico
        errores_sint = self.analizador_sintactico.analizar(tokens)
        if errores_sint:
            messagebox.showerror("Errores Sintácticos", "\n".join(errores_sint))
        else:
            messagebox.showinfo("Compilación", "Código sintácticamente correcto.")

            
    #mostrar la tabla de simbolos del analizador sintactico
    def mostrar_tabla(self):
        if not self.tabla_simbolos:
            messagebox.showinfo("Aviso", "No hay tabla de símbolos disponible.")
            return

        ventana_tabla = tk.Toplevel(self.ventana)
        ventana_tabla.title("Tabla de Símbolos")
        ventana_tabla.geometry("700x500")

        # Definir columnas
        tabla = ttk.Treeview(ventana_tabla, columns=(
            "Identificador", "Categoria", "Tipo_dato", "Linea", "Ambito",
            "Direccion", "Valor", "Estado", "Estructura", "Contador"
        ), show="headings")

        # Definir encabezados individualmente
        tabla.heading("Identificador", text="Identificador")
        tabla.heading("Categoria", text="Categoría")
        tabla.heading("Tipo_dato", text="Tipo de dato")
        tabla.heading("Linea", text="Línea")
        tabla.heading("Ambito", text="Ámbito")
        tabla.heading("Direccion", text="Dirección")
        tabla.heading("Valor", text="Valor")
        tabla.heading("Estado", text="Estado")
        tabla.heading("Estructura", text="Estructura")
        tabla.heading("Contador", text="Contador de referencias")

        # Ajustar ancho de columnas
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

        # Insertar todos los símbolos de memoria + overflow
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
