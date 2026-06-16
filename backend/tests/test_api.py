import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

fd, path = tempfile.mkstemp(prefix='aion-test-', suffix='.db')
os.close(fd)
os.environ['AION_DB_PATH'] = path

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)


def test_health_contract():
    assert client.get('/health').json() == {'status': 'online', 'project': 'AION Agentes'}


def test_task_loop_report_logs_memory():
    created = client.post('/tasks', json={'description': 'Criar uma rotina de teste para o AION'}).json()
    task_id = created['id']
    result = client.post(f'/tasks/{task_id}/run')
    assert result.status_code == 200
    payload = result.json()
    assert payload['task']['status'] == 'completed'
    assert payload['steps']
    assert 'Relatório AION Agentes' in payload['report']
    assert client.get(f'/tasks/{task_id}').status_code == 200
    assert client.get(f'/tasks/{task_id}/report').status_code == 200
    assert client.get('/logs').json()
    assert client.get('/memory').json()


def test_not_found_contracts():
    assert client.get('/tasks/999999').status_code == 404
    assert client.post('/tasks/999999/run').status_code == 404
