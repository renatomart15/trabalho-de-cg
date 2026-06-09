# Estados do Turno
TURNO_JOGADOR = 0
TURNO_INIMIGO = 1

# Estados do Seletor/Cursor
MODO_NAVEGACAO = 0
MODO_MOVIMENTACAO = 1
MODO_ATAQUE = 2

# Configurações de Atributos das Entidades
HP_INICIAL = {
    1: 5,   # Trator
    2: 4,   # Escavadeira
    10: 3,  # Mosquito
    11: 3,  # Barata
    50: 4   # Casa (Mutantes querem atacar!)
}

DANO_UNIDADE = {
    1: 2,   # Trator
    2: 3,   # Escavadeira
    10: 1,  # Mosquito
    11: 2   # Barata
}

ALCANCE_MOVIMENTO = {
    1: 3,   # Trator
    2: 2,   # Escavadeira
    10: 4,  # Mosquito
    11: 2   # Barata
}

ALCANCE_ATAQUE = {
    1: 1,   # Trator
    2: 2,   # Escavadeira (Alcance especial de 2 na diagonal imediata)
    10: 1,  # Mosquito
    11: 1   # Barata
}