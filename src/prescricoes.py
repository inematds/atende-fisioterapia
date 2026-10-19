"""Prescrições domiciliares, preferências e registros diários persistentes."""
import json
import os
import re
from datetime import date, timedelta

from .core import Erro, agora

DIAS = ('seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom')


def iniciar(c):
    colunas = {r[1] for r in c.db.execute('PRAGMA table_info(pacientes)')}
    if 'lembrete_hora' not in colunas:
        c.db.execute('ALTER TABLE pacientes ADD COLUMN lembrete_hora TEXT')
        c.db.execute('ALTER TABLE pacientes ADD COLUMN lembrete_ativo INTEGER NOT NULL DEFAULT 0')
        c.db.execute('UPDATE pacientes SET lembrete_hora=?', (c.cfg['lembrete_hora_padrao'],))
    c.db.executescript('''
        CREATE TABLE IF NOT EXISTS prescricoes (
            id INTEGER PRIMARY KEY, paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            criado_em TEXT NOT NULL, inicio TEXT NOT NULL, itens TEXT NOT NULL, ativo INTEGER NOT NULL);
        CREATE UNIQUE INDEX IF NOT EXISTS prescricao_ativa ON prescricoes(paciente_id) WHERE ativo=1;
        CREATE TABLE IF NOT EXISTS registros (
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id), data TEXT NOT NULL,
            fez INTEGER, dor INTEGER, quando TEXT NOT NULL, PRIMARY KEY(paciente_id,data));
    ''')


def hora(valor):
    if not isinstance(valor, str) or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', valor):
        raise Erro(422, 'Hora do lembrete inválida')
    return valor


def preferencias(c, pid, b):
    c.paciente(pid)
    if 'lembrete_hora' in b:
        hora(b['lembrete_hora'])
    if 'lembrete_ativo' in b and type(b['lembrete_ativo']) is not bool:
        raise Erro(422, 'lembrete_ativo deve ser booleano')
    for campo in ('lembrete_hora', 'lembrete_ativo'):
        if campo in b:
            c.db.execute(f'UPDATE pacientes SET {campo}=? WHERE id=?', (b[campo], pid))
    p = c.paciente(pid)
    return {k: p[k] for k in ('lembrete_hora', 'lembrete_ativo')}


def obter(c, pid):
    p = c.paciente(pid)
    r = c.db.execute('SELECT * FROM prescricoes WHERE paciente_id=? AND ativo=1', (pid,)).fetchone()
    if not r:
        return None
    return {**dict(r), 'itens': json.loads(r['itens']), 'ativo': True,
            'lembrete_hora': p['lembrete_hora'], 'lembrete_ativo': p['lembrete_ativo']}


def link(ident):
    return os.environ.get('PUBLIC_URL', '').rstrip('/') + '/exercicios/' + ident


def linha(item):
    return f"- {item['nome']}: {item['series']} x {item['repeticoes']}, {item['vezes_dia']}x ao dia"


def criar(c, pid, b):
    from .conversa import enviar
    c.paciente(pid)
    itens = b.get('itens')
    if not isinstance(itens, list) or not itens:
        raise Erro(422, 'Informe itens da prescrição')
    catalogo = {e['id']: e for e in c.catalogo('exercicios')}
    novos = []
    for item in itens:
        if not isinstance(item, dict):
            raise Erro(422, 'Item inválido')
        ident = item.get('exercicio')
        e = catalogo.get(ident) if isinstance(ident, str) else None
        dias = item.get('dias')
        if (not e or not e.get('ativo', True) or
                any(type(item.get(k)) is not int or item[k] < 1 for k in ('series', 'repeticoes', 'vezes_dia')) or
                not isinstance(dias, list) or not dias or any(d not in DIAS for d in dias) or
                not isinstance(item.get('observacao', ''), str)):
            raise Erro(422, 'Item inválido')
        novos.append({k: item[k] for k in ('exercicio', 'series', 'repeticoes', 'vezes_dia', 'dias')})
        novos[-1].update(nome=e['nome'], observacao=item.get('observacao', ''))
    if 'lembrete_hora' in b:
        preferencias(c, pid, {'lembrete_hora': b['lembrete_hora']})
    c.db.execute('UPDATE prescricoes SET ativo=0 WHERE paciente_id=?', (pid,))
    t = agora().isoformat(timespec='minutes')
    c.db.execute('INSERT INTO prescricoes(paciente_id,criado_em,inicio,itens,ativo) VALUES (?,?,?,?,1)',
                 (pid, t, t[:10], json.dumps(novos, ensure_ascii=False)))
    texto = '\n'.join(linha(i) + ' (' + ', '.join(i['dias']) + ')\n' + link(i['exercicio']) for i in novos)
    enviar(c, pid, 'prescricao', texto + '\nPara receber lembrete diário, responda LEMBRETE e a hora (ex.: LEMBRETE 19:00).')
    return obter(c, pid)


def remover(c, pid):
    c.paciente(pid)
    c.db.execute('UPDATE prescricoes SET ativo=0 WHERE paciente_id=?', (pid,))
    preferencias(c, pid, {'lembrete_ativo': False})


