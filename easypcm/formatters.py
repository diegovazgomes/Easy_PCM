from .schemas import WorkOrder, SEM_INFO

def format_os_message(wo: WorkOrder, os_id: int) -> str:
    equipamento = wo.equipamento
    setor = wo.setor
    solicitante = wo.solicitante
    executor = wo.executor
    descricao = wo.descrição_do_problema
    tipo = wo.tipo_manutenção
    status = wo.status
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
        f"🚨 Problema detectado:{descricao}\n"
        f"🛠 Solução aplicada:{solucao}"
    )
    return msg
