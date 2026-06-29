# estado_jogo.py
from config import (
    TURNO_JOGADOR,
    TURNO_INIMIGO,
    MODO_NAVEGACAO,
    HP_INICIAL,
    DANO_UNIDADE,
)


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
        self.turno_atual = (
            TURNO_INIMIGO if self.turno_atual == TURNO_JOGADOR else TURNO_JOGADOR
        )

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
        """Aplica o dano base e calcula o efeito de empurrão (apenas para robôs e insetos)."""
        origem_r, origem_c = self.pos_selecionada
        id_atacante = self.peca_selecionada
        id_alvo = self.tabuleiro.entities[alvo_r][alvo_c]

        # 1. APLICAR DANO DIRETO INICIAL
        dano_base = DANO_UNIDADE.get(id_atacante, 1)
        print(
            f"\n⚔️ ATAQUE: Peça {id_atacante} atacou Peça {id_alvo} em [{alvo_r}][{alvo_c}]"
        )

        # Salva o HP antes do ataque para saber se o alvo vai sobreviver
        hp_alvo_antes = self.hp_unidades.get((alvo_r, alvo_c), 0)
        self.causar_dano(alvo_r, alvo_c, dano_base)

        # Se o alvo morreu com o dano direto, não há necessidade de empurrar
        if hp_alvo_antes - dano_base <= 0:
            self.alternar_turno()
            return

        # 🛑 TRAVA ADICIONADA: Se o alvo for uma Casa (ID 50), ela NÃO é empurrada!
        if id_alvo == 50:
            print(
                "🏢 ESTRUTURA FIXA: Casas e edifícios civis absorvem o impacto e não podem ser empurrados."
            )
            self.alternar_turno()
            return

        # 2. CALCULAR VETOR E DIREÇÃO DO EMPURRÃO (Apenas para unidades móveis: Robôs e Insetos)
        dir_r = alvo_r - origem_r
        dir_c = alvo_c - origem_c

        if dir_r != 0:
            dir_r = 1 if dir_r > 0 else -1
        if dir_c != 0:
            dir_c = 1 if dir_c > 0 else -1

        dest_r = alvo_r + dir_r
        dest_c = alvo_c + dir_c

        print(f"➡️ Tentando empurrar Peça {id_alvo} para [{dest_r}][{dest_c}]...")

        # 3. VERIFICAR CENÁRIOS DE COLISÃO
        # Cenário A: Fora dos limites do tabuleiro
        if not (0 <= dest_r < 8 and 0 <= dest_c < 8):
            print(
                "🧱 COLISÃO: Empurrado contra os limites do mapa! +1 de dano extra por impacto."
            )
            self.causar_dano(alvo_r, alvo_c, 1)

        # Cenário B: Colisão com outra unidade ou obstáculo
        elif self.tabuleiro.entities[dest_r][dest_c] != 0:
            id_obstaculo = self.tabuleiro.entities[dest_r][dest_c]
            print(
                f"💥 COLISÃO: Empurrado contra Peça {id_obstaculo} em [{dest_r}][{dest_c}]! Ambas sofrem +1 de dano."
            )
            self.causar_dano(alvo_r, alvo_c, 1)
            self.causar_dano(dest_r, dest_c, 1)

        # Cenário C: Destino livre, mas é Água (Rio Jaguaribe = ID 1)
        elif self.tabuleiro.grid[dest_r][dest_c] == 1:
            if id_alvo != 10:  # Se não for o mosquito voador, afoga
                print(
                    f"🌊 AFOGAMENTO: Peça terrestre {id_alvo} foi jogada no Rio Jaguaribe e afundou!"
                )
                self.causar_dano(
                    alvo_r, alvo_c, self.hp_unidades.get((alvo_r, alvo_c), 99)
                )
            else:
                print(
                    "🪰 O Mosquito foi empurrado sobre o rio e continua flutuando com sucesso."
                )
                self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        # Cenário D: O bloco de destino está completamente vazio e seguro
        else:
            print("🍃 Destino limpo. Peça deslocada com sucesso para trás!")
            self.deslocar_entidade_fisicamente(alvo_r, alvo_c, dest_r, dest_c)

        self.alternar_turno()

    def deslocar_entidade_fisicamente(self, r_orig, c_orig, r_dest, c_dest):
        id_peca = self.tabuleiro.entities[r_orig][c_orig]
        hp_atual = self.hp_unidades.pop((r_orig, c_orig), HP_INICIAL.get(id_peca, 3))

        self.tabuleiro.entities[r_orig][c_orig] = 0
        self.tabuleiro.entities[r_dest][c_dest] = id_peca
        self.hp_unidades[(r_dest, c_dest)] = hp_atual