def rodar(c, t):
    from .conversa import enviar
    total = 0
    for row in c.db.execute('SELECT paciente_id FROM prescricoes WHERE ativo=1 ORDER BY paciente_id').fetchall():
        pid = row[0]
        p = obter(c, pid)
        if not p['lembrete_ativo'] or t.strftime('%H:%M') < p['lembrete_hora']:
            continue
        itens = [i for i in p['itens'] if DIAS[t.weekday()] in i['dias']]
        if not itens or c.db.execute("SELECT 1 FROM saida WHERE paciente_id=? AND tipo='exercicio' AND substr(quando,1,10)=?", (pid, t.date().isoformat())).fetchone():
            continue
        texto = '\n'.join(linha(i) + (' — ' + i['observacao'] if i['observacao'] else '') for i in itens)
        total += enviar(c, pid, 'exercicio', texto + '\nResponda FIZ, NÃO FIZ ou a dor de 0 a 10.', quando=t)
    return total


def registros(c, pid):
    return [{**dict(r), 'fez': None if r['fez'] is None else bool(r['fez'])} for r in c.db.execute(
        'SELECT data,fez,dor,quando FROM registros WHERE paciente_id=? ORDER BY data', (pid,))]


def registrar(c, p, original, fez=None, dor=None):
    from .conversa import abrir_humano
    t = agora().isoformat(timespec='minutes')
    c.db.execute('''INSERT INTO registros VALUES (?,?,?,?,?) ON CONFLICT(paciente_id,data)
        DO UPDATE SET fez=coalesce(excluded.fez,registros.fez), dor=coalesce(excluded.dor,registros.dor), quando=excluded.quando''',
        (p['id'], t[:10], fez, dor, t))
    resposta = 'Registrado.'
    if dor is not None and dor >= c.cfg['dor_alerta']:
        abrir_humano(c, p['telefone'], f'dor {dor}', 'alta', original)
        resposta += ' Seu fisioterapeuta foi avisado. Em emergência, ligue 192.'
    return resposta


def conversar(c, p, original, t, pendente):
    from .conversa import contem
    if not p:
        return None
    if pendente and pendente['tipo'] == 'exercicio' and re.fullmatch(r'(?:[0-9]|10)', t):
        respondida = c.db.execute('SELECT 1 FROM registros WHERE paciente_id=? AND data=? AND dor IS NOT NULL',
                                 (p['id'], pendente['quando'][:10])).fetchone()
        if not respondida:
            return registrar(c, p, original, dor=int(t))
    prescricao = obter(c, p['id'])
    if prescricao and contem(t, 'lembrete'):
        if contem(t, 'sem lembrete'):
            preferencias(c, p['id'], {'lembrete_ativo': False})
            return 'Lembrete desligado.'
        m = re.search(r'\d{1,2}:\d{2}', original)
        valor = m[0].zfill(5) if m else c.cfg['lembrete_hora_padrao']
        try:
            preferencias(c, p['id'], {'lembrete_ativo': True, 'lembrete_hora': valor})
        except Erro:
            return 'Hora inválida para o lembrete.'
        return f'Lembrete ligado às {valor}.'
    fez = None
    if prescricao:
        if contem(t, 'nao fiz') or contem(t, 'nao consegui'):
            fez = False
        elif contem(t, 'fiz'):
            fez = True
    m = re.search(r'(?<!\w)dor (10|[0-9])(?!\w)', t)
    dor = int(m[1]) if m else None
    if fez is not None or dor is not None:
        return registrar(c, p, original, fez, dor)
    return None


def adesao(c, pid, semanas=4):
    c.paciente(pid)
    try:
        n = int(semanas)
        if n < 1:
            raise ValueError()
    except (ValueError, TypeError):
        raise Erro(422, 'Número de semanas inválido')
    regs = registros(c, pid)
    p = obter(c, pid)
    resultado = []
    if p:
        hoje = agora().date()
        inicio = date.fromisoformat(p['inicio'])
        segunda = hoje - timedelta(days=hoje.weekday())
        primeira = inicio - timedelta(days=inicio.weekday())
        disponiveis = max(0, (segunda - primeira).days // 7)
        semana = max(primeira, segunda - timedelta(weeks=min(n - 1, disponiveis)))
        dias = {d for i in p['itens'] for d in i['dias']}
        por_data = {r['data']: r for r in regs}
        while semana <= segunda:
            previstos = [semana + timedelta(days=d) for d in range(7)
                         if DIAS[d] in dias and inicio <= semana + timedelta(days=d) <= hoje]
            feitos = sum(por_data.get(d.isoformat(), {}).get('fez') is True for d in previstos)
            dores = [r['dor'] for r in regs if r['dor'] is not None and semana.isoformat() <= r['data'] <= (semana + timedelta(days=6)).isoformat()]
            resultado.append({'inicio': semana.isoformat(), 'previstos': len(previstos), 'feitos': feitos,
                              'adesao_pct': round(feitos / len(previstos) * 100, 1) if previstos else 0.0,
                              'dor_media': round(sum(dores) / len(dores), 1) if dores else None})
            semana += timedelta(weeks=1)
    return {'semanas': resultado, 'registros': regs}


def geral(c):
    resultado = []
    for row in c.db.execute('SELECT paciente_id FROM prescricoes WHERE ativo=1 ORDER BY paciente_id'):
        pid = row[0]
        dados = adesao(c, pid, 1)
        semana = dados['semanas'][-1] if dados['semanas'] else {'adesao_pct': 0.0, 'dor_media': None}
        dores = [r['dor'] for r in dados['registros'] if r['dor'] is not None]
        resultado.append({'paciente_id': pid, 'nome': c.paciente(pid)['nome'],
                          'adesao_pct': semana['adesao_pct'], 'dor_media': semana['dor_media'],
                          'ultima_dor': dores[-1] if dores else None})
    return resultado
