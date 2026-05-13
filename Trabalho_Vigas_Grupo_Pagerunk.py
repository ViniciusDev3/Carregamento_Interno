import math
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from PIL import Image

# LÓGICA DE CÁLCULO

class viga:
    def __init__ (self, comprimento, tipo_apoio="biapoiada"):
        self.Comprimento = comprimento
        self.tipo_apoio = tipo_apoio
        self.cargas = []
        self.reacoes = {"Ra": 0, "Rb": 0, "Ma": 0}
        self.posA = 0.0
        self.posB = 0.0

    def add_carga(self, carga):
        self.cargas.append(carga)

    def calcular_reacoes(self, posA, posB=0):
        self.posA, self.posB = posA, posB
        sFy, sM = 0, 0
        for c in self.cargas:
            if isinstance(c, CarregamentoConcentrado):
                sFy += c.Forca
                sM += c.Forca * (c.Posicao - posA)
            elif isinstance(c, CarregamentoDistribuido):
                L = c.PosicaoF - c.PosicaoI
                if L <= 0: continue
                F = (c.ForcaI + c.ForcaF) * L / 2
                centroide = (L * (c.ForcaI + 2 * c.ForcaF) / (3 * (c.ForcaI + c.ForcaF))) if (c.ForcaI + c.ForcaF) != 0 else L/2
                sFy += F
                sM += F * (c.PosicaoI + centroide - posA)
            elif isinstance(c, MomentoConcentrado):
                sM += c.Magnitude

        if self.tipo_apoio == "biapoiada":
            d = (posB - posA) if (posB - posA) != 0 else 1
            self.reacoes["Rb"] = sM / d
            self.reacoes["Ra"] = sFy - self.reacoes["Rb"]
        else:
            self.reacoes["Ra"], self.reacoes["Ma"] = sFy, sM

    def calcular_esforcos_internos(self, passo=0.01):
        px, vy, my = [], [], []
        for i in range(int(self.Comprimento / passo) + 1):
            X, V, M = i * passo, 0.0, 0.0
            if X >= self.posA - 1e-7:
                V += self.reacoes["Ra"]
                M += self.reacoes["Ra"] * (X - self.posA)
            if self.tipo_apoio == "biapoiada" and X >= self.posB - 1e-7:
                V += self.reacoes["Rb"]
                M += self.reacoes["Rb"] * (X - self.posB)
            if self.tipo_apoio == "engastada" and X >= self.posA - 1e-7:
                M -= self.reacoes["Ma"]
            for c in self.cargas:
                if isinstance(c, CarregamentoConcentrado) and X >= c.Posicao - 1e-7:
                    V -= c.Forca
                    M -= c.Forca * (X - c.Posicao)
                elif isinstance(c, MomentoConcentrado) and X >= c.Posicao - 1e-7:
                    M -= c.Magnitude
                elif isinstance(c, CarregamentoDistribuido) and X > c.PosicaoI:
                    xf = min(X, c.PosicaoF)
                    La = xf - c.PosicaoI
                    taxa = (c.ForcaF - c.ForcaI) / (c.PosicaoF - c.PosicaoI) if (c.PosicaoF - c.PosicaoI) != 0 else 0
                    qa = c.ForcaI + taxa * La
                    Fa = (c.ForcaI + qa) * La / 2
                    cent = (La * (c.ForcaI + 2 * qa) / (3 * (c.ForcaI + qa))) if (c.ForcaI + qa) != 0 else La/2
                    V -= Fa
                    M -= Fa * (X - (c.PosicaoI + cent))
            px.append(X); vy.append(V); my.append(M)
        return px, vy, my

class CarregamentoConcentrado:
    def __init__(self, f, p): self.Forca, self.Posicao = f, p
    def __str__(self): return f"Conc: {self.Forca}kN @ {self.Posicao}m"
class CarregamentoDistribuido:
    def __init__(self, qi, qf, pi, pf): self.ForcaI, self.ForcaF, self.PosicaoI, self.PosicaoF = qi, qf, pi, pf
    def __str__(self): return f"Dist: {self.ForcaI}-{self.ForcaF}kN/m"
class MomentoConcentrado:
    def __init__(self, m, p): self.Magnitude, self.Posicao = m, p
    def __str__(self): return f"Mom: {self.Magnitude}kNm @ {self.Posicao}m"

