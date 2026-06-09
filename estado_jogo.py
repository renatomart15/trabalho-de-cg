# estado_jogo.py
from config import TURNO_JOGADOR, TURNO_INIMIGO, MODO_NAVEGACAO, HP_INICIAL, DANO_UNIDADE

class EstadoJogo:
    def __init__(self, tabuleiro):
        self.tabuleiro = tabuleiro
        self.turno_atual = TURNO_JOGADOR
        self.estado_seletor = MODO_NAVEGACAO
        
        self.cursor_row = 4
        self.cursor_col = 4
        
        self.peca_selecionada = None
        self.pos_selecionada = None
        
        self.hp_unidades = {}
        self.inicializar_vidas()

    def inicializar_vidas(self):
        
        for r in range(8):
            for c in range(8):
                id_peca = self.tabuleiro.entities[r][c]
                if id_peca != 0:
                    self.hp_unidades[(r, c)] = HP_INICIAL.get(id_peca, 3)

    def alternar_turno(self):
        
        self.peca_selecionada = None
        self.pos_selecionada = None
        self.estado_seletor = MODO_NAVEGACAO
        self.turno_atual = TURNO_INIMIGO if self.turno_atual == TURNO_JOGADOR else TURNO_JOGADOR
        

    def causar_dano(self, r, c, quantidade):
        
        if (r, c) not in self.hp_unidades:
            return
        
        id_alvo = self.tabuleiro.entities[r][c]
        self.hp_unidades[(r, c)] -= quantidade
        hp_restante = self.hp_unidades[(r, c)]
        
        
        
        if hp_restante <= 0:

            self.tabuleiro.entities[r][c] = 0
            self.hp_unidades.pop((r, c), None)

    def aplicar_ataque(self, alvo_r, alvo_c):
        
        origem_r, origem_c = self.pos_selecionada
        id_atacante = self.peca_selecionada
        id_alvo = self.tabuleiro.entities[alvo_r][alvo_c]
        
        
        dano_base = DANO_UNIDADE.get(id_atacante, 1)
        
        
        
        hp_alvo_antes = self.hp_unidades.get((alvo_r, alvo_c), 0)
        self.causar_dano(alvo_r, alvo_c, dano_base)
        
        
        if hp_alvo_antes - dano_base <= 0:
            self.alternar_turno()
            return

        
        dir_r = alvo_r - origem_r
        dir_c = alvo_c - origem_c
        

        if dir_r != 0: dir_r = 1 if dir_r > 0 else -1
        if dir_c != 0: dir_c = 1 if dir_c > 0 else -1
        
        dest_r = alvo_r + dir_r
        dest_c = alvo_c + dir_c
        

        if not (0 <= dest_r < 8 and 0 <= dest_c < 8):
            self.causar_dano(alvo_r, alvo_c, 1)
            
        
        elif self.tabuleiro.entities[dest_r][dest_c] != 0:
            id_obstaculo = self.tabuleiro.entities[dest_r][dest_c]

            self.causar_dano(alvo_r, alvo_c, 1)
            self.causar_dano(dest_r, dest_c, 1)

        elif self.tabuleiro.grid[dest_r][dest_c] == 1:

            if id_alvo != 10:  
                self.causar_dano(alvo_r, alvo_c, self.hp_unidades.get((alvo_r, alvo_c), 99))
            else:
                self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        else:
            self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        self.alternar_turno()

    def deslocar_entidade_fisicamente(self, r_orig, c_orig, r_dest, c_dest):
        id_peca = self.tabuleiro.entities[r_orig][c_orig]
        hp_atual = self.hp_unidades.pop((r_orig, c_orig), HP_INICIAL.get(id_peca, 3))
        
        self.tabuleiro.entities[r_orig][c_orig] = 0
        self.tabuleiro.entities[r_dest][c_dest] = id_peca
        self.hp_unidades[(r_dest, c_dest)] = hp_atual