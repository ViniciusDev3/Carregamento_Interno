import math
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PIL import Image
import numpy as np

# =========================== LÓGICA DE CÁLCULO ===========================

class Viga:
    def __init__(self, comprimento, tipo_apoio="biapoiada"):
        self.comprimento = comprimento
        self.tipo_apoio = tipo_apoio
        self.cargas = []
        self.reacoes = {"Ra": 0, "Rb": 0, "Ma": 0}
        self.posA = 0.0
        self.posB = 0.0

    def add_carga(self, carga):
        self.cargas.append(carga)

    def calcular_reacoes(self, posA, posB=0):
        self.posA = posA
        self.posB = posB
        sFy = 0.0
        sM = 0.0
        for c in self.cargas:
            if isinstance(c, CarregamentoConcentrado):
                sFy += c.forca
                sM += c.forca * (c.posicao - posA)
            elif isinstance(c, CarregamentoDistribuido):
                L = c.posicaoF - c.posicaoI
                if L <= 0:
                    continue
                F = (c.forcaI + c.forcaF) * L / 2.0
                if (c.forcaI + c.forcaF) != 0:
                    centroide = L * (c.forcaI + 2 * c.forcaF) / (3 * (c.forcaI + c.forcaF))
                else:
                    centroide = L / 2.0
                sFy += F
                sM += F * (c.posicaoI + centroide - posA)
            elif isinstance(c, MomentoConcentrado):
                sM -= c.magnitude
                
        if self.tipo_apoio == "biapoiada":
            d = posB - posA
            if abs(d) < 1e-9:
                d = 1.0
            self.reacoes["Rb"] = sM / d
            self.reacoes["Ra"] = sFy - self.reacoes["Rb"]
        else:  # engastada
            self.reacoes["Ra"] = sFy
            self.reacoes["Ma"] = sM

    def calcular_esforcos_internos(self, passo=0.01):
        pontos_especiais = set()
        pontos_especiais.add(0.0)
        pontos_especiais.add(self.comprimento)
        pontos_especiais.add(self.posA)
        if self.tipo_apoio == "biapoiada":
            pontos_especiais.add(self.posB)
        for c in self.cargas:
            if isinstance(c, CarregamentoConcentrado):
                pontos_especiais.add(c.posicao)
            elif isinstance(c, MomentoConcentrado):
                pontos_especiais.add(c.posicao)
            elif isinstance(c, CarregamentoDistribuido):
                pontos_especiais.add(c.posicaoI)
                pontos_especiais.add(c.posicaoF)
                
        pontos = sorted(list(pontos_especiais))
        
        x_vals = []
        v_vals = []
        m_vals = []
        
        for i in range(len(pontos) - 1):
            x0 = pontos[i]
            x1 = pontos[i+1]
            n = max(2, int((x1 - x0) / passo) + 1)
            for x in np.linspace(x0, x1, n):
                if x in x_vals:
                    continue
                X = x
                V = 0.0
                M = 0.0

                if X >= self.posA - 1e-7:
                    V += self.reacoes["Ra"]
                    M += self.reacoes["Ra"] * (X - self.posA)
                if self.tipo_apoio == "biapoiada" and X >= self.posB - 1e-7:
                    V += self.reacoes["Rb"]
                    M += self.reacoes["Rb"] * (X - self.posB)
                if self.tipo_apoio == "engastada" and X >= self.posA - 1e-7:
                    M -= self.reacoes["Ma"]

                for c in self.cargas:
                    if isinstance(c, CarregamentoConcentrado) and X >= c.posicao - 1e-7:
                        V -= c.forca
                        M -= c.forca * (X - c.posicao)
                    elif isinstance(c, MomentoConcentrado) and X >= c.posicao - 1e-7:
                        M -= c.magnitude
                    elif isinstance(c, CarregamentoDistribuido) and X > c.posicaoI:
                        xf = min(X, c.posicaoF)
                        Lparc = xf - c.posicaoI
                        if Lparc <= 0:
                            continue
                        taxa = (c.forcaF - c.forcaI) / (c.posicaoF - c.posicaoI) if (c.posicaoF - c.posicaoI) != 0 else 0
                        qa = c.forcaI + taxa * Lparc
                        Fparc = (c.forcaI + qa) * Lparc / 2.0
                        if (c.forcaI + qa) != 0:
                            centroide = Lparc * (c.forcaI + 2 * qa) / (3 * (c.forcaI + qa))
                        else:
                            centroide = Lparc / 2.0
                        V -= Fparc
                        M -= Fparc * (X - (c.posicaoI + centroide))

                x_vals.append(X)
                v_vals.append(V)
                m_vals.append(M)

        if not math.isclose(x_vals[-1], self.comprimento):
            x_vals.append(self.comprimento)
            v_vals.append(v_vals[-1])
            m_vals.append(m_vals[-1])

        return x_vals, v_vals, m_vals