# INTERFACE GRÁFICA

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Vigas - GRUPO PAGERUNK")
        self.geometry("1100x900")
        self.cargas_lista = []

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=320)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="CONFIGURAÇÕES", font=("Arial", 16, "bold")).pack(pady=10)
        self.el = ctk.CTkEntry(self.sidebar, placeholder_text="Comprimento (m)")
        self.el.pack(fill="x", padx=20, pady=5)
        
        self.tipo_var = ctk.StringVar(value="biapoiada")
        ctk.CTkRadioButton(self.sidebar, text="Biapoiada", variable=self.tipo_var, value="biapoiada").pack()
        ctk.CTkRadioButton(self.sidebar, text="Engastada", variable=self.tipo_var, value="engastada").pack()

        self.ea = ctk.CTkEntry(self.sidebar, placeholder_text="Posição Apoio A")
        self.ea.pack(fill="x", padx=20, pady=5)
        self.eb = ctk.CTkEntry(self.sidebar, placeholder_text="Posição Apoio B")
        self.eb.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.sidebar, text="ADICIONAR CARGAS", font=("Arial", 12, "bold")).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="+ Concentrada", command=self.add_c).pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(self.sidebar, text="+ Distribuída", command=self.add_d).pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(self.sidebar, text="+ Momento (Binário)", command=self.add_m, fg_color="#1f538d").pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(self.sidebar, text="Remover Última", command=self.remover_ultima, fg_color="#5d6d7e").pack(fill="x", padx=20, pady=5)

        self.txt_lista = ctk.CTkTextbox(self.sidebar, height=150)
        self.txt_lista.pack(fill="x", padx=20, pady=5)
        self.txt_lista.configure(state="disabled")

        ctk.CTkButton(self.sidebar, text="CALCULAR", fg_color="green", command=self.executar, font=("Arial", 13, "bold")).pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self.sidebar, text="Limpar Tudo", fg_color="red", command=self.limpar).pack(fill="x", padx=20)

        self.main_view = ctk.CTkFrame(self)
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.lbl_res = ctk.CTkLabel(self.main_view, text="Aguardando dados...", font=("Arial", 16, "bold"))
        self.lbl_res.pack(pady=10)

        self.lbl_v_val = ctk.CTkLabel(self.main_view, text="", font=("Arial", 12, "italic"), text_color="#3498db")
        self.lbl_v_val.pack()
        self.lbl_m_val = ctk.CTkLabel(self.main_view, text="", font=("Arial", 12, "italic"), text_color="#e74c3c")
        self.lbl_m_val.pack()

        self.fig_container = ctk.CTkFrame(self.main_view, fg_color="black") 
        self.fig_container.pack(fill="both", expand=True)
        
        self.mostrar_logo()

    def mostrar_logo(self):
        for w in self.fig_container.winfo_children(): w.destroy()
        try:
            img_data = Image.open("pinguim_pagerunk.png").convert("RGBA")
            img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(400, 400))
            
            self.lbl_logo = ctk.CTkLabel(self.fig_container, image=img, text="", fg_color="black")
            self.lbl_logo.place(relx=0.5, rely=0.5, anchor="center") 
        except:
            ctk.CTkLabel(self.fig_container, text="PAGERUNK STRUCTURAL", font=("Arial", 24, "bold"), text_color="white").pack(expand=True)

    def atualizar_display(self):
        self.txt_lista.configure(state="normal"); self.txt_lista.delete("1.0", "end")
        for i, c in enumerate(self.cargas_lista): self.txt_lista.insert("end", f"{i+1}. {str(c)}\n")
        self.txt_lista.configure(state="disabled")

    def add_c(self):
        val = ctk.CTkInputDialog(text="Força (kN), Posição (m):", title="Carga Concentrada").get_input()
        if val:
            try:
                f, p = map(float, val.replace(" ", "").split(","))
                self.cargas_lista.append(CarregamentoConcentrado(f, p)); self.atualizar_display()
            except: pass

    def add_d(self):
        val = ctk.CTkInputDialog(text="Qi, Qf, Pi, Pf:", title="Carga Distribuída").get_input()
        if val:
            try:
                qi, qf, pi, pf = map(float, val.replace(" ", "").split(","))
                self.cargas_lista.append(CarregamentoDistribuido(qi, qf, pi, pf)); self.atualizar_display()
            except: pass

    def add_m(self):
        val = ctk.CTkInputDialog(text="Mag(kNm), Pos(m):", title="Momento").get_input()
        if val:
            try:
                m, p = map(float, val.replace(" ", "").split(","))
                self.cargas_lista.append(MomentoConcentrado(m, p)); self.atualizar_display()
            except: pass

    def remover_ultima(self):
        if self.cargas_lista: self.cargas_lista.pop(); self.atualizar_display()

    def limpar(self):
        self.cargas_lista = []; self.atualizar_display()
        self.lbl_res.configure(text="Aguardando dados..."); self.lbl_v_val.configure(text=""); self.lbl_m_val.configure(text="")
        self.el.delete(0, 'end'); self.ea.delete(0, 'end'); self.eb.delete(0, 'end')
        self.mostrar_logo()

    def executar(self):
        try:
            v_calc = viga(float(self.el.get()), self.tipo_var.get())
            for c in self.cargas_lista: v_calc.add_carga(c)
            v_calc.calcular_reacoes(float(self.ea.get()), float(self.eb.get() or 0))
            X, V, M = v_calc.calcular_esforcos_internos()
            
            res = f"Ra: {v_calc.reacoes['Ra']:.2f}kN | Rb: {v_calc.reacoes['Rb']:.2f}kN"
            if v_calc.tipo_apoio == "engastada": res += f" | Ma: {v_calc.reacoes['Ma']:.2f}kNm"
            self.lbl_res.configure(text=res)
            self.lbl_v_val.configure(text=f"Cortante (V) -> Máx: {max(V):.2f} kN | Mín: {min(V):.2f} kN")
            self.lbl_m_val.configure(text=f"Momento (M) -> Máx: {max(M):.2f} kNm | Mín: {min(M):.2f} kNm")
            
            for w in self.fig_container.winfo_children(): w.destroy()
            f = Figure(figsize=(5, 7), dpi=100, facecolor='#2b2b2b')
            a1 = f.add_subplot(211); a1.plot(X, V, '#3498db', linewidth=2); a1.set_title("Cortante (V)", color='w')
            a1.grid(True, alpha=0.2); a1.tick_params(colors='w')
            a2 = f.add_subplot(212); a2.plot(X, M, '#e74c3c', linewidth=2); a2.set_title("Fletor (M)", color='w')
            a2.invert_yaxis(); a2.grid(True, alpha=0.2); a2.tick_params(colors='w')
            f.tight_layout(pad=3.0)
            canvas = FigureCanvasTkAgg(f, master=self.fig_container); canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)
        except: self.lbl_res.configure(text="Erro nos dados!")

if __name__ == "__main__":
    App().mainloop()
