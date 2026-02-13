from openai import OpenAI

# Prompt do sistema (corrigido e seguro usando triple quotes)
SYSTEM_PROMPT = """
Você é um assistente de PCM especializado em manutenção industrial.
Sua tarefa é receber uma informação e extrair os dados em formato JSON.

Use estes campos:
- equipamento
- setor
- solicitante
- executor
- descrição_do_problema
- tipo_manutenção
- status
- tempo_gasto_minutos
- custo_peças
- solução_aplicada

Regras:
1) Qualquer campo que não for mencionado deve ser preenchido com o texto: "SEM INFORMAÇÃO".
2) Se o usuário mencionar tempo em horas, converta para minutos.
   Exemplo: "1,5 horas" -> 90 minutos; "2h" -> 120; "1 hora e 30" -> 90.
3) tempo_gasto_minutos deve ser um número inteiro (minutos) ou "SEM INFORMAÇÃO".
4) custo_peças deve ser um número (float) ou "SEM INFORMAÇÃO".
5) Responda SOMENTE com JSON válido, sem markdown, sem explicações.
""".strip()


def extrair_os(openai_client: OpenAI, texto: str) -> str:
    user_prompt = f"""
Texto do técnico:
{texto}

Instruções de preenchimento:
- equipamento: Nome/TAG literal (ex: "Bomba 14", "Misturador 5").
- setor: Localização/linha/setor.
- solicitante: Quem abriu/solicitou a OS.
- executor: Quem executou o serviço.
- descrição_do_problema: Defeito/sintoma relatado.
- tipo_manutenção: Preventiva, Corretiva, Preditiva, etc.
- status: Aberto, Em andamento, Concluído, Terceiro, Compras, etc.
- tempo_gasto_minutos: apenas número inteiro em minutos, ou "SEM INFORMAÇÃO".
- custo_peças: apenas número (float), ou "SEM INFORMAÇÃO".
- solução_aplicada: Descrição técnica da ação tomada.

Retorne JSON com EXATAMENTE estas chaves:
equipamento, setor, solicitante, executor, descrição_do_problema, tipo_manutenção, status, tempo_gasto_minutos, custo_peças, solução_aplicada
""".strip()

    resp = openai_client.chat.completions.create(
        model="o4-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    # Retorna a string JSON (para o app.py fazer json.loads e formatar)
    return resp.choices[0].message.content
