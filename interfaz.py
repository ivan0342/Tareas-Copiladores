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
        ventana_resultados.title("Resultados")
        ventana_resultados.geometry("900x500")

        # Configurar grid de 2 columnas
        frame = ttk.Frame(ventana_resultados)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        # Errores léxicos
        lado_izq = ttk.LabelFrame(frame, text="Errores léxicos")
        lado_izq.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        area_errores = tk.Text(lado_izq, wrap=tk.WORD, font=("Consolas", 12), fg="red")
        area_errores.pack(fill="both", expand=True)
        scroll_lex = ttk.Scrollbar(lado_izq, command=area_errores.yview)
        area_errores.configure(yscrollcommand=scroll_lex.set)
        scroll_lex.pack(side="right", fill="y")

        # Mostrar errores léxicos
        if errores_lex:
            for e in errores_lex:
                area_errores.insert(tk.END, f"[Línea {e['linea']}, {e['tipo']}: '{e['token']}']\n")
        else:
            area_errores.insert(tk.END, "No se encontraron errores léxicos.\n")

        # Errores sintácticos
        lado_der = ttk.LabelFrame(frame, text="Errores sintácticos")
        lado_der.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        area_errores_sint = tk.Text(lado_der, wrap=tk.WORD, font=("Consolas", 12), fg="purple")
        area_errores_sint.pack(fill="both", expand=True)
        scroll_sint = ttk.Scrollbar(lado_der, command=area_errores_sint.yview)
        area_errores_sint.configure(yscrollcommand=scroll_sint.set)
        scroll_sint.pack(side="right", fill="y")

        # Mostrar errores sintácticos
        if errores_sint:
            for e in errores_sint:
                area_errores_sint.insert(tk.END, f"{e}\n")
        else:
            area_errores_sint.insert(tk.END, "No se encontraron errores sintácticos.\n")

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

        tokens, errores_lex = self.analizador.tokenize(texto)

        # Analizador sintáctico
        parser = Parser(tokens, self.tabla_simbolos)
        ast = parser.parse()
        errores_parser = parser.errores
        errores_sint = self.analizador_sintactico.analizar(tokens)
        # Combinar errores sintácticos del parser y del analizador
        errores_sint_total = errores_parser + errores_sint

        # Mostrar ventanas automáticamente
        self.mostrar_resultados_errores(errores_lex, errores_sint_total)
        self.mostrar_tabla_tokens(tokens)

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
