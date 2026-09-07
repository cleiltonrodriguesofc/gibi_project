import pytest


def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Guardiões da Saúde" in response.text


@pytest.mark.parametrize("cap_id", [1, 2, 3, 4, 5, 6, 7, 8])
def test_read_capitulos(client, cap_id):
    response = client.get(f"/capitulo/{cap_id}")
    assert response.status_code == 200
    assert f"Capítulo {cap_id}" in response.text


def test_read_capitulo_not_found(client):
    response = client.get("/capitulo/999")
    assert response.status_code == 404


def test_read_mapa(client):
    response = client.get("/mapa")
    assert response.status_code == 200


def test_read_conquistas(client):
    response = client.get("/conquistas")
    assert response.status_code == 200
    assert "Minhas Conquistas" in response.text
