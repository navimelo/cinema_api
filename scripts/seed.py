"""F16 — Povoamento inicial. Uso:  python -m scripts.seed"""
import random
from datetime import date, datetime, time, timedelta, timezone

from sqlmodel import Session, select

from app.crud import cliente as cliente_crud
from app.crud import filme as filme_crud
from app.crud import genero as genero_crud
from app.crud import sala as sala_crud
from app.database import engine
from app.exceptions import AppError
from app.models import Assento, Compra, Filme, Ingresso, Sessao, Validacao
from app.models.constantes import StatusIngresso
from app.schemas.cliente import ClienteCreate
from app.schemas.compra import CompraCreate
from app.schemas.filme import FilmeCreate
from app.schemas.genero import GeneroCreate
from app.schemas.sala import SalaCreate
from app.schemas.sessao import SessaoCreate
from app.schemas.validacao import ValidacaoCreate
from app.services import sessao_service, venda_service
from app.services.sessao_service import calcular_fim

GENEROS = ["Ação", "Aventura", "Animação", "Comédia", "Drama", "Ficção Científica", "Terror", "Romance", "Suspense"]

# (título, duração, classificação, gêneros, sinopse)
FILMES = [
    ("Horizonte Perdido", 128, "12", ["Aventura", "Ação"], "Uma expedição busca uma cidade esquecida."),
    ("Noite Sem Fim", 104, "16", ["Terror", "Suspense"], "Um plantão noturno que não termina."),
    ("Amor em Quixadá", 96, "L", ["Romance", "Comédia"], "Um romance entre os monólitos do sertão."),
    ("Galáxia Zero", 142, "12", ["Ficção Científica", "Aventura"], "A última nave rumo ao desconhecido."),
    ("O Pequeno Dragão", 88, "L", ["Animação", "Aventura"], "Um dragão aprende a voar."),
    ("Código Vermelho", 115, "14", ["Ação", "Suspense"], "Uma agente contra o relógio."),
    ("Sombras do Passado", 133, "16", ["Drama", "Suspense"], "Segredos de família vêm à tona."),
    ("Riso Solto", 99, "10", ["Comédia"], "Três amigos e uma viagem desastrada."),
    ("A Última Sessão", 110, "14", ["Drama", "Romance"], "O fim de um cinema de rua."),
    ("Mundo Brinquedo", 92, "L", ["Animação", "Comédia"], "Os brinquedos ganham vida à noite."),
    ("Colapso", 121, "18", ["Ação", "Ficção Científica"], "A cidade em colapso, sem regras."),
    ("Entre Marés", 107, "12", ["Drama", "Aventura"], "Pescadores enfrentam a maior tempestade."),
]

# (nome, tipo, fileiras, assentos por fileira, preço)
SALAS = [
    ("Sala 1", "2D", 4, 5, 28.0),     # 20 lugares (sala pequena)
    ("Sala 2", "3D", 6, 8, 36.0),     # 48 lugares
    ("Sala 3", "IMAX", 8, 10, 48.0),  # 80 lugares
    ("Sala VIP", "VIP", 3, 6, 60.0),  # 18 lugares
]

CLIENTES = [
    ("Ana Beatriz Lima", "ana.lima@email.com", "11111111111", date(1995, 3, 14)),
    ("Bruno Carvalho", "bruno.carvalho@email.com", "22222222222", date(1988, 7, 2)),
    ("Camila Souza", "camila.souza@email.com", "33333333333", date(2001, 11, 25)),
    ("Daniel Pereira", "daniel.pereira@email.com", "44444444444", date(1979, 1, 30)),
    ("Eduarda Nunes", "eduarda.nunes@email.com", "55555555555", date(1999, 5, 9)),
    ("Felipe Araújo", "felipe.araujo@email.com", "66666666666", date(1993, 9, 18)),
    ("Gabriela Rocha", "gabriela.rocha@email.com", "77777777777", date(1985, 12, 3)),
    ("Henrique Alves", "henrique.alves@email.com", "88888888888", date(2003, 2, 21)),
    ("Isabela Martins", "isabela.martins@email.com", "99999999999", date(1997, 6, 6)),
    ("João Pedro Gomes", "joao.gomes@email.com", None, date(1990, 8, 27)),
    ("Karina Freitas", "karina.freitas@email.com", None, date(1982, 4, 11)),
    # Menor de idade: permite demonstrar a regra de classificação indicativa.
    ("Lucas Menor", "lucas.menor@email.com", None, date(date.today().year - 13, 1, 15)),
]


