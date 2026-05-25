# regras_combate.py
from collections import deque
from config import ALCANCE_MOVIMENTO, ALCANCE_ATAQUE

def verificar_inimigo(atacante_id, alvo_id):
    """Retorna True se o alvo for um inimigo válido para o atacante."""
    if atacante_id in [1, 2] and alvo_id in [10, 11]:
        return True
    if atacante_id in [10, 11] and alvo_id in [1, 2, 50]:
        return True
    return False

def calcular_distancia_ataque(r1, c1, r2, c2, peca_id):
    """Calcula a distância de ataque considerando a regra da Escavadeira."""
    diff_r = abs(r1 - r2)
    diff_c = abs(c1 - c2)
    if peca_id == 2 and diff_r == 1 and diff_c == 1:
        return 1
    return diff_r + diff_c

def validar_movimento(r_orig, c_orig, r_dest, c_dest, peca_id, tabuleiro):
    """
    Verifica se existe um caminho válido passo a passo até o destino,
    garantindo que unidades terrestres não atravessem nem pisem na água.
    """
    # Se o destino for igual à origem, o movimento é nulo (soltar a peça)
    if (r_orig, c_orig) == (r_dest, c_dest):
        return True

    ID_AGUA = 1
    limite_movimento = ALCANCE_MOVIMENTO.get(peca_id, 2)

    # Caso especial da Escavadeira (ID 2): Movimenta-se em qualquer direção adjacente (incluindo diagonais)
    if peca_id == 2:
        diff_r = abs(r_orig - r_dest)
        diff_c = abs(c_orig - c_dest)
        if max(diff_r, diff_c) <= 1:
            # Mesmo adjacente, a escavadeira não pode pousar na água
            return tabuleiro.grid[r_dest][c_dest] != ID_AGUA
        return False

    # Para as demais unidades (Trator e Barata), usamos BFS para achar um caminho válido de até N passos
    # O Mosquito (ID 10) ignora a água, mas ainda respeita a distância máxima
    
    # Filas para o BFS: (linha, coluna, passos_gastos)
    fila = deque([(r_orig, c_orig, 0)])
    visitados = set([(r_orig, c_orig)])

    while fila:
        r_atual, c_atual, passos = fila.popleft()

        # Se alcançamos o destino dentro do limite de passos, o caminho é válido!
        if (r_atual, c_atual) == (r_dest, c_dest):
            return True

        # Se já atingimos o limite de passos a partir daqui, não expandimos mais este caminho
        if passos >= limite_movimento:
            continue

        # Movimentos ortogonais permitidos (Cima, Baixo, Esquerda, Direita)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nova_r, nova_c = r_atual + dr, c_atual + dc

            # Verifica se está dentro dos limites do tabuleiro 8x8
            if 0 <= nova_r < 8 and 0 <= nova_c < 8:
                if (nova_r, nova_c) not in visitados:
                    
                    # Checa restrição de água para unidades terrestres (Trator e Barata)
                    if peca_id != 10 and tabuleiro.grid[nova_r][nova_c] == ID_AGUA:
                        continue # Bloqueia: não pode pisar e nem passar por aqui
                    
                    # Opcional: Você também pode bloquear passar por cima de outras unidades (exceto o mosquito)
                    # se id_entidade != 0 e (nova_r, nova_c) != (r_dest, c_dest): continue

                    visitados.add((nova_r, nova_c))
                    fila.append((nova_r, nova_c, passos + 1))

    return False