class viga:
    def __init__ (self, comprimento, tipo_apoio="biapoiada"):
        self.Comprimento = comprimento
        self.tipo_apoio = tipo_apoio
        self.apoios = []
        self.cargas = []
        self.reacoes = {"Ra": 0, "Rb": 0, "Ma": 0}

    def add_carga(self, carga):
        self.cargas.append(carga)

    def calcular_reacoes(self, posA, posB=0):
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

carga1 = CarregamentoDistribuido(0.0, 3.0, 0.0, 2.0)
minha_viga.add_carga(carga1)

carga2 = CarregamentoDistribuido(3.0, 3.0, 4.0, 6.0)
minha_viga.add_carga(carga2)

minha_viga.calcular_reacoes(2.0, 6.0)

print(f"Ra: {minha_viga.reacoes['Ra']:.2f} kN")
print(f"Rb: {minha_viga.reacoes['Rb']:.2f} kN")    