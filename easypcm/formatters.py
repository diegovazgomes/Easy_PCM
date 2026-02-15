def format_os_message(data: dict) -> str:
    def safe_get(key: str):
        val = data.get(key)
        if val is None or val == "" or val == "SEM INFORMAÇÃO":
            return "SEM INFORMAÇÃO"
        return str(val)

    equipamento = safe_get("equipamento")
    setor = safe_get("setor")
    solicitante = safe_get("solicitante")
    executor = safe_get("executor")
    descricao = safe_get("descrição_do_problema")
    tipo = safe_get("tipo_manutenção")
    status = safe_get("status")
    tempo = safe_get("tempo_gasto_minutos")
    custo = safe_get("custo_peças")
    solucao = safe_get("solução_aplicada")

    msg = (
        "🟢 OS REGISTRADA (PRÉ-ANÁLISE)\n\n"
        f"🔧 Equipamento: {equipamento}\n"
        f"📍 Setor: {setor}\n"
        f"📝 Solicitante: {solicitante}\n"
        f"👨‍🔧 Executor: {executor}\n"
        f"⚙️ Tipo de manutenção: {tipo}\n"
        f"📌 Status: {status}\n"
        f"⏱ Tempo gasto (min): {tempo}\n"
        f"💰 Custo de peças: {custo}\n"
        f"🚨 Problema detectado:\n{descricao}\n"
        f"🛠 Solução aplicada:\n{solucao}"
    )
    return msg
