"""Planos de tratamento e alertas derivados da agenda persistida."""
from datetime import datetime, timedelta

from .core import Erro, agora
from . import integracoes


def iniciar(c):
    c.db.executescript('''
        CREATE TABLE IF NOT EXISTS planos (
            id INTEGER PRIMARY KEY, paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            servico TEXT NOT NULL, servico_avaliacao TEXT, profissional TEXT,
            sessoes_previstas INTEGER NOT NULL, frequencia_semanal INTEGER NOT NULL,
            observacao TEXT, criado_em TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ativo',
            alerta_abandono TEXT, alerta_reavaliacao TEXT, motivo_encerramento TEXT,
            abandono_ultima_sessao TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS plano_ativo_unico
            ON planos(paciente_id,servico) WHERE status='ativo';
        CREATE TABLE IF NOT EXISTS alertas (
            id INTEGER PRIMARY KEY, tipo TEXT NOT NULL,
            paciente_id INTEGER NOT NULL REFERENCES pacientes(id),
            plano_id INTEGER NOT NULL REFERENCES planos(id), texto TEXT NOT NULL,
            quando TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'aberto');
    ''')


def obter(c, ident):
    r = c.db.execute('SELECT * FROM planos WHERE id=?', (ident,)).fetchone()
    if r is None:
        raise Erro(404, 'Plano inexistente')
    p = dict(r)
    p.pop('motivo_encerramento')
    p.pop('abandono_ultima_sessao')
    sessoes = c.db.execute('SELECT inicio,status FROM agendamentos WHERE plano_id=? ORDER BY inicio,id', (ident,)).fetchall()
    realizadas = [a['inicio'] for a in sessoes if a['status'] == 'realizado']
    ultima = max(realizadas) if realizadas else None
    p.update(realizadas=len(realizadas), faltas=sum(a['status'] == 'falta' for a in sessoes),
             faltas_seguidas=sum(a['status'] == 'falta' and (ultima is None or a['inicio'] > ultima) for a in sessoes),
             restantes=max(0, p['sessoes_previstas'] - len(realizadas)), ultima_sessao=ultima)
    return p


def listar(c, paciente_id=None):
    return [obter(c, r['id']) for r in c.db.execute(
        'SELECT id FROM planos WHERE (? IS NULL OR paciente_id=?) ORDER BY id', (paciente_id, paciente_id)).fetchall()]


def criar(c, b):
    c.paciente(b.get('paciente_id'))
    c.servico(b.get('servico'))
    profissional = b.get('profissional')
    if profissional is not None and not any(p['id'] == profissional for p in c.catalogo('profissionais')):
        raise Erro(404, 'Profissional inexistente')
    for campo in ('sessoes_previstas', 'frequencia_semanal'):
        if type(b.get(campo)) is not int or b[campo] < 1:
            raise Erro(422, 'Quantidade deve ser inteiro positivo')
    avaliacao = b.get('servico_avaliacao', 'avaliacao' if any(s['id'] == 'avaliacao' for s in c.catalogo('servicos')) else None)
    if avaliacao is not None:
        c.servico(avaliacao)
    if c.db.execute("SELECT 1 FROM planos WHERE paciente_id=? AND servico=? AND status='ativo'", (b['paciente_id'], b['servico'])).fetchone():
        raise Erro(409, 'Já existe plano ativo para este serviço')
    ident = c.db.execute('''INSERT INTO planos(paciente_id,servico,servico_avaliacao,profissional,
        sessoes_previstas,frequencia_semanal,observacao,criado_em) VALUES (?,?,?,?,?,?,?,?)''',
        (b['paciente_id'], b['servico'], avaliacao, profissional, b['sessoes_previstas'],
         b['frequencia_semanal'], b.get('observacao'), agora().isoformat(timespec='minutes'))).lastrowid
    return obter(c, ident)


def vinculo(c, b):
    ident = b.get('plano_id')
    if ident is None:
        r = c.db.execute("SELECT id FROM planos WHERE paciente_id=? AND servico=? AND status='ativo'",
                         (b['paciente_id'], b['servico'])).fetchone()
        return r['id'] if r else None
    p = obter(c, ident)
    if p['status'] != 'ativo' or p['paciente_id'] != b['paciente_id'] or p['servico'] != b['servico']:
        raise Erro(422, 'Plano incompatível com o agendamento')
    return ident


