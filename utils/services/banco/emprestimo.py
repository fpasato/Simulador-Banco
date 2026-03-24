
def simularEmprestimo(valor, parcelas):

    return {

        "valor": valor,

        "parcelas": parcelas,

        "valor_parcela": valor / parcelas,

        "juros": 0.05,  # 5% de juros

        "total": valor * 1.05

    }

