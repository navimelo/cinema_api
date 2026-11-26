from datetime import datetime, timedelta


def _cenario(client, duracao=100, classificacao="12"):
    """Cria gênero, filme, sala (2x3 = 6 assentos), cliente e uma sessão amanhã."""
    g = client.post("/generos", json={"nome": "Ação"}).json()
    f = client.post("/filmes", json={
        "titulo": "Filme Teste", "duracao_minutos": duracao,
        "classificacao_indicativa": classificacao, "generos_ids": [g["id"]],
    }).json()
    s = client.post("/salas", json={"nome": "Sala T", "tipo": "2D", "fileiras": 2, "assentos_por_fileira": 3}).json()
    c = client.post("/clientes", json={
        "nome": "Maria Teste", "email": "maria@teste.com", "data_nascimento": "1990-01-01",
    }).json()
    inicio = (datetime.now() + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
    ses = client.post("/sessoes", json={
        "filme_id": f["id"], "sala_id": s["id"], "inicio": inicio.isoformat(), "preco": 30,
    })
    assert ses.status_code == 201, ses.text
    return g, f, s, c, ses.json()


def test_assento_nao_pode_ser_vendido_duas_vezes_e_volta_apos_cancelamento(client):
    _, _, sala, cliente, sessao = _cenario(client)
    assentos = client.get(f"/salas/{sala['id']}/assentos").json()
    assert len(assentos) == 6
    a1 = assentos[0]["id"]

    r1 = client.post("/compras", json={"cliente_id": cliente["id"], "sessao_id": sessao["id"], "assentos_ids": [a1]})
    assert r1.status_code == 201, r1.text
    ingresso_id = r1.json()["ingressos"][0]["id"]

    r2 = client.post("/compras", json={"cliente_id": cliente["id"], "sessao_id": sessao["id"], "assentos_ids": [a1]})
    assert r2.status_code == 409

    mapa = client.get(f"/sessoes/{sessao['id']}/assentos").json()
    assert mapa["ocupados"] == 1 and mapa["disponiveis"] == 5

    assert client.post(f"/ingressos/{ingresso_id}/cancelar").status_code == 200
    r3 = client.post("/compras", json={"cliente_id": cliente["id"], "sessao_id": sessao["id"], "assentos_ids": [a1]})
    assert r3.status_code == 201


def test_compra_multipla_e_atomica(client):
    _, _, sala, cliente, sessao = _cenario(client)
    ids = [a["id"] for a in client.get(f"/salas/{sala['id']}/assentos").json()]
    client.post("/compras", json={"cliente_id": cliente["id"], "sessao_id": sessao["id"], "assentos_ids": [ids[1]]})
    r = client.post("/compras", json={"cliente_id": cliente["id"], "sessao_id": sessao["id"], "assentos_ids": [ids[0], ids[1]]})
    assert r.status_code == 409
    assert client.get(f"/sessoes/{sessao['id']}/assentos").json()["ocupados"] == 1  # nada foi gravado


def test_conflito_de_horario_na_mesma_sala(client):
    _, filme, sala, _, sessao = _cenario(client)
    inicio = datetime.fromisoformat(sessao["inicio"]) + timedelta(minutes=30)
    r = client.post("/sessoes", json={
        "filme_id": filme["id"], "sala_id": sala["id"], "inicio": inicio.isoformat(), "preco": 30,
    })
    assert r.status_code == 409


def test_classificacao_indicativa_bloqueia_menor(client):
    _, _, sala, _, sessao = _cenario(client, classificacao="18")
    menor = client.post("/clientes", json={
        "nome": "Menor", "email": "menor@teste.com",
        "data_nascimento": (datetime.now() - timedelta(days=365 * 15)).date().isoformat(),
    }).json()
    a = client.get(f"/salas/{sala['id']}/assentos").json()[0]["id"]
    r = client.post("/compras", json={"cliente_id": menor["id"], "sessao_id": sessao["id"], "assentos_ids": [a]})
    assert r.status_code == 422


def test_paginacao_e_filtros(client):
    for nome in ["Aaa", "Bbb", "Ccc"]:
        assert client.post("/generos", json={"nome": nome}).status_code == 201
    r = client.get("/generos", params={"limit": 2, "offset": 0}).json()
    assert r["total"] == 3 and len(r["itens"]) == 2 and r["total_paginas"] == 2
    r = client.get("/generos", params={"nome": "bb"}).json()
    assert r["total"] == 1 and r["itens"][0]["nome"] == "Bbb"


def test_erros_http(client):
    assert client.get("/filmes/999").status_code == 404
    assert client.get("/filmes/abc").status_code == 422
    assert client.get("/filmes/0").status_code == 422
    assert client.post("/generos", json={"nome": "X"}).status_code == 422
    client.post("/generos", json={"nome": "Drama"})
    assert client.post("/generos", json={"nome": "drama"}).status_code == 409


def test_exclusao_bloqueada_com_dependencias(client):
    g, filme, sala, cliente, sessao = _cenario(client)
    assert client.delete(f"/filmes/{filme['id']}").status_code == 409
    assert client.delete(f"/salas/{sala['id']}").status_code == 409
    assert client.delete(f"/generos/{g['id']}").status_code == 409


def test_estatisticas_e_consultas(client):
    _, filme, sala, cliente, sessao = _cenario(client)
    ids = [a["id"] for a in client.get(f"/salas/{sala['id']}/assentos").json()]
    client.post("/compras", json={"cliente_id": cliente["id"], "sessao_id": sessao["id"], "assentos_ids": ids[:2]})
    est = client.get("/estatisticas").json()
    assert est["ingressos_por_status"]["valido"] == 2 and est["receita_total"] == 60.0
    top = client.get("/consultas/filmes-mais-vistos").json()
    assert top[0]["ingressos_vendidos"] == 2
    ocup = client.get("/consultas/ocupacao-sessoes").json()
    assert ocup["itens"][0]["vendidos"] == 2
    hoje = datetime.now().date().isoformat()
    assert client.get("/consultas/vendas-por-dia", params={"inicio": hoje, "fim": hoje}).json()[0]["ingressos"] == 2
    assert client.get(f"/clientes/{cliente['id']}/ingressos").json()["total"] == 2
