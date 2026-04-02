class viga:
    def __init__ (self, comprimento):
        self.Comprimento = comprimento
        self.apoios = []
        self.cargas = []
        self.reacoes = {"Ra": 0, "Rb": 0}

class CarregamentoConcentrado:
    def __init__ (self, forca, posição):
        self.Forca = forca
        self.Posicao = posição
    
    #retorna a saida
    def info(self):
        return f"{self.Forca} {self.Posicao}"
        
class CarregamentoDistribuido:
    def __init__ (self, forçaI, forcaF, posicaoI, posicaoF):
        self.ForcaI = forcaI
        self.FrocaF = forcaF
        self.PosicaoI = posicaoI
        self.PosicaoF = posicaoF

#teste de saida
valor1 = input('digite o valor da força')
valor2 = input('digite o valor da posição')

resultado = CarregamentoConcentrado(valor1, valor2)
print(resultado.info())       