def povoar(session: Session) -> None:
    if session.exec(select(Filme.id).limit(1)).first() is not None:
        print("Banco já possui dados; povoamento ignorado.")
        return

    print("Criando gêneros, filmes, salas e clientes...")
    generos = {nome: genero_crud.criar(session, GeneroCreate(nome=nome)) for nome in GENEROS}
    filmes = [
        filme_crud.criar(
            session,
            FilmeCreate(
                titulo=t, duracao_minutos=d, classificacao_indicativa=c, sinopse=s,
                data_estreia=date.today() - timedelta(days=10), em_cartaz=True,
                generos_ids=[generos[g].id for g in gs],
            ),
        )
        for t, d, c, gs, s in FILMES
    ]
    salas = [
        sala_crud.criar(session, SalaCreate(nome=n, tipo=t, fileiras=f, assentos_por_fileira=a))
        for n, t, f, a, _ in SALAS
    ]
    precos = {n: p for n, _, _, _, p in SALAS}
    clientes = [
        cliente_crud.criar(
            session, ClienteCreate(nome=n, email=e, cpf=c, data_nascimento=nasc, telefone="(88) 99999-0000")
        )
        for n, e, c, nasc in CLIENTES
    ]

    print("Programando sessões (7 dias x 4 salas x 3 sessões)...")
    amanha = date.today() + timedelta(days=1)
    sessoes: list[Sessao] = []
    for dia in range(7):
        for idx_sala, sala in enumerate(salas):
            cursor = datetime.combine(
             amanha + timedelta(days=dia),
             time(10, 0),
             tzinfo=timezone.utc
    )
            for k in range(3):
                filme = filmes[(dia + idx_sala * 3 + k) % len(filmes)]
                sessao = sessao_service.criar_sessao(
                    session, SessaoCreate(filme_id=filme.id, sala_id=sala.id, inicio=cursor, preco=precos[sala.nome])
                )
                sessoes.append(sessao)
                cursor = sessao.fim + timedelta(minutes=10)

    print("Vendendo ingressos...")
    rng = random.Random(7)
    ingressos_para_cancelar = []
    for sessao in sessoes[:40]:
        for _ in range(rng.randint(1, 4)):
            cliente = rng.choice(clientes)
            qtd = rng.randint(1, 4)
            livres = [a for a in sessao_service.mapa_assentos(session, sessao.id, True).assentos]
            if len(livres) < qtd:
                continue
            inicio = rng.randrange(0, len(livres) - qtd + 1)
            ids = [a.id for a in livres[inicio:inicio + qtd]]
            try:
                compra = venda_service.comprar_ingressos(
                    session, CompraCreate(cliente_id=cliente.id, sessao_id=sessao.id, assentos_ids=ids)
                )
                if len(ingressos_para_cancelar) < 3:
                    ingressos_para_cancelar.append(compra.ingressos[0].id)
            except AppError:  # ex.: menor de idade em filme 16/18
                session.rollback()

    print("Cancelando alguns ingressos (assento volta a ficar disponível)...")
    for ingresso_id in ingressos_para_cancelar:
        venda_service.cancelar_ingresso(session, ingresso_id)

    print("Criando uma sessão de ontem com ingressos já validados (histórico)...")
    ontem = datetime.combine(
        date.today() - timedelta(days=1),
        time(20, 0),
        tzinfo=timezone.utc
    )
    filme_ontem, sala_ontem = filmes[0], salas[1]
    passada = Sessao(
        filme_id=filme_ontem.id, sala_id=sala_ontem.id, inicio=ontem,
        fim=calcular_fim(filme_ontem, ontem), preco=precos[sala_ontem.nome],
    )
    session.add(passada)
    session.flush()
    assentos = session.exec(
        select(Assento).where(Assento.sala_id == sala_ontem.id).order_by(Assento.fileira, Assento.numero).limit(3)
    ).all()
    compra = Compra(cliente_id=clientes[0].id, data_compra=ontem - timedelta(days=1),
                    valor_total=round(passada.preco * len(assentos), 2))
    compra.ingressos = [
        Ingresso(sessao_id=passada.id, assento_id=a.id, valor=passada.preco,
                 status=StatusIngresso.UTILIZADO, criado_em=ontem - timedelta(days=1))
        for a in assentos
    ]
    session.add(compra)
    session.flush()
    for ingresso in compra.ingressos:
        session.add(Validacao(ingresso_id=ingresso.id, operador="Funcionário Seed", validado_em=ontem - timedelta(minutes=10)))
    session.commit()

    print(
        f"Povoamento concluído: {len(GENEROS)} gêneros, {len(filmes)} filmes, {len(salas)} salas, "
        f"{len(clientes)} clientes, {len(sessoes) + 1} sessões."
    )


if __name__ == "__main__":
    with Session(engine) as sessao_db:
        povoar(sessao_db)
