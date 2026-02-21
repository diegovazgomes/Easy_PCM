# easypcm/ui_labels.py

# Botões do menu principal (sempre visíveis)
BTN_OPEN = "Abrir OS"
BTN_UPDATE = "Atualizar OS"
BTN_CLOSE = "Fechar OS"
BTN_CONSULT = "Consultar OS"

# Comandos alternativos (caso usuário digite)
CMD_OPEN = "/abrir"
CMD_UPDATE = "/atualizar"
CMD_CLOSE = "/fechar"
CMD_MENU_1 = "/menu"
CMD_MENU_2 = "/opcoes"
CMD_MENU_3 = "/opções"

# Callback prefixes
CB_CLOSE_PREFIX = "close:"
CB_UPDATE_PREFIX = "update:"
CB_VIEW_PREFIX = "view:"          # (futuro)
CB_STATUS_PREFIX = "status:"      # status:<VALOR>

# Status (MVP) - valores que vão para o banco
STATUS_ABERTA = "ABERTA"
STATUS_EM_ANDAMENTO = "EM_ANDAMENTO"
STATUS_AGUARDANDO_COMPRAS = "AGUARDANDO_COMPRAS"
STATUS_AGUARDANDO_TI = "AGUARDANDO_TI"
STATUS_AGUARDANDO_SEGURANCA = "AGUARDANDO_SEGURANCA"
STATUS_AGUARDANDO_PARADA = "AGUARDANDO_PARADA"
STATUS_AGUARDANDO_TERCEIRO = "AGUARDANDO_TERCEIRO"
STATUS_AGUARDANDO_OUTROS = "AGUARDANDO_OUTROS"
STATUS_FECHADA = "FECHADA"
STATUS_CANCELADA = "CANCELADA"

# Lista para teclado de status (Atualizar OS)
STATUS_OPTIONS = [
    ("Aberta", STATUS_ABERTA),
    ("Em andamento", STATUS_EM_ANDAMENTO),
    ("Aguardando compras", STATUS_AGUARDANDO_COMPRAS),
    ("Aguardando TI", STATUS_AGUARDANDO_TI),
    ("Aguardando segurança", STATUS_AGUARDANDO_SEGURANCA),
    ("Aguardando parada", STATUS_AGUARDANDO_PARADA),
    ("Aguardando terceiro", STATUS_AGUARDANDO_TERCEIRO),
    ("Aguardando outros", STATUS_AGUARDANDO_OUTROS),
]
