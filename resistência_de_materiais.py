class viga:
    def __init__ (self, comprimento, tipo_apoio="biapoiada"):
        self.Comprimento = comprimento
        self.tipo_apoio = tipo_apoio
        self.apoios = []
        self.cargas = []
        self.reacoes = {"Ra": 0, "Rb": 0, "Ma": 0}
        self.posA = 0.0
        self.posB = 0.0

    def add_carga(self, carga):
        self.cargas.append(carga)

    def calcular_reacoes(self, posA, posB=0):
        self.posA = posA
        self.posB = posB
        somaFy = 0
        somaM = 0

        for c in self.cargas:
            if isinstance(c, CarregamentoConcentrado):
                F = c.Forca
                X = c.Posicao
            elif isinstance(c, CarregamentoDistribuido):
                largura = c.PosicaoF - c.PosicaoI
                F = (c.ForcaI + c.ForcaF) * largura / 2
                centroide_local = (largura * (c.ForcaI + 2 * c.ForcaF) / (3 * (c.ForcaI + c.ForcaF)))
                X = c.PosicaoI + centroide_local
            
            somaFy += F
            somaM += F * (X - posA)

        if self.tipo_apoio == "biapoiada":
            dist_apoios = posB - posA
            self.reacoes["Rb"] = somaM / dist_apoios
            self.reacoes["Ra"] = somaFy - self.reacoes["Rb"]
            self.reacoes["Ma"] = 0
            
        elif self.tipo_apoio == "engastada":
            self.reacoes["Ra"] = somaFy
            self.reacoes["Ma"] = somaM
            self.reacoes["Rb"] = 0

    def calcular_esforcos_internos(self, passo=0.01):
        pontos_x = []
        valores_v = []
        valores_m = []

        num_passos = int(round(self.Comprimento / passo)) + 1

        for i in range(num_passos):
            X = i * passo
            V = 0.0
            M = 0.0

            if X >= self.posA:
                V += self.reacoes["Ra"]
                M += self.reacoes["Ra"] * (X - self.posA)
            if X >= self.posB:
                V += self.reacoes["Rb"]
                M += self.reacoes["Rb"] * (X - self.posB)
            
            if self.tipo_apoio == "engastada" and X >= self.posA:
                M -= self.reacoes["Ma"]

            for c in self.cargas:
                if isinstance(c, CarregamentoConcentrado):
                    if X >= c.Posicao:
                        V -= c.Forca
                        M -= c.Forca * (X - c.Posicao)
                
                elif isinstance(c, CarregamentoDistribuido):
                    if X > c.PosicaoI:
                        X_fim = min(X, c.PosicaoF)
                        largura_ativa = X_fim - c.PosicaoI
                        
                        q_atual = c.ForcaI + (c.ForcaF - c.ForcaI) * (largura_ativa / (c.PosicaoF - c.PosicaoI))
                        forca_acumulada = (c.ForcaI + q_atual) * largura_ativa / 2
                        
                        if forca_acumulada != 0:
                            centroide = (largura_ativa * (c.ForcaI + 2 * q_atual)) / (3 * (c.ForcaI + q_atual))
                        else:
                            centroide = 0
                            
                        braco_alavanca = X - (c.PosicaoI + centroide)
                        
                        V -= forca_acumulada
                        M -= forca_acumulada * braco_alavanca

            pontos_x.append(round(X, 3))
            valores_v.append(V)
            valores_m.append(M)

        return pontos_x, valores_v, valores_m

class CarregamentoConcentrado:
    def __init__ (self, forca, posicao):
        self.Forca = forca
        self.Posicao = posicao
        
class CarregamentoDistribuido:
    def __init__ (self, forcaI, forcaF, posicaoI, posicaoF):
        self.ForcaI = forcaI
        self.ForcaF = forcaF
        self.PosicaoI = posicaoI
        self.PosicaoF = posicaoF

minha_viga = viga(6.0, tipo_apoio="biapoiada")

minha_viga.add_carga(CarregamentoDistribuido(0.0, 3.0, 0.0, 2.0))
minha_viga.add_carga(CarregamentoDistribuido(3.0, 3.0, 4.0, 6.0))

minha_viga.calcular_reacoes(2.0, 6.0)

print(f"Reações:")
print(f"Ra: {minha_viga.reacoes['Ra']:.2f} kN")
print(f"Rb: {minha_viga.reacoes['Rb']:.2f} kN\n")

X, V, M = minha_viga.calcular_esforcos_internos(passo=0.01)

print("Esforços Internos:")
print(f"Força Cortante Máxima (+): {max(V):.2f} kN")
print(f"Força Cortante Mínima (-): {min(V):.2f} kN")
print(f"Momento Fletor Máximo (+): {max(M):.2f} kN.m")
print(f"Momento Fletor Mínimo (-): {min(M):.2f} kN.m")
