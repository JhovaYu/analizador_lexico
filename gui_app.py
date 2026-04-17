import customtkinter as ctk
from lexer import DFALexer
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import Counter

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LexerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Analizador Léxico - Python DFA")
        self.geometry("1100x700")

        self.lexer = DFALexer()

        # Grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0) # Title
        self.grid_rowconfigure(1, weight=3) # Input & Table
        self.grid_rowconfigure(2, weight=2) # Chart

        # 1. Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        self.label_title = ctk.CTkLabel(self.header_frame, text="Analizador Léxico (DFA)", font=("Roboto", 24, "bold"))
        self.label_title.pack(pady=10)

        # 2. Input Area (Left)
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        self.label_input = ctk.CTkLabel(self.input_frame, text="Código Fuente:", font=("Roboto", 16))
        self.label_input.pack(pady=5, padx=10, anchor="w")
        
        self.textbox_input = ctk.CTkTextbox(self.input_frame, font=("Consolas", 14))
        self.textbox_input.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.btn_analyze = ctk.CTkButton(self.input_frame, text="Analizar", command=self.analyze_code, height=40)
        self.btn_analyze.pack(fill="x", padx=10, pady=5)
        
        self.btn_clear = ctk.CTkButton(self.input_frame, text="Limpiar", command=self.clear_code, fg_color="gray", hover_color="darkgray")
        self.btn_clear.pack(fill="x", padx=10, pady=(0, 10))

        # 3. Results Table (Right)
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=(0, 10))
        
        self.label_table = ctk.CTkLabel(self.table_frame, text="Tabla de Tokens:", font=("Roboto", 16))
        self.label_table.pack(pady=5, padx=10, anchor="w")
        
        # Use a Textbox for simple table display or create a custom frame for a grid
        # For simplicity and style, a readonly Textbox or scrollable frame with labels is good.
        # Let's use a ScrollableFrame for a structured table look.
        self.scroll_table = ctk.CTkScrollableFrame(self.table_frame)
        self.scroll_table.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Table Headers
        headers = ["Token", "Atributo", "Tipo", "Línea"]
        self.data_widgets = []
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.scroll_table, text=h, font=("Roboto", 14, "bold"), anchor="w")
            lbl.grid(row=0, column=i, sticky="ew", padx=5, pady=5)
            self.scroll_table.grid_columnconfigure(i, weight=1)

        # 4. Visualization (Bottom)
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        
        self.fig = plt.Figure(figsize=(6, 2.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self.ax.set_title("Frecuencia de Tokens")
        self.ax.set_facecolor('#2b2b2b') # Matches dark theme typically
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')
        
    def clear_code(self):
        self.textbox_input.delete("0.0", "end")
        self.label_table.configure(text="Tabla de Tokens:")
        self.reset_table()
        self.reset_chart()

    def reset_table(self):
        # Remove only data widgets, keep headers
        for widget in self.data_widgets:
            widget.destroy()
        self.data_widgets = []

    def reset_chart(self):
        self.ax.clear()
        self.ax.set_title("Frecuencia de Tokens")
        self.ax.set_facecolor('#2b2b2b')
        self.canvas.draw()

    def analyze_code(self):
        code = self.textbox_input.get("0.0", "end")
        if not code.strip():
            # Optional: Show a warning if empty?
            return
            
        try:
            tokens = self.lexer.tokenize(code)
            
            # Update Status/Results (visual feedback)
            self.label_table.configure(text=f"Tabla de Tokens: ({len(tokens)} encontrados)")
        except Exception as e:
            # Simple error logging or popup could go here
            print(f"Error during analysis: {e}")
            return
        
        # Populate Table
        self.reset_table()
        
        for idx, t in enumerate(tokens, start=1):
            values = [t['token'], str(t['attribute']), t['type'], str(t['line'])]
            for col, val in enumerate(values):
                lbl = ctk.CTkLabel(self.scroll_table, text=val, anchor="w", font=("Consolas", 12))
                lbl.grid(row=idx, column=col, sticky="ew", padx=5, pady=2)
                self.data_widgets.append(lbl) # Track it
        
        # Populate Chart
        self.update_chart(tokens)
        
    def update_chart(self, tokens):
        self.ax.clear()
        
        if not tokens:
            self.canvas.draw()
            return
            
        types = [t['type'] for t in tokens]
        counts = Counter(types)
        
        labels = list(counts.keys())
        values = list(counts.values())
        
        # Bar chart
        bars = self.ax.barh(labels, values, color='#1f6aa5') # CustomTkinter blue-ish
        self.ax.set_title("Distribución de Tipos de Token")
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(axis='y', labelsize=8)
        self.fig.tight_layout()
        
        self.canvas.draw()

if __name__ == "__main__":
    app = LexerApp()
    app.mainloop()
