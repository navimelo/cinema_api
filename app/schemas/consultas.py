from datetime import datetime

from pydantic import BaseModel


class FilmePublico(BaseModel):
    filme_id: int
    titulo: str
    ingressos_vendidos: int
    receita: float


class OcupacaoSessao(BaseModel):
    sessao_id: int
    filme: str
    sala: str
    inicio: datetime
    capacidade: int
    vendidos: int
    disponiveis: int
    ocupacao_percentual: float


class VendasDia(BaseModel):
    dia: str
    ingressos: int
    receita: float


class ContagemItem(BaseModel):
    rotulo: str
    quantidade: int


class Estatisticas(BaseModel):
    total_filmes: int
    total_salas: int
    total_sessoes: int
    total_clientes: int
    total_compras: int
    ingressos_por_status: dict[str, int]
    receita_total: float
    ticket_medio: float
    ocupacao_media_percentual: float
    ingressos_por_sala: list[ContagemItem]
    ingressos_por_classificacao: list[ContagemItem]
    filmes_por_genero: list[ContagemItem]
    filmes_mais_vistos: list[FilmePublico]
