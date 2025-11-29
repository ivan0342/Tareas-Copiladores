# visualizador_optimizacion.py
import json
import tkinter as tk
from tkinter import ttk, scrolledtext


class VisualizadorOptimizacion:
    def __init__(self, optimizador):
        self.optimizador = optimizador
        self.ventana = None

    def mostrar_comparacion(self):
        """Muestra ventana con comparación antes/después de optimización"""
        self.ventana = tk.Toplevel()
        self.ventana.title("🔍 Comparación de Optimización - Antes vs Después")
        self.ventana.geometry("1200x800")

        # Crear notebook (pestañas)
        notebook = ttk.Notebook(self.ventana)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña 1: Comparación de Scopes
        self._crear_pestana_scopes(notebook)

        # Pestaña 2: Métricas de Optimización
        self._crear_pestana_metricas(notebook)

        # Pestaña 3: Código Antes/Después
        self._crear_pestana_codigo(notebook)

        # Pestaña 4: Optimizaciones Aplicadas
        self._crear_pestana_optimizaciones(notebook)

    def _crear_pestana_scopes(self, notebook):
        """Crea pestaña de comparación de scopes"""
        frame_scopes = ttk.Frame(notebook)
        notebook.add(frame_scopes, text="🔍 Scopes y Variables")

        # Crear frame dividido
        frame_comparacion = ttk.Frame(frame_scopes)
        frame_comparacion.pack(fill="both", expand=True)

        # Columna izquierda: Antes
        frame_antes = ttk.LabelFrame(frame_comparacion, text="🔄 Scopes ANTES de Optimización")
        frame_antes.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        texto_antes = scrolledtext.ScrolledText(frame_antes, wrap=tk.WORD, width=50, height=20)
        texto_antes.pack(fill="both", expand=True, padx=5, pady=5)
        texto_antes.insert(tk.END, self._formatear_scopes(self.optimizador.scopes_antes))
        texto_antes.config(state="disabled")

        # Columna derecha: Después
        frame_despues = ttk.LabelFrame(frame_comparacion, text="🚀 Scopes DESPUÉS de Optimización")
        frame_despues.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        texto_despues = scrolledtext.ScrolledText(frame_despues, wrap=tk.WORD, width=50, height=20)
        texto_despues.pack(fill="both", expand=True, padx=5, pady=5)
        texto_despues.insert(tk.END, self._formatear_scopes(self.optimizador.scopes_despues))
        texto_despues.config(state="disabled")

    def _formatear_scopes(self, scopes_dict):
        """Formatea los scopes para visualización"""
        if not scopes_dict:
            return "No hay scopes para mostrar\n"

        texto = ""
        for scope, variables in scopes_dict.items():
            texto += f"\n📁 {scope}:\n"
            for var in variables:
                ref_text = f" ({var['referencias']} refs)" if var['referencias'] > 0 else " (sin referencias)"
                texto += f"   • {var['nombre']}: {var['tipo']}{ref_text}\n"

        return texto

    def _crear_pestana_metricas(self, notebook):
        """Crea pestaña de métricas de optimización"""
        frame_metricas = ttk.Frame(notebook)
        notebook.add(frame_metricas, text="📊 Métricas")

        texto_metricas = scrolledtext.ScrolledText(frame_metricas, wrap=tk.WORD, height=20)
        texto_metricas.pack(fill="both", expand=True, padx=10, pady=10)

        metricas = self._calcular_metricas_completas()
        texto_metricas.insert(tk.END, metricas)
        texto_metricas.config(state="disabled")

    def _calcular_metricas_completas(self):
        """Calcula métricas completas de la optimización"""
        metricas = "=== 📊 MÉTRICAS DE OPTIMIZACIÓN COMPLETA ===\n\n"

        # Métricas por nivel
        for nivel in ['local', 'bucles', 'global']:
            if nivel in self.optimizador.metricas:
                m = self.optimizador.metricas[nivel]
                metricas += f"🔧 {nivel.upper()}:\n"
                metricas += f"   • Optimizaciones aplicadas: {m['aplicadas']}\n"
                metricas += f"   • Tiempo de ejecución: {m['tiempo']:.4f}s\n"
                metricas += f"   • Reducción de código: {m['reduccion_codigo']} líneas\n\n"

        # Métricas de scopes
        scopes_antes = len(self.optimizador.scopes_antes)
        scopes_despues = len(self.optimizador.scopes_despues)
        vars_antes = sum(len(vars) for vars in self.optimizador.scopes_antes.values())
        vars_despues = sum(len(vars) for vars in self.optimizador.scopes_despues.values())

        metricas += "=== 🔍 ANÁLISIS DE SCOPES ===\n"
        metricas += f"Scopes antes: {scopes_antes}\n"
        metricas += f"Scopes después: {scopes_despues}\n"
        metricas += f"Variables antes: {vars_antes}\n"
        metricas += f"Variables después: {vars_despues}\n"
        metricas += f"Reducción de variables: {vars_antes - vars_despues}\n\n"

        # Eficiencia
        total_optimizaciones = sum(m['aplicadas'] for m in self.optimizador.metricas.values())
        total_tiempo = sum(m['tiempo'] for m in self.optimizador.metricas.values())
        total_reduccion = sum(m['reduccion_codigo'] for m in self.optimizador.metricas.values())

        metricas += "=== ⚡ EFICIENCIA GENERAL ===\n"
        metricas += f"Total optimizaciones: {total_optimizaciones}\n"
        metricas += f"Tiempo total: {total_tiempo:.4f}s\n"
        metricas += f"Reducción total: {total_reduccion} líneas\n"
        metricas += f"Optimizaciones/segundo: {total_optimizaciones / max(total_tiempo, 0.001):.2f}\n"

        return metricas

    def _crear_pestana_codigo(self, notebook):
        """Crea pestaña de comparación de código"""
        frame_codigo = ttk.Frame(notebook)
        notebook.add(frame_codigo, text="📝 Código")

        # Frame dividido para antes/después
        frame_comparacion = ttk.Frame(frame_codigo)
        frame_comparacion.pack(fill="both", expand=True)

        # Antes
        frame_antes = ttk.LabelFrame(frame_comparacion, text="📄 Código ANTES")
        frame_antes.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        texto_antes = scrolledtext.ScrolledText(frame_antes, wrap=tk.WORD, width=50)
        texto_antes.pack(fill="both", expand=True, padx=5, pady=5)
        texto_antes.insert(tk.END, json.dumps(self.optimizador.ast_antes, indent=2))
        texto_antes.config(state="disabled")

        # Después
        frame_despues = ttk.LabelFrame(frame_comparacion, text="🚀 Código DESPUÉS")
        frame_despues.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        texto_despues = scrolledtext.ScrolledText(frame_despues, wrap=tk.WORD, width=50)
        texto_despues.pack(fill="both", expand=True, padx=5, pady=5)
        texto_despues.insert(tk.END, json.dumps(self.optimizador.ast_despues, indent=2))
        texto_despues.config(state="disabled")

    def _crear_pestana_optimizaciones(self, notebook):
        """Crea pestaña de optimizaciones aplicadas"""
        frame_opt = ttk.Frame(notebook)
        notebook.add(frame_opt, text="🔧 Optimizaciones")

        texto_opt = scrolledtext.ScrolledText(frame_opt, wrap=tk.WORD, height=20)
        texto_opt.pack(fill="both", expand=True, padx=10, pady=10)

        # Recopilar todas las optimizaciones aplicadas
        todas_optimizaciones = []
        for nivel in ['local', 'bucles', 'global']:
            if nivel in self.optimizador.metricas:
                optimizaciones = self.optimizador.metricas[nivel].get('optimizaciones', [])
                for opt in optimizaciones:
                    todas_optimizaciones.append(f"{nivel.upper()}: {opt}")

        texto_opt.insert(tk.END, "=== 🔧 OPTIMIZACIONES APLICADAS ===\n\n")
        for i, opt in enumerate(todas_optimizaciones, 1):
            texto_opt.insert(tk.END, f"{i}. {opt}\n")

        texto_opt.config(state="disabled")