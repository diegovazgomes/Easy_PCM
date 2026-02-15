from pydantic import BaseModel, Field
from typing import Union


SEM_INFO = "SEM INFORMAÇÃO"


def _norm_str(v) -> str:
    if v is None:
        return SEM_INFO
    s = str(v).strip()
    return s if s else SEM_INFO


class WorkOrder(BaseModel):
    equipamento: str = Field(default=SEM_INFO)
    setor: str = Field(default=SEM_INFO)
    solicitante: str = Field(default=SEM_INFO)
    executor: str = Field(default=SEM_INFO)
    descrição_do_problema: str = Field(default=SEM_INFO)
    tipo_manutenção: str = Field(default=SEM_INFO)
    status: str = Field(default=SEM_INFO)

    # Aceita int ou "SEM INFORMAÇÃO"
    tempo_gasto_minutos: Union[int, str] = Field(default=SEM_INFO)

    # Aceita float ou "SEM INFORMAÇÃO"
    custo_peças: Union[float, str] = Field(default=SEM_INFO)

    solução_aplicada: str = Field(default=SEM_INFO)

    @classmethod
    def from_ai_dict(cls, d: dict) -> "WorkOrder":
        """
        Normaliza dados vindos da IA para evitar None, string vazia,
        e garantir int/float quando aplicável.
        """
        data = {k: d.get(k) for k in [
            "equipamento", "setor", "solicitante", "executor",
            "descrição_do_problema", "tipo_manutenção", "status",
            "tempo_gasto_minutos", "custo_peças", "solução_aplicada"
        ]}

        # Normaliza strings
        for k in [
            "equipamento", "setor", "solicitante", "executor",
            "descrição_do_problema", "tipo_manutenção", "status",
            "solução_aplicada"
        ]:
            data[k] = _norm_str(data.get(k))

        # Normaliza tempo
        t = data.get("tempo_gasto_minutos")
        if isinstance(t, str):
            t = t.strip()
            if t == "" or t.upper() == SEM_INFO:
                data["tempo_gasto_minutos"] = SEM_INFO
            else:
                # tenta converter string numérica
                try:
                    data["tempo_gasto_minutos"] = int(float(t.replace(",", ".")))
                except Exception:
                    data["tempo_gasto_minutos"] = SEM_INFO
        elif isinstance(t, (int, float)):
            data["tempo_gasto_minutos"] = int(t)
        else:
            data["tempo_gasto_minutos"] = SEM_INFO

        # Normaliza custo
        c = data.get("custo_peças")
        if isinstance(c, str):
            c = c.strip()
            if c == "" or c.upper() == SEM_INFO:
                data["custo_peças"] = SEM_INFO
            else:
                try:
                    data["custo_peças"] = float(c.replace(",", "."))
                except Exception:
                    data["custo_peças"] = SEM_INFO
        elif isinstance(c, (int, float)):
            data["custo_peças"] = float(c)
        else:
            data["custo_peças"] = SEM_INFO

        return cls(**data)
