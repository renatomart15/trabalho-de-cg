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
        """Mapeia a vida de todas as peças (incluindo as casas) no início do jogo."""
        for r in range(8):
            for c in range(8):
                id_peca = self.tabuleiro.entities[r][c]
                if id_peca != 0:
                    self.hp_unidades[(r, c)] = HP_INICIAL.get(id_peca, 3)

    def alternar_turno(self):
        """Limpa as seleções e passa o controle do turno."""
        self.peca_selecionada = None
        self.pos_selecionada = None
        self.estado_seletor = MODO_NAVEGACAO
        self.turno_atual = TURNO_INIMIGO if self.turno_atual == TURNO_JOGADOR else TURNO_JOGADOR
        print(f"🔄 Turno alterado! Agora é a vez do: {'JOGADOR (Robôs)' if self.turno_atual == TURNO_JOGADOR else 'INIMIGO (Insetos)'}")

    def causar_dano(self, r, c, quantidade):
        """Função auxiliar para aplicar dano a uma coordenada e gerenciar a morte/destruição."""
        if (r, c) not in self.hp_unidades:
            return
        
        id_alvo = self.tabuleiro.entities[r][c]
        self.hp_unidades[(r, c)] -= quantidade
        hp_restante = self.hp_unidades[(r, c)]
        
        print(f"💥 Peça {id_alvo} em [{r}][{c}] sofreu {quantidade} de dano! (HP restante: {hp_restante})")
        
        if hp_restante <= 0:
            print(f"💀 A Peça {id_alvo} em [{r}][{c}] foi completamente destruída!")
            self.tabuleiro.entities[r][c] = 0
            self.hp_unidades.pop((r, c), None)

    def aplicar_ataque(self, alvo_r, alvo_c):
        """Aplica o dano base e calcula o efeito de empurrão (knockback) tático."""
        origem_r, origem_c = self.pos_selecionada
        id_atacante = self.peca_selecionada
        id_alvo = self.tabuleiro.entities[alvo_r][alvo_c]
        
        # 1. APLICAR DANO DIRETO INICIAL
        dano_base = DANO_UNIDADE.get(id_atacante, 1)
        print(f"\n⚔️ ATAQUE: Peça {id_atacante} atacou Peça {id_alvo} em [{alvo_r}][{alvo_c}]")
        
        # Salva o HP antes do ataque para saber se o alvo vai sobreviver para ser empurrado
        hp_alvo_antes = self.hp_unidades.get((alvo_r, alvo_c), 0)
        self.causar_dano(alvo_r, alvo_c, dano_base)
        
        # Se o alvo morreu com o dano direto, não há necessidade de empurrar
        if hp_alvo_antes - dano_base <= 0:
            self.alternar_turno()
            return

        # 2. CALCULAR VETOR E DIREÇÃO DO EMPURRÃO (1 casa de deslocamento)
        # Se a diferença for positiva (+1), empurra para frente. Se negativa (-1), para trás.
        dir_r = alvo_r - origem_r
        dir_c = alvo_c - origem_c
        
        # Normaliza a direção para garantir o deslocamento exato de 1 casa (retira o efeito de alcances longos)
        if dir_r != 0: dir_r = 1 if dir_r > 0 else -1
        if dir_c != 0: dir_c = 1 if dir_c > 0 else -1
        
        dest_r = alvo_r + dir_r
        dest_c = alvo_c + dir_c
        
        print(f"➡️ Tentando empurrar Peça {id_alvo} para [{dest_r}][{dest_c}]...")

        # 3. VERIFICAR CENÁRIOS DE COLISÃO
        
        # Cenário A: Fora dos limites do tabuleiro (Borda do mapa 8x8)
        if not (0 <= dest_r < 8 and 0 <= dest_c < 8):
            print("🧱 COLISÃO: Empurrado contra os limites do mapa! +1 de dano extra por impacto.")
            self.causar_dano(alvo_r, alvo_c, 1)
            
        # Cenário B: Colisão com outra unidade ou obstáculo/casa ocupada
        elif self.tabuleiro.entities[dest_r][dest_c] != 0:
            id_obstaculo = self.tabuleiro.entities[dest_r][dest_c]
            print(f"💥 COLISÃO: Empurrado contra Peça {id_obstaculo} em [{dest_r}][{dest_c}]! Ambas sofrem +1 de dano.")
            
            # Aplica 1 de dano extra por colisão no alvo empurrado
            self.causar_dano(alvo_r, alvo_c, 1)
            # Aplica 1 de dano na peça que serviu de obstáculo no impacto
            self.causar_dano(dest_r, dest_c, 1)

        # Cenário C: Destino livre, mas é Água (Rio Jaguaribe = ID 1)
        elif self.tabuleiro.grid[dest_r][dest_c] == 1:
            # Se for uma unidade terrestre (Trator, Escavadeira ou Barata), ela se afoga!
            if id_alvo != 10:  # ID 10 é o Mosquito/Muriçoca (voador)
                print(f"🌊 AFOGAMENTO: Peça terrestre {id_alvo} foi jogada no Rio Jaguaribe e afundou!")
                # Remove instantaneamente zerando a vida
                self.causar_dano(alvo_r, alvo_c, self.hp_unidades.get((alvo_r, alvo_c), 99))
            else:
                # Mosquito voa sobre a água tranquilamente, então ele apenas se move para lá
                print("🪰 O Mosquito foi empurrado sobre o rio e continua flutuando com sucesso.")
                self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        # Cenário D: O bloco de destino está completamente vazio e seguro
        else:
            print("🍃 Destino limpo. Peça deslocada com sucesso para trás!")
            self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        self.alternar_turno()

    def deslocar_entidade_fisicamente(self, r_orig, c_orig, r_dest, c_dest):
        """Muda os dados da matriz e atualiza as chaves do dicionário de vida."""
        id_peca = self.tabuleiro.entities[r_orig][c_orig]
        hp_atual = self.hp_unidades.pop((r_orig, c_orig), HP_INICIAL.get(id_peca, 3))
        
        self.tabuleiro.entities[r_orig][c_orig] = 0
        self.tabuleiro.entities[r_dest][c_dest] = id_peca
        self.hp_unidades[(r_dest, c_dest)] = hp_atual