import settings
from lore_data import LORE_STRINGS, LANG_EN, LANG_PT

STRINGS = {
    # Menu
    "menu_start": {LANG_EN: "START GAME", LANG_PT: "INICIAR JOGO"},
    "menu_continue": {LANG_EN: "CONTINUE", LANG_PT: "CONTINUAR"},
    "menu_how_to": {LANG_EN: "HOW TO PLAY", LANG_PT: "COMO JOGAR"},
    "menu_quit": {LANG_EN: "QUIT", LANG_PT: "SAIR"},
    "menu_language": {LANG_EN: "LANGUAGE", LANG_PT: "IDIOMA"},
    "menu_difficulty": {LANG_EN: "DIFFICULTY", LANG_PT: "DIFICULDADE"},
    "difficulty_easy": {LANG_EN: "EASY", LANG_PT: "FÁCIL"},
    "difficulty_medium": {LANG_EN: "MEDIUM", LANG_PT: "MÉDIO"},
    "difficulty_hard": {LANG_EN: "HARD", LANG_PT: "DIFÍCIL"},
    "menu_nav": {LANG_EN: "Use UP/DOWN to navigate, ENTER to select", LANG_PT: "Use CIMA/BAIXO para navegar, ENTER para selecionar"},
    "game_title": {LANG_EN: "Ctrl + Alt + Math", LANG_PT: "Ctrl + Alt + Math"},
    "game_subtitle": {LANG_EN: "A Mathematical Rebellion", LANG_PT: "Uma Rebelião Matemática"},
    "intro_1": {LANG_EN: "In a world where math is forbidden,", LANG_PT: "Em um mundo onde a matemática é proibida,"},
    "intro_2": {LANG_EN: "you are the last mathematician.", LANG_PT: "você é o último matemático."},
    "intro_3": {LANG_EN: "Fight the regime with forbidden theorems.", LANG_PT: "Lute contra o regime com teoremas proibidos."},

    # HUD
    "hp": {LANG_EN: "HP", LANG_PT: "PV"},
    "rigor": {LANG_EN: "Rigor", LANG_PT: "Rigor"},
    "entropy": {LANG_EN: "Entropy", LANG_PT: "Entropia"},
    "wave": {LANG_EN: "Wave", LANG_PT: "Onda"},
    "skill_points": {LANG_EN: "Skill Points", LANG_PT: "Pontos de Habilidade"},
    "stats": {LANG_EN: "STATS", LANG_PT: "ATRIBUTOS"},
    "actions": {LANG_EN: "ACTIONS", LANG_PT: "AÇÕES"},
    "feed": {LANG_EN: "FEED", LANG_PT: "REGISTRO"},
    "controls_move": {LANG_EN: "WASD: Move", LANG_PT: "WASD: Mover"},
    "controls_atk": {LANG_EN: "Space: Atk", LANG_PT: "Espaço: Atk"},
    "controls_pitagoras": {LANG_EN: "1: Pitagoras", LANG_PT: "1: Pitágoras"},
    "controls_reflexao": {LANG_EN: "2: Reflexao", LANG_PT: "2: Reflexão"},
    "controls_rewind": {LANG_EN: "R: Rewind", LANG_PT: "R: Desfazer"},
    "controls_skills": {LANG_EN: "Tab: Skills", LANG_PT: "Tab: Habilidades"},
    "controls_pause": {LANG_EN: "Esc: Pause", LANG_PT: "Esc: Pausa"},
    "controls_quit_menu": {LANG_EN: "Q: Quit Menu", LANG_PT: "Q: Sair p/ Menu"},

    # How to Play
    "how_to_title": {LANG_EN: "HOW TO PLAY", LANG_PT: "COMO JOGAR"},
    "how_to_intro": {LANG_EN: "You are a mathematician fighting the regime.", LANG_PT: "Você é um matemático lutando contra o regime."},
    "how_to_move": {LANG_EN: "Use WASD or Arrow Keys to move around the arena.", LANG_PT: "Use WASD ou Setas para se mover na arena."},
    "how_to_combat": {LANG_EN: "COMBAT:", LANG_PT: "COMBATE:"},
    "how_to_space": {LANG_EN: "  Space - Basic attack (melee range)", LANG_PT: "  Espaço - Ataque básico (curto alcance)"},
    "how_to_1": {LANG_EN: "  1 - Pitagoras theorem attack (if unlocked)", LANG_PT: "  1 - Ataque do teorema de Pitágoras (se desbloqueado)"},
    "how_to_2": {LANG_EN: "  2 - Reflexao defensive burst (if unlocked)", LANG_PT: "  2 - Explosão defensiva de Reflexão (se desbloqueado)"},
    "how_to_r": {LANG_EN: "  R - Ctrl+Z rewind (+10 HP, increases Entropy)", LANG_PT: "  R - Desfazer Ctrl+Z (+10 HP, aumenta Entropia)"},
    "how_to_skills": {LANG_EN: "SKILL TREE:", LANG_PT: "ÁRVORE DE HABILIDADES:"},
    "how_to_tab": {LANG_EN: "  Press Tab to open the skill tree.", LANG_PT: "  Pressione Tab para abrir a árvore de habilidades."},
    "how_to_spend": {LANG_EN: "  Spend skill points to unlock theorem abilities.", LANG_PT: "  Gaste pontos de habilidade para desbloquear teoremas."},
    "how_to_prereq": {LANG_EN: "  Each skill has prerequisites that must be unlocked first.", LANG_PT: "  Cada habilidade tem pré-requisitos necessários."},
    "how_to_enemies": {LANG_EN: "ENEMIES:", LANG_PT: "INIMIGOS:"},
    "how_to_censor": {LANG_EN: "  Censor Linear - Moves directly toward you", LANG_PT: "  Censor Linear - Move-se diretamente para você"},
    "how_to_strawman": {LANG_EN: "  Falacia Espantalho - Erratic, creates decoys", LANG_PT: "  Falácia Espantalho - Errático, cria iscas"},
    "how_to_bayesian": {LANG_EN: "  Inquisidor Bayesiano - Predicts your movement", LANG_PT: "  Inquisidor Bayesiano - Prevê seu movimento"},
    "how_to_boss": {LANG_EN: "  O Grande Simplificador - The final boss", LANG_PT: "  O Grande Simplificador - O chefe final"},
    "how_to_win": {LANG_EN: "Survive all waves and defeat the boss to win!", LANG_PT: "Sobreviva a todas as ondas e vença o chefe para ganhar!"},
    "how_to_return": {LANG_EN: "Press Esc to return", LANG_PT: "Pressione Esc para retornar"},

    # Pause
    "paused": {LANG_EN: "PAUSED", LANG_PT: "PAUSADO"},
    "press_esc_resume": {LANG_EN: "Press Esc to resume", LANG_PT: "Pressione Esc para continuar"},
    "press_q_quit": {LANG_EN: "Press Q to quit to main menu", LANG_PT: "Pressione Q para sair para o menu principal"},
    "press_q_quit_short": {LANG_EN: "Press Q to quit to menu", LANG_PT: "Pressione Q para sair para o menu"},

    # Game Over
    "game_over": {LANG_EN: "GAME OVER", LANG_PT: "FIM DE JOGO"},
    "fell_at": {LANG_EN: "You fell at: {room}", LANG_PT: "Você caiu em: {room}"},
    "fell_battle": {LANG_EN: "You fell in battle", LANG_PT: "Você caiu em batalha"},
    "regime_silenced": {LANG_EN: "The regime has silenced another mind.", LANG_PT: "O regime silenciou outra mente."},
    "upgrades_lost": {LANG_EN: "All upgrades lost.", LANG_PT: "Melhorias perdidas."},
    "press_enter_return": {LANG_EN: "Press ENTER to return to map", LANG_PT: "Pressione ENTER para voltar ao mapa"},

    # Victory
    "victory": {LANG_EN: "VICTORY!", LANG_PT: "VITÓRIA!"},
    "defeated_boss": {LANG_EN: "You defeated O Grande Simplificador!", LANG_PT: "Você derrotou O Grande Simplificador!"},
    "complexity_survives": {LANG_EN: "You proved that complexity survives.", LANG_PT: "Você provou que a complexidade sobrevive."},
    "math_never_forgotten": {LANG_EN: "Mathematics will never be forgotten.", LANG_PT: "A matemática nunca será esquecida."},
    "victory_quote": {LANG_EN: "\"The universe cannot be reduced to simple answers.\"", LANG_PT: "\"O universo não pode ser reduzido a respostas simples.\""},
    "press_enter_play_again": {LANG_EN: "Press ENTER to continue, Esc for new game", LANG_PT: "Pressione ENTER para continuar, Esc p/ novo jogo"},

    # Waves
    "wave_count": {LANG_EN: "Wave {wave}", LANG_PT: "Onda {wave}"},
    "press_key_begin": {LANG_EN: "Press any key to begin", LANG_PT: "Pressione qualquer tecla para começar"},
    "wave_complete": {LANG_EN: "WAVE COMPLETE", LANG_PT: "ONDA CONCLUÍDA"},
    "earned_skill_point": {LANG_EN: "You earned 1 Skill Point!", LANG_PT: "Você ganhou 1 Ponto de Habilidade!"},
    "press_tab_skills": {LANG_EN: "Press Tab to open Skill Tree", LANG_PT: "Pressione Tab p/ Árvore de Habilidades"},
    "press_key_continue": {LANG_EN: "Press any key to continue", LANG_PT: "Pressione qualquer tecla para continuar"},

    # Skill Tree
    "skill_tree_title": {LANG_EN: "SKILL TREE", LANG_PT: "ÁRVORE DE HABILIDADES"},
    "cost_free": {LANG_EN: "Free", LANG_PT: "Grátis"},
    "cost_label": {LANG_EN: "Cost: {cost}", LANG_PT: "Custo: {cost}"},
    "skill_unlocked_ok": {LANG_EN: "OK", LANG_PT: "OK"},
    "skill_tree_footer": {LANG_EN: "Click to unlock | Tab / Esc to close", LANG_PT: "Clique p/ desbloquear | Tab / Esc p/ fechar"},

    # Feedback / Floating Text
    "qed": {LANG_EN: "QED", LANG_PT: "QED"},
    "qed_full": {LANG_EN: "Quod Erat Demonstrandum", LANG_PT: "Quod Erat Demonstrandum"},
    "qed_translated": {LANG_EN: "\"What was to be demonstrated\"", LANG_PT: "\"Como se queria demonstrar\""},
    "eliminated": {LANG_EN: "exists=0 (eliminated)", LANG_PT: "existe=0 (eliminado)"},
    "map_title": {LANG_EN: "THE FORBIDDEN ARCHIVE", LANG_PT: "O ARQUIVO PROIBIDO"},
    "press_enter_room": {LANG_EN: "Press ENTER to enter", LANG_PT: "Pressione ENTER para entrar"},
    "room_completed_replay": {LANG_EN: "Completed - ENTER to replay", LANG_PT: "Concluído - ENTER p/ jogar de novo"},
    "unknown": {LANG_EN: "???", LANG_PT: "???"},
    "map_footer": {LANG_EN: "WASD: Navigate | ENTER: Enter | ESC: Menu", LANG_PT: "WASD: Navegar | ENTER: Entrar | ESC: Menu"},
    "class_label": {LANG_EN: "Class: {name}", LANG_PT: "Classe: {name}"},
    "theme_label": {LANG_EN: "Theme: {name}", LANG_PT: "Tema: {name}"},
    "miss": {LANG_EN: "Miss", LANG_PT: "Errou"},
    "crit": {LANG_EN: "CRIT!", LANG_PT: "CRÍT!"},
    "blocked": {LANG_EN: "BLOCKED", LANG_PT: "BLOQUEADO"},
    "no_hit": {LANG_EN: "NO HIT", LANG_PT: "NÃO ACERTOU"},
    "out_of_reach": {LANG_EN: "OUT OF REACH", LANG_PT: "FORA DE ALCANCE"},
    "out_of_range": {LANG_EN: "OUT OF RANGE", LANG_PT: "FORA DE ALCANCE"},
    "skill_locked": {LANG_EN: "SKILL LOCKED", LANG_PT: "HABILIDADE BLOQUEADA"},
    "not_enough_rigor": {LANG_EN: "NOT ENOUGH RIGOR", LANG_PT: "RIGOR INSUFICIENTE"},
    "rewind_locked": {LANG_EN: "REWIND LOCKED", LANG_PT: "REBOBINAR BLOQUEADO"},
    "no_rewind_available": {LANG_EN: "NO REWIND AVAILABLE", LANG_PT: "SEM REBOBINAR DISPONIVEL"},
    "wait": {LANG_EN: "Wait", LANG_PT: "Aguardar"},

    # Enemies
    "enemy_censor": {LANG_EN: "Censor Linear", LANG_PT: "Censor Linear"},
    "enemy_strawman": {LANG_EN: "Falacia Espantalho", LANG_PT: "Falácia Espantalho"},
    "enemy_bayesian": {LANG_EN: "Inquisidor Bayesiano", LANG_PT: "Inquisidor Bayesiano"},
    "enemy_boss": {LANG_EN: "O Grande Simplificador", LANG_PT: "O Grande Simplificador"},
    "enemy_unknown": {LANG_EN: "Unknown Entity", LANG_PT: "Entidade Desconhecida"},
    "lore_unknown": {LANG_EN: "A mysterious figure lurking in the mathematical shadows.", LANG_PT: "Uma figura misteriosa espreitando nas sombras matemáticas."},

    "lore_censor": {
        LANG_EN: "A relentless enforcer of mathematical purity. It seeks to eliminate any equation that doesn't fit the regime's narrow logic.",
        LANG_PT: "Um executor implacável da pureza matemática. Busca eliminar qualquer equação que não se encaixe na lógica estreita do regime."
    },
    "lore_strawman": {
        LANG_EN: "Distorts reality by creating false targets. It avoids direct confrontation by manipulating the observer's perception.",
        LANG_PT: "Distorce a realidade criando alvos falsos. Evita o confronto direto manipulando a percepção do observador."
    },
    "lore_bayesian": {
        LANG_EN: "Calculates every possibility. It doesn't just attack where you are, but where you are most likely to be.",
        LANG_PT: "Calcula todas as possibilidades. Não ataca apenas onde você está, mas onde é mais provável que você esteja."
    },
    "lore_boss": {
        LANG_EN: "The ultimate authority of the regime. It reduces the infinite complexity of the universe into a single, suffocating truth.",
        LANG_PT: "A autoridade máxima do regime. Reduz a complexidade infinita do universo em uma verdade única e sufocante."
    },
    "enemy_ortogonal": {LANG_EN: "Orthogonal Enforcer", LANG_PT: "Executor Ortogonal"},
    "enemy_atirador": {LANG_EN: "Ranged Assassin", LANG_PT: "Atirador de Elite"},
    "enemy_granadeiro": {LANG_EN: "Area Denier", LANG_PT: "Granadeiro Tático"},
    "lore_ortogonal": {
        LANG_EN: "Attacks in four directions simultaneously. Its cross-shaped pattern leaves no escape.",
        LANG_PT: "Ataca em quatro direções simultaneamente. Seu padrão em cruz não deixa escapatória."
    },
    "lore_atirador": {
        LANG_EN: "Fires piercing shots in a straight line. Distance is no protection.",
        LANG_PT: "Dispara tiros perfurantes em linha reta. Distância não é proteção."
    },
    "lore_granadeiro": {
        LANG_EN: "Saturates an area with explosions. Staying close together is fatal.",
        LANG_PT: "Satura uma área com explosões. Ficar muito próximo é fatal."
    },

    # Skills
    "skill_axioma_name": {LANG_EN: "Axioma Básico", LANG_PT: "Axioma Básico"},
    "skill_axioma_desc": {
        LANG_EN: "The foundation of all\nmathematical thought.\nforall x: f(x) = f(x)",
        LANG_PT: "A base de todo\npensamento matemático.\npara todo x: f(x) = f(x)"
    },
    "skill_derivada_name": {LANG_EN: "Derivada", LANG_PT: "Derivada"},
    "skill_derivada_desc": {
        LANG_EN: "Predict enemy movement.\n+5% Dmg per tile moved\nthis turn. df/dx.",
        LANG_PT: "Preveja o movimento.\n+5% Dano por bloco movido\nneste turno. df/dx."
    },
    "skill_pitagoras_name": {LANG_EN: "Pitágoras", LANG_PT: "Pitágoras"},
    "skill_pitagoras_desc": {
        LANG_EN: "Geometric attack (r<=3).\nd = sqrt(dx^2+dy^2)\nDeals 25 damage.",
        LANG_PT: "Ataque geométrico (r<=3).\nd = sqrt(dx^2+dy^2)\nCausa 25 de dano."
    },
    "skill_ctrlz_name": {LANG_EN: "Ctrl+Z", LANG_PT: "Ctrl+Z"},
    "skill_ctrlz_desc": {
        LANG_EN: "Rewind to the previous turn.\nRestore +10 HP on rewind.\nPress R.",
        LANG_PT: "Volte ao turno anterior.\nRecupere +10 HP ao rebobinar.\nPressione R."
    },
    "skill_bayes_name": {LANG_EN: "Bayes", LANG_PT: "Bayes"},
    "skill_bayes_desc": {
        LANG_EN: "Improved prediction.\nP(A|B) = P(B|A)\n* P(A) / P(B)",
        LANG_PT: "Previsão aprimorada.\nP(A|B) = P(B|A)\n* P(A) / P(B)"
    },
    "skill_reflexao_name": {LANG_EN: "Reflexão", LANG_PT: "Reflexão"},
    "skill_reflexao_desc": {
        LANG_EN: "High-energy pulse (r<=2).\nArea damage skill.\nDeals 15 damage.",
        LANG_PT: "Pulso de alta energia (r<=2).\nHabilidade de dano em área.\nCausa 15 de dano."
    },
    "skill_entropia_name": {LANG_EN: "Entropia Controlada", LANG_PT: "Entropia Controlada"},
    "skill_entropia_desc": {
        LANG_EN: "Halve rewind entropy gain.\ndS -> dS/2\nMakes time theft safer.",
        LANG_PT: "Reduz pela metade a entropia do rewind.\ndS -> dS/2\nTorna o rewind mais seguro."
    },
    "skill_teoria_jogos_name": {LANG_EN: "Teoria dos Jogos", LANG_PT: "Teoria dos Jogos"},
    "skill_teoria_jogos_desc": {
        LANG_EN: "Reveal enemy targets.\nNash equilibrium:\nno regrets strategy.",
        LANG_PT: "Revele os alvos inimigos.\nEquilíbrio de Nash:\nestratégia sem arrependimento."
    },
    "skill_integral_name": {LANG_EN: "Integral", LANG_PT: "Integral"},
    "skill_integral_desc": {
        LANG_EN: "Lifesteal zone attack.\nRecovers 30% of damage\ndealt as HP. Key 3.",
        LANG_PT: "Ataque em zona de dreno.\nRecupera 30% do dano\ncausado como HP. Tecla 3."
    },
    "enemy_decoy": {LANG_EN: "Decoy Clone", LANG_PT: "Clone Chamariz"},
    "lore_decoy": {
        LANG_EN: "A mathematical fractal projection of the rebel. It mimics your appearance to draw enemy fire away from the real target.",
        LANG_PT: "Uma projeção fractal matemática do rebelde. Imita sua aparência para desviar o fogo inimigo do alvo real."
    },
    "skill_fractal_name": {LANG_EN: "Fractal", LANG_PT: "Fractal"},
    "skill_fractal_desc": {
        LANG_EN: "Summon a decoy clone.\nEnemies may target it\ninstead of you. Key 4.",
        LANG_PT: "Invoca um clone chamariz.\nInimigos podem mirar nele\nem vez de voce. Tecla 4."
    },
    "skill_gauss_name": {LANG_EN: "Gauss", LANG_PT: "Gauss"},
    "skill_gauss_desc": {
        LANG_EN: "Chain attack.\nBasic attack bounces to\nnearest enemy for % dmg.",
        LANG_PT: "Ataque em cadeia.\nAtaque basico ricocheteia\nno inimigo proximo."
    },
    "skill_simetria_name": {LANG_EN: "Simetria", LANG_PT: "Simetria"},
    "skill_simetria_desc": {
        LANG_EN: "Reflect damage back.\nThorns: X% of damage taken\nreturned to attacker.",
        LANG_PT: "Reflete dano de volta.\nEspinhos: X% do dano recebido\nretornado ao atacante."
    },
    "skill_matriz_name": {LANG_EN: "Matriz", LANG_PT: "Matriz"},
    "skill_matriz_desc": {
        LANG_EN: "Capstone mastery.\nAll buffs last +1 turn.\nGain +1 SP on unlock.",
        LANG_PT: "Maestria final.\nBuffs duram +1 turno.\nGanha +1 SP ao desbloquear."
    },

    # Skill Flavor Lore
    "skill_axioma_flavor": {LANG_EN: "The first thing they tried to erase was the equal sign.", LANG_PT: "A primeira coisa que tentaram apagar foi o sinal de igual."},
    "skill_derivada_flavor": {LANG_EN: "Change is the only constant the Regime fears.", LANG_PT: "A mudança é a única constante que o Regime teme."},
    "skill_pitagoras_flavor": {LANG_EN: "Triangles: the sharpest weapons in the archive.", LANG_PT: "Triângulos: as armas mais afiadas do arquivo."},
    "skill_ctrlz_flavor": {LANG_EN: "Time is just another variable we can manipulate.", LANG_PT: "O tempo é apenas mais uma variável que podemos manipular."},
    "skill_bayes_flavor": {LANG_EN: "Uncertainty is where rebellion grows.", LANG_PT: "A incerteza é onde a rebelião cresce."},
    "skill_reflexao_flavor": {LANG_EN: "Your own hatred will be your downfall.", LANG_PT: "Seu próprio ódio será sua ruína."},
    "skill_entropia_flavor": {LANG_EN: "Order is a fragile illusion.", LANG_PT: "A ordem é uma ilusão frágil."},
    "skill_teoria_jogos_flavor": {LANG_EN: "We are playing a game they already lost.", LANG_PT: "Estamos jogando um jogo que eles já perderam."},
    "skill_integral_flavor": {LANG_EN: "The area under the curve is the sum of all our victories.", LANG_PT: "A area sob a curva e a soma de todas as nossas vitorias."},
    "skill_fractal_flavor": {LANG_EN: "Every part contains the whole rebellion.", LANG_PT: "Cada parte contem a rebeliao inteira."},
    "skill_gauss_flavor": {LANG_EN: "The bell rings for the Regime's final hour.", LANG_PT: "O sino toca para a hora final do Regime."},
    "skill_simetria_flavor": {LANG_EN: "What they do to you, they do to themselves.", LANG_PT: "O que eles fazem a voce, fazem a si mesmos."},
    "skill_matriz_flavor": {LANG_EN: "The matrix has you. You have the matrix.", LANG_PT: "A matriz tem voce. Voce tem a matriz."},

    # Waves Narrative
    "wave_1_narr": {LANG_EN: "Mathematics is forbidden.\nBut reality still obeys it.", LANG_PT: "A matemática é proibida.\nMas a realidade ainda a obedece."},
    "wave_1_post": {LANG_EN: "You recover a lost axiom\nfrom a censored archive.", LANG_PT: "Você recupera um axioma perdido\nde um arquivo censurado."},
    "wave_2_narr": {LANG_EN: "The regime sends more censors.\nThey cannot erase what is proven.", LANG_PT: "O regime envia mais censores.\nEles não podem apagar o que foi provado."},
    "wave_2_post": {LANG_EN: "Derivatives and integrals\nwhisper in the static.", LANG_PT: "Derivadas e integrais\nsussurram na estática."},
    "wave_3_narr": {LANG_EN: "Rhetorical tricksters enter the field.\nThey distort your theorems.", LANG_PT: "Trapaceiros retóricos entram em campo.\nEles distorcem seus teoremas."},
    "wave_3_post": {LANG_EN: "You see through their\nlogical fallacies.", LANG_PT: "Você enxerga através de suas\nfalácias lógicas."},
    "wave_4_narr": {LANG_EN: "An Inquisidor Bayesiano joins.\nIt calculates your every move.", LANG_PT: "Um Inquisidor Bayesiano se junta.\nEle calcula cada movimento seu."},
    "wave_4_post": {LANG_EN: "Probability bends to your will.\nThe end approaches.", LANG_PT: "A probabilidade se curva à sua vontade.\nO fim se aproxima."},
    "wave_5_narr": {LANG_EN: "O Grande Simplificador approaches.\nIt wants to reduce all thought\nto one dimension.", LANG_PT: "O Grande Simplificador se aproxima.\nEle quer reduzir todo o pensamento\na uma dimensão."},
    "wave_6_narr": {LANG_EN: "Elite enforcers surround you.\nOnly proof withstands their assault.", LANG_PT: "Executores de elite te cercam.\nSó a prova resiste ao ataque deles."},
    "wave_7_narr": {LANG_EN: "The final confrontation.\nAll of mathematics hangs in the balance.", LANG_PT: "O confronto final.\nToda a matemática está em jogo."},

    # Map Rooms
    "room_archive_name": {LANG_EN: "The Archive", LANG_PT: "O Arquivo"},
    "room_archive_narr": {LANG_EN: "A safe haven where forbidden knowledge persists.", LANG_PT: "Um refúgio seguro onde o conhecimento proibido persiste."},
    "room_library_name": {LANG_EN: "Censored Library", LANG_PT: "Biblioteca Censurada"},
    "room_library_narr": {LANG_EN: "Books burn themselves as you enter.", LANG_PT: "Livros se queimam sozinhos ao entrar."},
    "room_logic_name": {LANG_EN: "Logic Chamber", LANG_PT: "Câmara da Lógica"},
    "room_logic_narr": {LANG_EN: "Every argument here must be proven.", LANG_PT: "Todo argumento aqui deve ser provado."},
    "room_gallery_name": {LANG_EN: "Proof Gallery", LANG_PT: "Galeria de Provas"},
    "room_gallery_narr": {LANG_EN: "Theorems hang on walls like paintings.", LANG_PT: "Teoremas pendem nas paredes como quadros."},
    "room_hall_name": {LANG_EN: "Derivative Hall", LANG_PT: "Salão da Derivada"},
    "room_hall_narr": {LANG_EN: "Rates of change echo through corridors.", LANG_PT: "Taxas de mudança ecoam pelos corredores."},
    "room_maze_name": {LANG_EN: "Fallacy Maze", LANG_PT: "Labirinto da Falácia"},
    "room_maze_narr": {LANG_EN: "Every path leads to a logical trap.", LANG_PT: "Cada caminho leva a uma armadilha lógica."},
    "room_tower_name": {LANG_EN: "Induction Tower", LANG_PT: "Torre da Indução"},
    "room_tower_narr": {LANG_EN: "Prove the base case to ascend.", LANG_PT: "Prove o caso base para ascender."},
    "room_dungeon_name": {LANG_EN: "Probability Dungeon", LANG_PT: "Masmorra da Probabilidade"},
    "room_dungeon_narr": {LANG_EN: "Bayesian inference is your only light.", LANG_PT: "A inferência Bayesiana é sua única luz."},
    "room_boss_censor_name": {LANG_EN: "The Censor General", LANG_PT: "O Censor Geral"},
    "room_boss_censor_narr": {LANG_EN: "The head of all censorship awaits.", LANG_PT: "O chefe de toda a censura aguarda."},
    "room_boss_engine_name": {LANG_EN: "The Reduction Engine", LANG_PT: "O Motor de Redução"},
    "room_boss_engine_narr": {LANG_EN: "It reduces complexity to nothing.", LANG_PT: "Ele reduz a complexidade a nada."},
    "room_boss_final_name": {LANG_EN: "O Grande Simplificador", LANG_PT: "O Grande Simplificador"},
    "room_boss_final_narr": {LANG_EN: "The final boss. It wants one-dimensional thought.", LANG_PT: "O chefe final. Ele quer o pensamento unidimensional."},
    "room_victory_name": {LANG_EN: "The Unbound Theorem", LANG_PT: "O Teorema Liberto"},
    "room_victory_narr": {LANG_EN: "Mathematics cannot be contained.", LANG_PT: "A matemática não pode ser contida."},
    "room_sanctuary_name": {LANG_EN: "Integral Sanctuary", LANG_PT: "Santuário Integral"},
    "room_sanctuary_narr": {LANG_EN: "Accumulated knowledge flows here.", LANG_PT: "Conhecimento acumulado flui aqui."},
    "room_vault_name": {LANG_EN: "Matrix Vault", LANG_PT: "Cofre de Matrizes"},
    "room_vault_narr": {LANG_EN: "Linear transformations guard this room.", LANG_PT: "Transformações lineares guardam esta sala."},
    "room_lab_name": {LANG_EN: "Chaos Lab", LANG_PT: "Laboratório do Caos"},
    "room_lab_narr": {LANG_EN: "Small changes have massive consequences.", LANG_PT: "Pequenas mudanças têm consequências massivas."},
    "room_study_name": {LANG_EN: "The Study", LANG_PT: "O Estúdio"},
    "room_study_narr": {LANG_EN: "Desks covered in forgotten formulas.", LANG_PT: "Mesas cobertas de fórmulas esquecidas."},
    "room_cloister_name": {LANG_EN: "The Cloister", LANG_PT: "O Claustro"},
    "room_cloister_narr": {LANG_EN: "Silence amplifies the whispers of logic.", LANG_PT: "O silêncio amplifica os sussurros da lógica."},
    "room_atrium_name": {LANG_EN: "The Atrium", LANG_PT: "O Átrio"},
    "room_atrium_narr": {LANG_EN: "Numbers spiral up the pillars like ivy.", LANG_PT: "Números espiralizam pelos pilares como hera."},
    "room_vestibule_name": {LANG_EN: "The Vestibule", LANG_PT: "O Vestíbulo"},
    "room_vestibule_narr": {LANG_EN: "A threshold between reason and chaos.", LANG_PT: "Um limiar entre a razão e o caos."},
    "room_observatory_name": {LANG_EN: "The Observatory", LANG_PT: "O Observatório"},
    "room_observatory_narr": {LANG_EN: "Stars align in prime-numbered constellations.", LANG_PT: "Estrelas se alinham em constelações de números primos."},
    "room_scriptorium_name": {LANG_EN: "The Scriptorium", LANG_PT: "O Scriptório"},
    "room_scriptorium_narr": {LANG_EN: "Monks transcribe forbidden equations by candlelight.", LANG_PT: "Monges transcrevem equações proibidas à luz de velas."},
    "room_catacomb_name": {LANG_EN: "The Catacombs", LANG_PT: "As Catacumbas"},
    "room_catacomb_narr": {LANG_EN: "Forgotten theorems are buried in these tunnels.", LANG_PT: "Teoremas esquecidos estão enterrados nestes túneis."},
    "room_citadel_name": {LANG_EN: "The Citadel", LANG_PT: "A Cidadela"},
    "room_citadel_narr": {LANG_EN: "A fortress built atop a mountain of discarded proofs.", LANG_PT: "Uma fortaleza construída sobre uma montanha de provas descartadas."},
    "room_fortress_name": {LANG_EN: "The Fortress", LANG_PT: "A Fortaleza"},
    "room_fortress_narr": {LANG_EN: "Iron walls inscribed with paradoxes that weaken the regime.", LANG_PT: "Paredes de ferro inscritas com paradoxos que enfraquecem o regime."},
    "room_stronghold_name": {LANG_EN: "The Stronghold", LANG_PT: "O Bastião"},
    "room_stronghold_narr": {LANG_EN: "The last bastion of free thought. Defend it at all cost.", LANG_PT: "O último bastião do pensamento livre. Defenda-o a todo custo."},
    
    # Intent Tooltips
    "tip_attack_area": {LANG_EN: "ATTACK AREA", LANG_PT: "ÁREA DE ATAQUE"},
    "tip_attack_desc": {LANG_EN: "Enemy will hit this tile next turn.", LANG_PT: "Inimigo atingirá este bloco no próximo turno."},
    "tip_move_vector": {LANG_EN: "MOVEMENT VECTOR", LANG_PT: "VETOR DE MOVIMENTO"},
    "tip_move_desc": {LANG_EN: "Enemy plans to relocate to this position.", LANG_PT: "Inimigo planeja se realocar para esta posição."},
    "tip_decoy_area": {LANG_EN: "DECOY INDICATOR", LANG_PT: "INDICADOR DE DECOY"},
    "tip_decoy_desc": {LANG_EN: "A false threat created to confuse you.", LANG_PT: "Uma ameaça falsa criada para te confundir."},
    "tip_player_move": {LANG_EN: "REACHABLE AREA", LANG_PT: "ÁREA ALCANÇÁVEL"},
    "tip_player_move_desc": {LANG_EN: "Tiles you can move to this turn.", LANG_PT: "Blocos para os quais você pode se mover este turno."},
    "tip_player_attack": {LANG_EN: "TARGET AREA", LANG_PT: "ÁREA DE ALVO"},
    "tip_player_attack_desc": {LANG_EN: "Tiles currently within your strike range.", LANG_PT: "Blocos atualmente dentro do seu alcance de ataque."},

    # Lobby / Multiplayer
    "lobby_title": {LANG_EN: "ONLINE MULTIPLAYER", LANG_PT: "MULTIPLAYER ONLINE"},
    "lobby_host": {LANG_EN: "Create Room", LANG_PT: "Criar Sala"},
    "lobby_join": {LANG_EN: "Join Room", LANG_PT: "Entrar na Sala"},
    "lobby_back": {LANG_EN: "Back", LANG_PT: "Voltar"},
    "lobby_hosting": {LANG_EN: "Room Created", LANG_PT: "Sala Criada"},
    "lobby_waiting": {LANG_EN: "Waiting for player... Room: {ip}", LANG_PT: "Aguardando jogador... Sala: {ip}"},
    "lobby_player_joined": {LANG_EN: "Player 2 connected!", LANG_PT: "Jogador 2 conectado!"},
    "lobby_start_prompt": {LANG_EN: "Press ENTER to start game", LANG_PT: "Pressione ENTER para comecar"},
    "lobby_esc_cancel": {LANG_EN: "ESC to cancel", LANG_PT: "ESC para cancelar"},
    "lobby_choose_help": {LANG_EN: "Create a room, then have the second player join it with the room code.", LANG_PT: "Crie uma sala e o segundo jogador entra usando o codigo da sala."},
    "lobby_share_ip": {LANG_EN: "Share this room code with the second player.", LANG_PT: "Compartilhe este codigo de sala com o segundo jogador."},
    "lobby_joining": {LANG_EN: "Join Room", LANG_PT: "Entrar na Sala"},
    "lobby_enter_ip": {LANG_EN: "Enter room code or ROOM@server:port:", LANG_PT: "Digite o codigo da sala ou SALA@servidor:porta:"},
    "lobby_scan_hint": {LANG_EN: "Default server shown below", LANG_PT: "Servidor padrao mostrado abaixo"},
    "lobby_join_help": {LANG_EN: "Example: ABC123 or ABC123@server:5555", LANG_PT: "Exemplo: ABC123 ou ABC123@servidor:5555"},
    "lobby_scanning": {LANG_EN: "Use the dedicated match server", LANG_PT: "Use o servidor dedicado"},
    "lobby_found": {LANG_EN: "Found {n} room(s)", LANG_PT: "{n} sala(s) encontrada(s)"},
    "lobby_no_hosts": {LANG_EN: "No rooms found", LANG_PT: "Nenhuma sala encontrada"},
    "lobby_select_host": {LANG_EN: "Select a room:", LANG_PT: "Selecione uma sala:"},
    "lobby_connected": {LANG_EN: "Connected to room!", LANG_PT: "Conectado a sala!"},
    "lobby_press_start": {LANG_EN: "Press ENTER to ready up", LANG_PT: "Pressione ENTER para pronto"},
    "lobby_connected_help": {LANG_EN: "Both players are in. Click or press ENTER to continue.", LANG_PT: "Os dois jogadores entraram. Clique ou pressione ENTER para continuar."},
    "lobby_waiting_host": {LANG_EN: "Waiting for host to start...", LANG_PT: "Aguardando o host iniciar..."},
    "lobby_match_server": {LANG_EN: "Match server:", LANG_PT: "Servidor da partida:"},
    "lobby_room_code": {LANG_EN: "Room code: {code}", LANG_PT: "Codigo da sala: {code}"},
    "lobby_default_server": {LANG_EN: "Default server: {server}", LANG_PT: "Servidor padrao: {server}"},
    "mp_vote_hint": {LANG_EN: "Stand on a room and press ENTER to vote — both players must agree", LANG_PT: "Vá a uma sala e pressione ENTER para votar — ambos devem concordar"},
    "mp_waiting_partner": {LANG_EN: "Waiting for partner to confirm this room...", LANG_PT: "Aguardando parceiro confirmar esta sala..."},
    "mp_vote_mismatch": {LANG_EN: "Partner wants: {room} — navigate to agree!", LANG_PT: "Parceiro quer: {room} — navegue para concordar!"},
    "mp_vote_entering": {LANG_EN: "Both agreed! Entering room...", LANG_PT: "Ambos concordaram! Entrando na sala..."},
    "menu_multiplayer": {LANG_EN: "ONLINE MULTIPLAYER", LANG_PT: "MULTIPLAYER ONLINE"},
    "menu_achievements": {LANG_EN: "ACHIEVEMENTS", LANG_PT: "CONQUISTAS"},
    "achievements_title": {LANG_EN: "ACHIEVEMENTS", LANG_PT: "CONQUISTAS"},

    # Achievements
    "ach_first_room_name": {LANG_EN: "The First Proof", LANG_PT: "A Primeira Prova"},
    "ach_first_room_desc": {LANG_EN: "Complete your first room.", LANG_PT: "Complete sua primeira sala."},
    "ach_no_damage_name": {LANG_EN: "Untouchable", LANG_PT: "Intocável"},
    "ach_no_damage_desc": {LANG_EN: "Complete a room without taking damage.", LANG_PT: "Complete uma sala sem sofrer dano."},
    "ach_fast_win_name": {LANG_EN: "Efficient Thinker", LANG_PT: "Pensador Eficiente"},
    "ach_fast_win_desc": {LANG_EN: "Complete a room in less than 10 turns.", LANG_PT: "Complete uma sala em menos de 10 turnos."},
    "ach_skill_master_name": {LANG_EN: "Forbidden Knowledge", LANG_PT: "Conhecimento Proibido"},
    "ach_skill_master_desc": {LANG_EN: "Unlock 5 or more skills.", LANG_PT: "Desbloqueie 5 ou mais habilidades."},
    "ach_crit_thinking_name": {LANG_EN: "Critical Thinking", LANG_PT: "Pensamento Crítico"},
    "ach_crit_thinking_desc": {LANG_EN: "Land 3 critical hits in a single room.", LANG_PT: "Acerte 3 golpes críticos em uma única sala."},
    "ach_math_god_name": {LANG_EN: "Q.E.D.", LANG_PT: "Q.E.D."},
    "ach_math_god_desc": {LANG_EN: "Reach the ultimate conclusion of the proof.", LANG_PT: "Alcance a conclusão definitiva da prova."},
    "ach_stars_1": {LANG_EN: "Easy", LANG_PT: "Fácil"},
    "ach_stars_2": {LANG_EN: "Medium", LANG_PT: "Médio"},
    "ach_stars_3": {LANG_EN: "Hard", LANG_PT: "Difícil"},
    "ach_locked": {LANG_EN: "Locked", LANG_PT: "Bloqueado"},
    "achievement_unlocked_toast": {LANG_EN: "Achievement Unlocked!", LANG_PT: "Conquista Desbloqueada!"},
    "lore_toast_title": {LANG_EN: "BERNOULLI LOG", LANG_PT: "REGISTRO BERNOULLI"},
    "ach_reset_hint": {LANG_EN: "Press R to Reset All Achievements", LANG_PT: "Pressione R para Reiniciar Conquistas"},
    "map_title": {LANG_EN: "WORLD ARCHIVE", LANG_PT: "ARQUIVO MUNDIAL"},
    
    # Skill tree Theorem Card details
    "skill_stats_title": {LANG_EN: "FORMULA STATS", LANG_PT: "ATRIBUTOS DA FÓRMULA"},
    "skill_operational": {LANG_EN: "State: Fully Operational", LANG_PT: "Estado: Totalmente Operacional"},
    "skill_maxed": {LANG_EN: "THEOREM MAXED OUT", LANG_PT: "TEOREMA NO MÁXIMO"},
    "skill_next_level_cost": {LANG_EN: "Next Level cost: {cost} SP", LANG_PT: "Custo do próximo nível: {cost} PH"},
    "stat_base_dmg": {LANG_EN: "Base Damage: {dmg}", LANG_PT: "Dano Base: {dmg}"},
    "stat_pitagoras": {LANG_EN: "Dmg: {dmg}  |  Range: {rng} tiles", LANG_PT: "Dano: {dmg}  |  Alcance: {rng} blocos"},
    "stat_reflexao": {LANG_EN: "Area Dmg: {dmg}  |  Radius: {rng} tiles", LANG_PT: "Dano em Área: {dmg}  |  Raio: {rng} blocos"},
    "stat_ctrlz": {LANG_EN: "Rewind: {undo} turns  |  Heal: +{heal} HP", LANG_PT: "Desfazer: {undo} turnos  |  Cura: +{heal} PV"},
    "stat_entropia": {LANG_EN: "Entropy Gain: -{red}%", LANG_PT: "Ganho de Entropia: -{red}%"},
    "stat_derivada": {LANG_EN: "Damage Buff: +{percent}% per tile", LANG_PT: "Bônus de Dano: +{percent}% por bloco"},
    "stat_teoria_jogos": {LANG_EN: "Crit Chance Bonus: +{percent}%", LANG_PT: "Bônus de Chance Crítica: +{percent}%"},

    # Shop Screen
    "shop_title": {LANG_EN: "FORBIDDEN BAZAAR", LANG_PT: "BAZAR PROIBIDO"},
    "shop_gold": {LANG_EN: "Gold: {gold}", LANG_PT: "Ouro: {gold}"},
    "shop_tab_weapons": {LANG_EN: "WEAPONS", LANG_PT: "ARMAS"},
    "shop_tab_shields": {LANG_EN: "SHIELDS", LANG_PT: "ESCUDOS"},
    "shop_tab_consumables": {LANG_EN: "ITEMS", LANG_PT: "ITENS"},
    "shop_already_equipped": {LANG_EN: "Already equipped!", LANG_PT: "Já equipado!"},
    "shop_insufficient_funds": {LANG_EN: "Insufficient Gold/SP!", LANG_PT: "Ouro/SP insuficiente!"},
    "shop_equipped_feedback": {LANG_EN: "{name} equipped!", LANG_PT: "{name} equipado!"},
    "shop_added_feedback": {LANG_EN: "{name} added!", LANG_PT: "{name} adicionado!"},
    "shop_purchased_feedback": {LANG_EN: "{name} purchased!", LANG_PT: "{name} comprado!"},
    "shop_equipped_status": {LANG_EN: "EQUIPPED", LANG_PT: "EQUIPADO"},
    "shop_select_prompt": {LANG_EN: "Select an item", LANG_PT: "Selecione um item"},
    "shop_atk_multiplier": {LANG_EN: "ATK Multiplier: x{mult}", LANG_PT: "Multiplicador ATK: x{mult}"},
    "shop_effect_label": {LANG_EN: "Effect: {effect}", LANG_PT: "Efeito: {effect}"},
    "shop_buy_button": {LANG_EN: "BUY {cost}", LANG_PT: "COMPRAR {cost}"},
    "shop_defense_bonus": {LANG_EN: "+{defense} DEF", LANG_PT: "+{defense} DEF"},
    
    # Weapon effects
    "effect_burn": {LANG_EN: "Burn (3 dmg/2t)", LANG_PT: "Queimadura (3 dmg/2t)"},
    "effect_slow": {LANG_EN: "Slow (-1 mov, 1t)", LANG_PT: "Lentidão (-1 mov, 1t)"},
    "effect_stun": {LANG_EN: "Stun (35% chance)", LANG_PT: "Atordoador (35% chance)"},
    "effect_aoe": {LANG_EN: "Area (hits adjacent)", LANG_PT: "Área (atinge adjacentes)"},
    "effect_poison": {LANG_EN: "Poison (2 dmg/3t)", LANG_PT: "Veneno (2 dmg/3t)"},
    "effect_reflect": {LANG_EN: "Reflect 25% of damage", LANG_PT: "Reflete 25% do dano"},
    
    # Consumable effects
    "effect_heal": {LANG_EN: "Restores {value} HP", LANG_PT: "Restaura {value} PV"},
    "effect_atk_buff": {LANG_EN: "+{value} ATK", LANG_PT: "+{value} ATK"},
    "effect_def_buff": {LANG_EN: "+{value} DEF", LANG_PT: "+{value} DEF"},
    "effect_range_buff": {LANG_EN: "+{value} Range", LANG_PT: "+{value} alcance"},
    "effect_max_hp_buff": {LANG_EN: "+{value} Max HP", LANG_PT: "+{value} vida máxima"},
    
    # Consumable scope
    "scope_instant": {LANG_EN: "Instant use", LANG_PT: "Uso imediato"},
    "scope_room": {LANG_EN: "Lasts until room exit", LANG_PT: "Dura até sair da sala"},
    "scope_turns": {LANG_EN: "Lasts {duration} turns", LANG_PT: "Dura {duration} turnos"},

    # Upgrades Screen
    "upgrades_title": {LANG_EN: "UPGRADES", LANG_PT: "MELHORIAS"},
    "upgrades_stats": {LANG_EN: "Tickets: {tickets}  |  Gold: {gold}g", LANG_PT: "Tickets: {tickets}  |  Ouro: {gold}g"},
    "upgrades_free": {LANG_EN: "FREE", LANG_PT: "GRÁTIS"},
    "upgrades_projection_title": {LANG_EN: "STAT PROJECTION & SCALING", LANG_PT: "PROJEÇÃO DE ATRIBUTOS & ESCALAMENTO"},
    "upgrades_formula_label": {LANG_EN: "Cost(L) = {base_cost} * ({scale})^L", LANG_PT: "Custo(L) = {base_cost} * ({scale})^L"},
    "upgrades_current_level_cost": {LANG_EN: "Current Level: {level} (Next cost: {next_cost}g)", LANG_PT: "Nível Atual: {level} (Próximo custo: {next_cost}g)"},
    "upgrades_scaling_function": {LANG_EN: "Scaling Function:", LANG_PT: "Função de Escalamento:"},
    "upgrades_exponential_rate": {LANG_EN: "Exponential growth rate: +{rate}% per level", LANG_PT: "Taxa de crescimento exponencial: +{rate}% por nível"},
    "upgrades_hover_hint": {LANG_EN: "Hover over a stat to see math scaling.", LANG_PT: "Passe o mouse sobre um atributo para ver o escalamento."},
    "upgrades_close_hint": {LANG_EN: "Press U or ESC to close", LANG_PT: "Pressione U ou ESC para fechar"},
    
    "upgrade_atk_name": {LANG_EN: "ATK", LANG_PT: "ATAQUE"},
    "upgrade_atk_desc": {LANG_EN: "+3 damage/level", LANG_PT: "+3 de dano/nível"},
    "upgrade_def_name": {LANG_EN: "DEF", LANG_PT: "DEFESA"},
    "upgrade_def_desc": {LANG_EN: "+2 defense/level", LANG_PT: "+2 de defesa/nível"},
    "upgrade_hp_name": {LANG_EN: "HP", LANG_PT: "PV"},
    "upgrade_hp_desc": {LANG_EN: "+15 max hp/level", LANG_PT: "+15 PV máximo/nível"},
    "upgrade_range_name": {LANG_EN: "RANGE", LANG_PT: "ALCANCE"},
    "upgrade_range_desc": {LANG_EN: "+1 move tile/level", LANG_PT: "+1 bloco de movimento/nível"},

    # Inventory Screen
    "inv_title": {LANG_EN: "INVENTORY", LANG_PT: "INVENTÁRIO"},
    "inv_subtitle": {LANG_EN: "Select consumable items", LANG_PT: "Selecione itens consumíveis"},
    "inv_empty": {LANG_EN: "Empty", LANG_PT: "Vazio"},
    "inv_use_button": {LANG_EN: "Use", LANG_PT: "Usar"},
    "inv_details_title": {LANG_EN: "DETAILS", LANG_PT: "DETALHES"},
    "inv_effect_formula": {LANG_EN: "Effect function: f(x) -> {effect}", LANG_PT: "Função de efeito: f(x) -> {effect}"},
    "inv_hover_hint": {LANG_EN: "Hover over an item to inspect formulas.", LANG_PT: "Passe o mouse sobre um item para inspecionar fórmulas."},
    "inv_close_hint": {LANG_EN: "Press I or ESC to close", LANG_PT: "Pressione I ou ESC para fechar"},

    # Equipment Screen
    "eq_title": {LANG_EN: "EQUIPMENT", LANG_PT: "EQUIPAMENTO"},
    "eq_subtitle": {LANG_EN: "Active combat loadout", LANG_PT: "Configuração de combate ativa"},
    "eq_empty_slot": {LANG_EN: "Empty Slot", LANG_PT: "Espaço Vazio"},
    "eq_dmg_mult": {LANG_EN: "Damage multiplier: x{mult}", LANG_PT: "Multiplicador de dano: x{mult}"},
    "eq_base_def": {LANG_EN: "Base Defense rating: +{defense}", LANG_PT: "Classificação de defesa base: +{defense}"},
    "eq_details_title": {LANG_EN: "EQUIPMENT DETAILS & LORE", LANG_PT: "DETALHES DO EQUIPAMENTO & HISTÓRIA"},
    "eq_lore_prefix": {LANG_EN: "Lore: {desc}", LANG_PT: "História: {desc}"},
    "eq_effect_prefix": {LANG_EN: "Special Effect: {effect}", LANG_PT: "Efeito Especial: {effect}"},
    "eq_mechanics_title": {LANG_EN: "Combat Mechanics:", LANG_PT: "Mecânicas de Combate:"},
    "eq_hover_hint": {LANG_EN: "Hover over a slot to inspect gear.", LANG_PT: "Passe o mouse sobre um espaço para inspecionar o equipamento."},
    "eq_close_hint": {LANG_EN: "Press E or ESC to close", LANG_PT: "Pressione E ou ESC para fechar"},
    "eq_weapon_label": {LANG_EN: "WEAPON", LANG_PT: "ARMA"},
    "eq_shield_label": {LANG_EN: "SHIELD", LANG_PT: "ESCUDO"},

    # Math RPG Items (remote)
    "item_linear_blade_name": {LANG_EN: "Linear Blade", LANG_PT: "Lâmina Linear"},
    "item_linear_blade_desc": {LANG_EN: "A sharp line segment that draws precise cuts.", LANG_PT: "Um segmento de reta bem afiado que traça cortes precisos."},
    "item_fiery_tangent_name": {LANG_EN: "Fiery Tangent", LANG_PT: "Tangente Incandescente"},
    "item_fiery_tangent_desc": {LANG_EN: "Causes thermal combustion (3 dmg/2 turns).", LANG_PT: "Causa queimadura térmica (3 dmg/2 turnos)."},
    "item_cryo_bisector_name": {LANG_EN: "Cryogenic Bisector", LANG_PT: "Bissetriz Criogênica"},
    "item_cryo_bisector_desc": {LANG_EN: "Divides gelid space, slowing enemy movement for 1 turn.", LANG_PT: "Divide o espaço gélido, reduzindo o movimento do inimigo por 1 turno."},
    "item_fractal_thunder_axe_name": {LANG_EN: "Fractal Thunder Axe", LANG_PT: "Machado Fractal do Trovão"},
    "item_fractal_thunder_axe_desc": {LANG_EN: "Discharges bifurcating lightning with a chance to stun the enemy.", LANG_PT: "Descarrega raios bifurcados com chance de atordoar inimigo."},
    "item_singularity_staff_name": {LANG_EN: "Staff of Singularity", LANG_PT: "Cajado da Singularidade"},
    "item_singularity_staff_desc": {LANG_EN: "Gravitational waves that affect enemies adjacent to the target.", LANG_PT: "Ondas gravitacionais que afetam inimigos adjacentes ao alvo."},
    "item_null_matrix_dagger_name": {LANG_EN: "Dagger of the Null Matrix", LANG_PT: "Adaga de Matriz Nula"},
    "item_null_matrix_dagger_desc": {LANG_EN: "Corrodes the enemy's existence (2 dmg/3 turns).", LANG_PT: "Corrói a existência do inimigo (2 dmg/3 turnos)."},
    "item_max_modulus_axe_name": {LANG_EN: "Axe of the Maximum Modulus", LANG_PT: "Machado de Módulo Máximo"},
    "item_max_modulus_axe_desc": {LANG_EN: "Devastating raw damage calculated by the Euclidean norm.", LANG_PT: "Dano bruto devastador calculado pela norma euclidiana."},

    "item_cartesian_plane_shield_name": {LANG_EN: "Cartesian Plane Shield", LANG_PT: "Escudo do Plano Cartesiano"},
    "item_cartesian_plane_shield_desc": {LANG_EN: "Basic two-dimensional defense.", LANG_PT: "Proteção bidimensional básica."},
    "item_orthogonal_barrier_name": {LANG_EN: "Orthogonal Barrier", LANG_PT: "Barreira Ortogonal"},
    "item_orthogonal_barrier_desc": {LANG_EN: "Creates a right angle of resistance to impact.", LANG_PT: "Cria um ângulo reto de resistência ao impacto."},
    "item_reflection_matrix_name": {LANG_EN: "Reflection Matrix", LANG_PT: "Matriz de Reflexão"},
    "item_reflection_matrix_desc": {LANG_EN: "Inverts the enemy vector, reflecting 25% of damage received.", LANG_PT: "Inverte o vetor inimigo, refletindo 25% do dano recebido."},
    "item_steel_axiom_shield_name": {LANG_EN: "Axiom of Steel Shield", LANG_PT: "Escudo do Axioma de Aço"},
    "item_steel_axiom_shield_desc": {LANG_EN: "An absolute and indestructible truth of maximum protection.", LANG_PT: "Uma verdade absoluta e indestrutível de proteção máxima."},

    "item_linear_hp_formula_name": {LANG_EN: "Linear HP Formula", LANG_PT: "Fórmula Linear de HP"},
    "item_linear_hp_formula_desc": {LANG_EN: "Adds a positive constant, restoring 30 HP.", LANG_PT: "Soma uma constante positiva, restaurando 30 HP."},
    "item_riemann_hp_sum_name": {LANG_EN: "Riemann HP Sum", LANG_PT: "Soma de Riemann de HP"},
    "item_riemann_hp_sum_desc": {LANG_EN: "Integrates slices of vitality, restoring 60 HP.", LANG_PT: "Integra fatias de vitalidade, restaurando 60 HP."},
    "item_force_derivative_name": {LANG_EN: "Force Derivative", LANG_PT: "Derivada de Força"},
    "item_force_derivative_desc": {LANG_EN: "+10 ATK for 1 room (rate of power change).", LANG_PT: "+10 ATAQUE por 1 sala (taxa de variação de potência)."},
    "item_defense_constant_name": {LANG_EN: "Defense Constant", LANG_PT: "Constante de Defesa"},
    "item_defense_constant_desc": {LANG_EN: "+5 DEF for 3 turns (defensive numerical invariant).", LANG_PT: "+5 DEF por 3 turnos (invariante numérico defensivo)."},
    "item_translation_vector_name": {LANG_EN: "Translation Vector", LANG_PT: "Vetor de Translação"},
    "item_translation_vector_desc": {LANG_EN: "+2 range for 1 room (spatial displacement).", LANG_PT: "+2 alcance por 1 sala (deslocamento espacial)."},
    "item_vitality_integral_name": {LANG_EN: "Vitality Integral", LANG_PT: "Integral de Vitalidade"},
    "item_vitality_integral_desc": {LANG_EN: "+15 Max HP for the room (expands integrity boundary).", LANG_PT: "+15 PV máximo pela sala (expande o limite de integridade)."},
}

# Merge Lore Strings
STRINGS.update(LORE_STRINGS)

def t(key, **kwargs):
    lang = getattr(settings, "LANGUAGE", LANG_EN)
    text = STRINGS.get(key, {}).get(lang, key)
    if kwargs:
        return text.format(**kwargs)
    return text
