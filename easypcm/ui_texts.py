# easypcm/ui_texts.py

class TXT:
    # Menu
    MENU_TITLE = "Menu:"

    # Abertura
    OPEN_START = "Ok. Vamos abrir uma OS.\n\nInforme o equipamento/TAG:"
    ASK_SETOR = "Informe o setor (obrigatório):"
    SETOR_REQUIRED = "Setor é obrigatório. Informe o setor:"
    ASK_PROBLEMA = "Descreva o problema / serviço solicitado:"
    ASK_PARADA = "A máquina está parada? Responda: SIM ou NÃO"
    PARADA_INVALID = "Resposta inválida. Digite SIM ou NÃO:"

    @staticmethod
    def open_done(os_id: int, equipamento: str, setor: str, parada: str, problema: str) -> str:
        return (
            f"✅ OS #{os_id} ABERTA\n\n"
            f"Equipamento: {equipamento}\n"
            f"Setor: {setor}\n"
            f"Parada: {parada}\n"
            f"Problema: {problema}"
        )

    # Fechamento
    @staticmethod
    def close_intro(os_id: int) -> str:
        # first prompt in the close flow: ask for execution date
        return (
            f"Ok. Vamos fechar a OS #{os_id}.\n\n"
            "Escreva HOJE ou coloque a data no formato DD/MM/AAAA."
        )

    CLOSE_ASK_SOLUCAO = (
        "Descreva o serviço executado / solução aplicada:"
    )

    CLOSE_ASK_INICIO = (
        "Informe a hora de INÍCIO (HH:MM).\n"
        "Se o serviço passou de 1 dia, você pode informar o tempo total assim:\n"
        "TOTAL 3h  (ou TOTAL 180)"
    )
    CLOSE_INICIO_INVALID = "Formato inválido. Envie HH:MM (ex: 08:10) ou TOTAL 3h:"
    CLOSE_ASK_FIM = "Informe a hora de TÉRMINO (HH:MM):"
    CLOSE_FIM_INVALID = "Formato inválido. Envie HH:MM (ex: 09:40):"
    CLOSE_ASK_TECNICOS = "Informe o(s) técnico(s) (ex: Marcos, João):"
    CLOSE_ASK_MATERIAIS = (
        "Informe as peças utilizadas (separe por vírgula).\n"
        "Ex: Rolamento, Retentor 45mm, Graxa\n"
        "Se não houve peças, digite: NENHUMA"
    )
    CLOSE_DATE_INVALID = (
        "Formato inválido. Envie HOJE ou DD/MM/AAAA (ex: 26/02/2026)."
    )

    CLOSE_ASK_CUSTO = (
        "Informe o custo de peças em Reais(opcional). Pode ser 0. Ex: 50\n"
        "Se não souber, envie 0."
    )

    @staticmethod
    def close_done(os_id: int, equipamento: str, setor: str, data_fechamento: str, tempo_min: str, tecnicos: str, pecas: str, custo: str, solucao: str) -> str:
        return (
            f"✅ OS #{os_id} FECHADA\n\n"
            f"Data execução: {data_fechamento}\n"
            f"Equipamento: {equipamento}\n"
            f"Setor: {setor}\n"
            f"Tempo (min): {tempo_min}\n"
            f"Técnicos: {tecnicos}\n"
            f"Peças: {pecas}\n"
            f"Custo peças: {custo}\n"
            f"Solução: {solucao}"
        )

    # Atualizar OS
    UPDATE_PICK_OS = "Selecione a OS para atualizar:"
    @staticmethod
    def update_intro(os_id: int) -> str:
        return f"Ok. Vamos atualizar a OS #{os_id}.\n\nSelecione o novo status:"

    UPDATE_ASK_OBS = (
        "Deseja adicionar uma observação? (opcional)\n"
        "Ex: aguardando diafragma chegar\n\n"
        "Se não quiser, digite: PULAR"
    )

    @staticmethod
    def update_done(os_id: int, status: str, obs: str) -> str:
        obs_txt = obs if obs.strip() else "SEM OBSERVAÇÃO"
        return (
            f"✅ OS #{os_id} ATUALIZADA\n\n"
            f"Status: {status}\n"
            f"Obs: {obs_txt}"
        )

    # Gerais
    UNKNOWN_ACTION = "Ação não reconhecida."
    UNKNOWN_COMMAND = "Escolha uma opção abaixo ⬇"
    NO_OPEN_OS_TO_CLOSE = "Não encontrei OS abertas para fechar."
    NO_OPEN_OS_TO_UPDATE = "Não encontrei OS abertas para atualizar."
