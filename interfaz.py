import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from lexico import Lexico
from analizador import Analizador

class Interfaz:
    def __init__(self):
        self.ventana  = tk.Tk()
        self.ventana.title("Analizador Lexico")
        self.ventana.geometry("700x700")
        self.lexico = Lexico()
        self.analizador = Analizador()
        self.creacion_interfaz()
        
    def creacion_interfaz(self):
        editor = ttk.Frame(self.ventana);
        editor.pack(pady=10, padx=10)
        
        #self.area_texto = tk.Text(editor, wrap=tk.WORD, font=("Consolas", 12))
        
        self.text_area = tk.Text(editor, wrap=tk.WORD, font=("Consolas", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)

        # Botón para analizar texto
        boton_analizar = ttk.Button(self.ventana, text="Analizar", command= self.analizar_texto)
        boton_analizar.pack(pady=10)
        
              
        
        
    def mostrar_resultados(self, texto):
        ventana_resultados = tk.Toplevel(self.ventana)
        ventana_resultados.title("Resultados del analizador léxico")
        ventana_resultados.geometry("700x500")

        # --- Crear marcos principales ---
        lado_der = ttk.LabelFrame(ventana_resultados, text="Tabla de símbolos")
        lado_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        lado_izq = ttk.LabelFrame(ventana_resultados, text="Errores léxicos")
        lado_izq.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # --- Tabla de símbolos ---
        self.tabla_simbolos = ttk.Treeview(lado_der, columns=("Tipo", "Token"), show="headings")
        self.tabla_simbolos.heading("Tipo", text="Tipo de token")
        self.tabla_simbolos.heading("Token", text="Token")
        self.tabla_simbolos.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Área de errores ---
        self.area_errores = tk.Text(lado_izq, wrap=tk.WORD, font=("Consolas", 12), fg="red")
        self.area_errores.pack(fill="both", expand=True, padx=5, pady=5)
        
        
    def analizar_texto(self):
       texto = self.text_area.get("1.0", tk.END).strip()
       if texto == "":
            messagebox.showinfo("Aviso", "No hay texto para analizar.")
            return
       
       
       tokens, errores = self.analizador.analizador(texto)
        
       self.mostrar_resultados(texto)
       
        # Mostrar tokens válidos
       for token in tokens:
            self.tabla_simbolos.insert("", tk.END, values=(token["token"], token["tipo"]))

        # Mostrar errores léxicos
       if errores:
            for e in errores:
                self.area_errores.insert(
                    tk.END,
                    f"Token no válido '{e['token']}' en línea {e['linea']}, columna {e['columna']}\n"
                )
       else:
            self.area_errores.insert(tk.END, "No se encontraron errores léxicos.\n")
       
    
    def ejecutar(self):
        self.ventana.mainloop()
        
        

app = Interfaz()
app.ejecutar()

        
        
       
       