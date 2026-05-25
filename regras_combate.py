# regras_combate.py
import numpy as np
from config import ALCANCE_MOVIMENTO, ALCANCE_ATAQUE

def verificar_inimigo(atacante_id, alvo_id):
    """Retorna True se o alvo for um inimigo válido para o atacante."""
    if atacante_id in [1, 2] and alvo_id in [10, 11]:
        return True
    if atacante_id in [10, 11] and alvo_id in [1, 2, 50]: # Insetos atacam robôs e casas
        return True
    return False

def calcular_distancia_ataque(r1, c1, r2, c2, peca_id):
    """Calcula a distância de ataque considerando a regra da Escavadeira."""
    diff_r = abs(r1 - r2)
    diff_c = abs(c1 - c2)
    
    # Regra especial da Escavadeira (ID 2): diagonal imediata conta como distância 1
    if peca_id == 2 and diff_r == 1 and diff_c == 1:
        return 1
        
    return diff_r + diff_c

def validar_movimento(r_orig, c_orig, r_dest, c_dest, peca_id):
    """Verifica se o movimento está dentro do limite da respectiva peça."""
    diff_r = abs(r_orig - r_dest)
    diff_c = abs(c_orig - c_dest)
    
    if peca_id == 2:  # Escavadeira usa distância Chebyshev (máximo entre eixos)
        return max(diff_r, diff_c) <= 1
    
    limite = ALCANCE_MOVIMENTO.get(peca_id, 2)
    return (diff_r + diff_c) <= limite