class CarregamentoConcentrado:
    def __init__(self, forca, posicao):
        self.forca = forca
        self.posicao = posicao
    def __str__(self):
        return f"Conc: {self.forca} kN @ {self.posicao} m"

class CarregamentoDistribuido:
    def __init__(self, forcaI, forcaF, posicaoI, posicaoF):
        self.forcaI = forcaI
        self.forcaF = forcaF
        self.posicaoI = posicaoI
        self.posicaoF = posicaoF
    def __str__(self):
        return f"Dist: {self.forcaI}-{self.forcaF} kN/m  [{self.posicaoI} a {self.posicaoF}] m"

class MomentoConcentrado:
    def __init__(self, magnitude, posicao):
        self.magnitude = magnitude
        self.posicao = posicao
    def __str__(self):
        return f"Mom: {self.magnitude} kNm @ {self.posicao} m"


# =========================== INTERFACE GRÁFICA ===========================

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
        self.entry_comprimento = ctk.CTkEntry(self.sidebar, placeholder_text="Comprimento (m)")
        self.entry_comprimento.pack(fill="x", padx=20, pady=5)

        self.tipo_var = ctk.StringVar(value="biapoiada")
        ctk.CTkRadioButton(self.sidebar, text="Biapoiada", variable=self.tipo_var,
                           value="biapoiada", command=self.desenhar_esquema).pack()
        ctk.CTkRadioButton(self.sidebar, text="Engastada", variable=self.tipo_var,
                           value="engastada", command=self.desenhar_esquema).pack()

        self.entry_posA = ctk.CTkEntry(self.sidebar, placeholder_text="Posição Apoio A (m)")
        self.entry_posA.pack(fill="x", padx=20, pady=5)
        self.entry_posB = ctk.CTkEntry(self.sidebar, placeholder_text="Posição Apoio B (m) [biapoiada]")
        self.entry_posB.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.sidebar, text="ADICIONAR CARGAS", font=("Arial", 12, "bold")).pack(pady=10)
        ctk.CTkButton(self.sidebar, text="+ Concentrada", command=self.add_carga_concentrada).pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(self.sidebar, text="+ Distribuída", command=self.add_carga_distribuida).pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(self.sidebar, text="+ Momento", command=self.add_momento_concentrado, fg_color="#1f538d").pack(fill="x", padx=20, pady=2)
        ctk.CTkButton(self.sidebar, text="Remover Última", command=self.remover_ultima, fg_color="#5d6d7e").pack(fill="x", padx=20, pady=10)

        self.txt_lista_cargas = ctk.CTkTextbox(self.sidebar, height=180)
        self.txt_lista_cargas.pack(fill="x", padx=20, pady=5)
        self.txt_lista_cargas.configure(state="disabled")

        ctk.CTkButton(self.sidebar, text="CALCULAR", fg_color="green", command=self.executar,
                      font=("Arial", 13, "bold")).pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(self.sidebar, text="Limpar Tudo", fg_color="red", command=self.limpar_tudo).pack(fill="x", padx=20)

        self.main_view = ctk.CTkFrame(self)
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.header_frame = ctk.CTkFrame(self.main_view, fg_color="transparent", height=40)
        self.header_frame.pack(fill="x", padx=10, pady=5)
        self.header_frame.pack_propagate(False)

        self.lbl_resultado = ctk.CTkLabel(self.header_frame, text="Aguardando dados...", font=("Arial", 14, "bold"))
        self.lbl_resultado.pack(side="left", padx=10)

        self.nav_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.nav_frame.pack(side="right")

        self.btn_voltar = ctk.CTkButton(self.nav_frame, text="◀ Ver Montagem", width=120, height=28,
                                        fg_color="#34495e", command=self.desenhar_esquema)
        self.btn_avancar = ctk.CTkButton(self.nav_frame, text="Ver Resultado ▶", width=120, height=28,
                                         fg_color="#1f538d", command=self.executar)

        self.lbl_cortante = ctk.CTkLabel(self.main_view, text="", font=("Arial", 11), text_color="#3498db")
        self.lbl_cortante.pack()
        self.lbl_momento = ctk.CTkLabel(self.main_view, text="", font=("Arial", 11), text_color="#e74c3c")
        self.lbl_momento.pack()

        self.fig_container = ctk.CTkFrame(self.main_view, fg_color="black")
        self.fig_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.mostrar_logo()

    def mostrar_erro(self, mensagem):
        self.lbl_resultado.configure(text=f"ERRO: {mensagem}")
        self.after(3000, lambda: self.lbl_resultado.configure(text="Aguardando dados..."))

    def mostrar_logo(self):
        self.btn_voltar.pack_forget()
        self.btn_avancar.pack_forget()
        self.lbl_resultado.configure(text="Aguardando dados...")
        for w in self.fig_container.winfo_children():
            w.destroy()
        try:
            img_data = Image.open("pinguim_pagerunk.png").convert("RGBA")
            img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(500, 500))
            lbl = ctk.CTkLabel(self.fig_container, image=img, text="", fg_color="black")
            lbl.place(relx=0.5, rely=0.5, anchor="center")
        except FileNotFoundError:
            ctk.CTkLabel(self.fig_container, text="PAGERUNK", font=("Arial", 30, "bold"),
                         text_color="white").pack(expand=True)

    def desenhar_esquema(self):
        self.lbl_resultado.configure(text="Esquema de Montagem")
        self.btn_voltar.pack_forget()
        self.btn_avancar.pack(side="right", padx=5)
        
        self.lbl_cortante.configure(text="")
        self.lbl_momento.configure(text="")
        
        try:
            L = float(self.entry_comprimento.get() or 0)
            if L <= 0: return
            posA = float(self.entry_posA.get() or 0)
            if posA < 0 or posA > L:
                self.mostrar_erro(f"Apoio A fora da viga (0 a {L})")
                return
            if self.tipo_var.get() == "biapoiada":
                posB = float(self.entry_posB.get() or 0)
                if posB < 0 or posB > L:
                    self.mostrar_erro(f"Apoio B fora da viga (0 a {L})")
                    return
            else:
                posB = 0.0
        except ValueError:
            self.mostrar_erro("Valores numéricos inválidos nos campos")
            return

        for w in self.fig_container.winfo_children():
            w.destroy()
        fig = Figure(figsize=(5, 3), dpi=100, facecolor='#2b2b2b')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#2b2b2b')
        ax.plot([0, L], [0, 0], color='white', linewidth=6)
        ax.text(L/2, -0.15, f"L = {L} m", color='white', ha='center', fontsize=10, fontweight='bold')
        
        if self.tipo_var.get() == "biapoiada":
            ax.plot(posA, -0.05, '^', color='yellow', markersize=15)
            ax.text(posA, -0.25, f"A ({posA}m)", color='yellow', ha='center', fontsize=9)
            ax.plot(posB, -0.05, '^', color='yellow', markersize=15)
            ax.text(posB, -0.25, f"B ({posB}m)", color='yellow', ha='center', fontsize=9)
        else:
            ax.add_patch(Rectangle((posA-0.15, -0.3), 0.15, 0.6, color='#bdc3c7', zorder=3))
            for i in range(7):
                y_hatch = -0.3 + i*0.1
                ax.plot([posA-0.15, posA-0.25], [y_hatch, y_hatch-0.05], color='#bdc3c7', linewidth=2)
            ax.text(posA, -0.45, f"A ({posA}m)", color='yellow', ha='center', fontsize=9)
            
        for c in self.cargas_lista:
            if isinstance(c, CarregamentoConcentrado):
                ax.annotate('', xy=(c.posicao, 0), xytext=(c.posicao, 0.4),
                            arrowprops=dict(facecolor='#3498db', shrink=0.05, width=2))
                ax.text(c.posicao, 0.45, f"{c.forca} kN\n({c.posicao}m)", color='#3498db', ha='center', fontsize=9, fontweight='bold')
            elif isinstance(c, CarregamentoDistribuido):
                ax.add_patch(Rectangle((c.posicaoI, 0), c.posicaoF - c.posicaoI, 0.2, color='#e74c3c', alpha=0.5))
                ax.text((c.posicaoI + c.posicaoF)/2, 0.25, f"{c.forcaI}-{c.forcaF} kN/m\n({c.posicaoI} a {c.posicaoF}m)", color='#e74c3c', ha='center', fontsize=8)
            elif isinstance(c, MomentoConcentrado):
                ax.plot(c.posicao, 0.1, 'go', markersize=12)
                ax.text(c.posicao, 0.2, f"{c.magnitude} kNm\n({c.posicao}m)", color='green', ha='center', fontsize=9)
        ax.set_xlim(-L*0.1, L*1.1)
        ax.set_ylim(-0.6, 0.7)
        ax.axis('off')
        canvas = FigureCanvasTkAgg(fig, master=self.fig_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def executar(self):
        self.btn_avancar.pack_forget()
        self.btn_voltar.pack(side="right", padx=5)  
        try:
            L = float(self.entry_comprimento.get())
            if L <= 0: raise ValueError("Comprimento deve ser > 0")
            posA = float(self.entry_posA.get())
            if posA < 0 or posA > L: raise ValueError(f"Apoio A fora da viga (0 a {L})")
            if self.tipo_var.get() == "biapoiada":
                posB = float(self.entry_posB.get())
                if posB < 0 or posB > L: raise ValueError(f"Apoio B fora da viga (0 a {L})")
                if abs(posB - posA) < 1e-6: raise ValueError("Apoios A e B não podem coincidir")
            else:
                posB = 0.0
        except ValueError as e:
            self.mostrar_erro(str(e))
            return

        viga = Viga(L, self.tipo_var.get())
        for carga in self.cargas_lista:
            viga.add_carga(carga)

        viga.calcular_reacoes(posA, posB)
        x, V, M = viga.calcular_esforcos_internos(passo=0.01)

        if viga.tipo_apoio == "engastada":
            res_text = f"Ra: {viga.reacoes['Ra']:.2f} kN | Ma: {viga.reacoes['Ma']:.2f} kNm"
        else:
            res_text = f"Ra: {viga.reacoes['Ra']:.2f} kN | Rb: {viga.reacoes['Rb']:.2f} kN"
            
        self.lbl_resultado.configure(text=res_text)

        max_diagrama_v = max(V) if len(V) > 0 else 0.0
        min_diagrama_v = min(V) if len(V) > 0 else 0.0
        
        if min_diagrama_v >= 0.0:
            if viga.tipo_apoio == "biapoiada" and viga.reacoes["Rb"] < 0:
                min_diagrama_v = viga.reacoes["Rb"]
            if viga.reacoes["Ra"] < 0:
                min_diagrama_v = min(min_diagrama_v, viga.reacoes["Ra"])
                
        if max_diagrama_v <= 0.0:
            if viga.tipo_apoio == "biapoiada" and viga.reacoes["Rb"] > 0:
                max_diagrama_v = viga.reacoes["Rb"]
            if viga.reacoes["Ra"] > 0:
                max_diagrama_v = max(max_diagrama_v, viga.reacoes["Ra"])

        maxM = max(M) if len(M) > 0 else 0.0
        minM = min(M) if len(M) > 0 else 0.0

        self.lbl_cortante.configure(text=f"Cortante (V) -> Máx: {max_diagrama_v:.2f} kN | Mín: {min_diagrama_v:.2f} kN")
        self.lbl_momento.configure(text=f"Momento (M) -> Máx: {maxM:.2f} kNm | Mín: {minM:.2f} kNm")

        for w in self.fig_container.winfo_children():
            w.destroy()

        fig = Figure(figsize=(5, 7), dpi=100, facecolor='#2b2b2b')
        ax1 = fig.add_subplot(211)
        ax1.plot(x, V, '#3498db', linewidth=2)
        ax1.set_title("Cortante (V)", color='w')
        ax1.grid(True, alpha=0.2)
        ax1.tick_params(colors='w')
        
        v_min_ax = min(0, min(V))
        v_max_ax = max(0, max(V))
        margem_v = (v_max_ax - v_min_ax) * 0.1
        if margem_v == 0: margem_v = 1.0
        ax1.set_ylim(v_min_ax - margem_v, v_max_ax + margem_v)

        ax2 = fig.add_subplot(212)
        ax2.plot(x, M, '#e74c3c', linewidth=2)
        ax2.set_title("Momento (M)", color='w')
        ax2.grid(True, alpha=0.2)
        ax2.tick_params(colors='w')
        
        m_min_ax = min(0, min(M))
        m_max_ax = max(0, max(M))
        margem_m = (m_max_ax - m_min_ax) * 0.1
        if margem_m == 0: margem_m = 1.0
        ax2.set_ylim(m_max_ax + margem_m, m_min_ax - margem_m)

        fig.tight_layout(pad=3.0)
        canvas = FigureCanvasTkAgg(fig, master=self.fig_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def atualizar_display(self):
        self.txt_lista_cargas.configure(state="normal")
        self.txt_lista_cargas.delete("1.0", "end")
        for i, c in enumerate(self.cargas_lista):
            self.txt_lista_cargas.insert("end", f"{i+1}. {str(c)}\n")
        self.txt_lista_cargas.configure(state="disabled")
        self.desenhar_esquema()

    def add_carga_concentrada(self):
        dialog = ctk.CTkInputDialog(text="Força (kN), Posição (m):", title="Carga Concentrada")
        val = dialog.get_input()
        if val:
            try:
                partes = val.replace(" ", "").split(",")
                if len(partes) != 2: raise ValueError("Dois valores necessários")
                self.cargas_lista.append(CarregamentoConcentrado(float(partes[0]), float(partes[1])))
                self.atualizar_display()
            except Exception as e: self.mostrar_erro(str(e))

    def add_carga_distribuida(self):
        dialog = ctk.CTkInputDialog(text="Qi (kN/m), Qf (kN/m), Pi (m), Pf (m):", title="Carga Distribuída")
        val = dialog.get_input()
        if val:
            try:
                partes = val.replace(" ", "").split(",")
                if len(partes) != 4: raise ValueError("Quatro valores necessários")
                qi, qf, pi, pf = map(float, partes)
                if pi >= pf: raise ValueError("Posição inicial deve ser menor que final")
                self.cargas_lista.append(CarregamentoDistribuido(qi, qf, pi, pf))
                self.atualizar_display()
            except Exception as e: self.mostrar_erro(str(e))

    def add_momento_concentrado(self):
        dialog = ctk.CTkInputDialog(text="Magnitude (kNm), Posição (m):", title="Momento Concentrado")
        val = dialog.get_input()
        if val:
            try:
                partes = val.replace(" ", "").split(",")
                if len(partes) != 2: raise ValueError("Dois valores necessários")
                self.cargas_lista.append(MomentoConcentrado(float(partes[0]), float(partes[1])))
                self.atualizar_display()
            except Exception as e: self.mostrar_erro(str(e))

    def remover_ultima(self):
        if self.cargas_lista:
            self.cargas_lista.pop()
            self.atualizar_display()
        else:
            self.mostrar_logo()

    def limpar_tudo(self):
        self.cargas_lista = []
        self.entry_comprimento.delete(0, 'end')
        self.entry_posA.delete(0, 'end')
        self.entry_posB.delete(0, 'end')
        self.atualizar_display()
        self.mostrar_logo()

if __name__ == "__main__":
    App().mainloop()
