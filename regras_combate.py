from collections import deque
from config import ALCANCE_MOVIMENTO, ALCANCE_ATAQUE

def verificar_inimigo(atacante_id, alvo_id):
    if atacante_id in [1, 2] and alvo_id in [10, 11]:
        return True
    if atacante_id in [10, 11] and alvo_id in [1, 2, 50]:
        return True
    return False

def calcular_distancia_ataque(r1, c1, r2, c2, peca_id):
    
    diff_r = abs(r1 - r2)
    diff_c = abs(c1 - c2)
    if peca_id == 2 and diff_r == 1 and diff_c == 1:
        return 1
    return diff_r + diff_c

def validar_movimento(r_orig, c_orig, r_dest, c_dest, peca_id, tabuleiro):
    
    if (r_orig, c_orig) == (r_dest, c_dest):
        return True

    ID_AGUA = 1
    limite_movimento = ALCANCE_MOVIMENTO.get(peca_id, 2)

    
    if peca_id == 2:
        diff_r = abs(r_orig - r_dest)
        diff_c = abs(c_orig - c_dest)
        if max(diff_r, diff_c) <= 1:
            
            return tabuleiro.grid[r_dest][c_dest] != ID_AGUA
        return False

    fila = deque([(r_orig, c_orig, 0)])
    visitados = set([(r_orig, c_orig)])

    while fila:
        r_atual, c_atual, passos = fila.popleft()

        
        if (r_atual, c_atual) == (r_dest, c_dest):
            return True

        
        if passos >= limite_movimento:
            continue

        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nova_r, nova_c = r_atual + dr, c_atual + dc

        
            if 0 <= nova_r < 8 and 0 <= nova_c < 8:
                if (nova_r, nova_c) not in visitados:
                    
                    
                    if peca_id != 10 and tabuleiro.grid[nova_r][nova_c] == ID_AGUA:
                        continue # Bloqueia: não pode pisar e nem passar por aqui
                    
                    
                    
                    visitados.add((nova_r, nova_c))
                    fila.append((nova_r, nova_c, passos + 1))

    return False