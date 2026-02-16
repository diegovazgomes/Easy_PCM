from .schemas import WorkOrder, SEM_INFO


def format_title(text: str) -> str:
    """Capitaliza corretamente cada palavra, tratando valores nulos."""
    if not text or text == SEM_INFO:
        return text
    return text.title()


def format_os_message(wo: WorkOrder, os_id: int) -> str:
    equipamento = format_title(wo.equipamento)
    setor = format_title(wo.setor)
    solicitante = format_title(wo.solicitante)
    executor = format_title(wo.executor)
    descricao = wo.descrição_do_problema
    tipo = format_title(wo.tipo_manutenção)
    status = format_title(wo.status)
    tempo = wo.tempo_gasto_minutos
    custo = wo.custo_peças
    solucao = wo.solução_aplicada

    msg = (
        f"🟢 OS REGISTRADA (PRÉ-ANÁLISE) #{os_id}\n\n"
        f"🔧 Equipamento: {equipamento}\n"
        f"📍 Setor: {setor}\n"
        f"📝 Solicitante: {solicitante}\n"
        f"👨‍🔧 Executor: {executor}\n"
        f"⚙️ Tipo de manutenção: {tipo}\n"
        f"📌 Status: {status}\n"
        f"⏱ Tempo gasto (min): {tempo}\n"
        f"💰 Custo de peças: {custo}\n"
        f"🚨 Problema detectado: {descricao}\n"
        f"🛠 Solução aplicada: {solucao}"
    )

    return msg
