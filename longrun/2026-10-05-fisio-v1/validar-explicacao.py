"""Validação local complementar: executa somente contra o servidor falso."""
import pathlib
import sys
import tempfile
import shutil

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'tests'))
from conftest import Servidor, Externo, FIXTURE, env_integracoes

with tempfile.TemporaryDirectory() as tmp:
    pasta = pathlib.Path(tmp)
    shutil.copy(FIXTURE, pasta / 'clinica.json')
    (pasta / 'ponte.mp4').write_bytes(b'video-local')
    externo = Externo()
    servidor = Servidor(pasta, env=env_integracoes(externo, EXERCICIOS_MP4_DIR=str(pasta)))
    try:
        api = servidor.subir()
        tel = '41987654321'
        pid = api.paciente('Teste local', tel)
        api.prescricao(pid)
        externo.falhas = 1
        texto = api.msg(tel, 'ponte')
        assert api.saida('explicacao')[-1]['status'] == 'pendente'
        servidor.parar()
        api = servidor.subir()
        assert api.rodar()['reenviadas'] == 1
        assert len(externo.media()) == 1
        assert externo.media()[0]['json']['caption'] == texto
        historico = api.get(f'/api/pacientes/{pid}/dados')[1]['mensagens']
        assert sum(m['direcao'] == 'saida' and m['texto'] == texto for m in historico) == 1
        api.msg(tel, '7')
        assert api.get(f'/api/pacientes/{pid}/adesao')[1]['registros'] == []
        # Um termo maior não prescrito vence um nome menor prescrito.
        assert api.post('/api/exercicios', {'id': 'ponte-longa', 'nome': 'Ponte longa',
            'regiao': 'teste', 'passos': ['Passo reservado.']})[0] == 201
        assert 'Fale com seu fisioterapeuta' in api.msg(tel, 'ponte longa')
        # Em empate, mantém o primeiro exercício na ordem do catálogo.
        api.put('/api/exercicios/ponte-longa', {'apelidos': ['ponte']})
        assert '1. Deite' in api.msg(tel, 'ponte')
        # Exercício desativado não é explicado nem listado.
        api.delete('/api/exercicios/retracao-cervical')
        assert 'Retração cervical' not in api.msg(tel, 'exercícios')
        api.put(f'/api/pacientes/{pid}', {'nao_contatar': True})
        antes = len(api.saida('explicacao'))
        api.msg(tel, 'ponte')
        assert len(api.saida('explicacao')) == antes
        print('EXPLICACAO OK: reenvio após reinício, histórico único, pendência, prioridade de termos, inativo e opt-out')
    finally:
        servidor.parar()
        externo.fechar()