def encerrar(c, ident, motivo):
    p = obter(c, ident)
    if p['status'] != 'ativo':
        raise Erro(409, 'Plano não está ativo')
    if not isinstance(motivo, str) or not motivo.strip():
        raise Erro(422, 'Motivo obrigatório')
    c.db.execute("UPDATE planos SET status='encerrado',motivo_encerramento=? WHERE id=?", (motivo, ident))
    return obter(c, ident)


def atualizar_presenca(c, ident):
    if ident is None:
        return
    p = obter(c, ident)
    if p['status'] == 'ativo' and p['realizadas'] >= p['sessoes_previstas']:
        c.db.execute("UPDATE planos SET status='concluido' WHERE id=?", (ident,))
        if p['servico_avaliacao'] is not None:
            ultima = c.db.execute("SELECT id FROM agendamentos WHERE plano_id=? AND status='realizado' ORDER BY inicio DESC,id DESC LIMIT 1", (ident,)).fetchone()
            data = (datetime.fromisoformat(p['ultima_sessao']) + timedelta(days=c.cfg['reavaliacao_dias'])).date().isoformat()
            c.db.execute('INSERT INTO retornos(agendamento_id,paciente_id,servico,data) VALUES (?,?,?,?)',
                         (ultima['id'], p['paciente_id'], p['servico_avaliacao'], data))


def listar_alertas(c):
    return [dict(r) for r in c.db.execute("""SELECT a.*,p.nome FROM alertas a JOIN pacientes p
        ON p.id=a.paciente_id WHERE a.status='aberto' ORDER BY a.id""")]


def resolver(c, ident):
    if not c.db.execute('SELECT 1 FROM alertas WHERE id=?', (ident,)).fetchone():
        raise Erro(404, 'Alerta inexistente')
    c.db.execute("UPDATE alertas SET status='resolvido' WHERE id=?", (ident,))
    return {'status': 'resolvido'}


def rodar_alertas(c, t):
    quantidade = 0
    quando = t.isoformat(timespec='minutes')
    for p in listar(c):
        if p['status'] != 'ativo':
            continue
        nome = c.paciente(p['paciente_id'])['nome']
        servico = c.servico(p['servico'])['nome']
        marcador = c.db.execute('SELECT abandono_ultima_sessao FROM planos WHERE id=?', (p['id'],)).fetchone()[0]
        # O relógio da rodada pode preceder presenças futuras já registradas.
        # A identidade da sequência impede alertar de novo no mesmo instante.
        abandono = (p['faltas_seguidas'] >= c.cfg['abandono_faltas'] and
                    (p['alerta_abandono'] is None or
                     (p['ultima_sessao'] is not None and p['alerta_abandono'] < p['ultima_sessao'] and marcador != p['ultima_sessao'])))
        regras = [('abandono', abandono, f"{nome}: {p['faltas_seguidas']} faltas seguidas no plano de {servico}"),
                  ('reavaliacao', p['restantes'] <= c.cfg['reavaliacao_sessoes'] and p['alerta_reavaliacao'] is None,
                   f"{nome}: faltam {p['restantes']} sessões do plano de {servico} — agendar reavaliação")]
        for tipo, devido, texto in regras:
            if not devido:
                continue
            ident = c.db.execute('INSERT INTO alertas(tipo,paciente_id,plano_id,texto,quando) VALUES (?,?,?,?,?)',
                                 (tipo, p['paciente_id'], p['id'], texto, quando)).lastrowid
            c.db.execute(f'UPDATE planos SET alerta_{tipo}=? WHERE id=?', (quando, p['id']))
            if tipo == 'abandono':
                c.db.execute('UPDATE planos SET abandono_ultima_sessao=? WHERE id=?', (p['ultima_sessao'], p['id']))
            integracoes.telegram(c, f"Alerta {tipo} #{ident}: {nome} — {texto}")
            quantidade += 1
    return quantidade
