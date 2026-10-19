"""Biblioteca pública de exercícios; edição somente pelas rotas autenticadas."""
from html import escape
import json
import os
from pathlib import Path
import re

from .core import ROOT, Erro

LISTAS = ('apelidos', 'passos', 'erros_comuns', 'cuidados', 'contraindicacoes', 'pare_se')


def caminho(ident, extensao):
    if not isinstance(ident, str) or not re.fullmatch(r'[a-z0-9-]+', ident):
        raise Erro(404, 'Exercício inexistente')
    pasta = ROOT / 'web' / 'exercicios'
    if extensao == 'mp4':
        pasta = Path(os.environ.get('EXERCICIOS_MP4_DIR') or pasta)
    return pasta / (ident + '.' + extensao)


def listar(c):
    return [apresentar(e) for e in c.catalogo('exercicios')]


def apresentar(item):
    return {**{k: [] for k in LISTAS}, **item, 'svg': caminho(item['id'], 'svg').is_file()}


def obter(c, ident, publico=False):
    item = next((e for e in c.catalogo('exercicios') if e['id'] == ident), None)
    if item is None or (publico and not item['ativo']):
        raise Erro(404, 'Exercício inexistente')
    return apresentar(item)


def salvar(c, b, ident=None):
    item = {**{k: [] for k in LISTAS}, 'ativo': True}
    if ident is not None:
        item.update(obter(c, ident))
    item.update({k: v for k, v in b.items() if k in (*LISTAS, 'id', 'nome', 'regiao', 'ativo')})
    if ident is not None:
        item['id'] = ident
    if not isinstance(item.get('id'), str) or not re.fullmatch(r'[a-z0-9-]+', item['id']):
        raise Erro(422, 'ID deve conter apenas letras minúsculas, números e hífen')
    if ident is None and any(e['id'] == item['id'] for e in c.catalogo('exercicios')):
        raise Erro(409, 'Exercício já cadastrado')
    for campo in ('nome', 'regiao'):
        if not isinstance(item.get(campo), str) or not item[campo].strip():
            raise Erro(422, campo + ' obrigatório')
    for campo in LISTAS:
        if not isinstance(item[campo], list) or any(not isinstance(v, str) or not v.strip() for v in item[campo]):
            raise Erro(422, campo + ' deve ser uma lista de textos')
    if not item['passos'] or type(item['ativo']) is not bool:
        raise Erro(422, 'Passos obrigatórios e ativo deve ser booleano')
    item.pop('svg', None)
    if ident is None:
        c.db.execute('INSERT INTO catalogo VALUES (?,?,?)', ('exercicios', item['id'], json.dumps(item)))
    else:
        c.db.execute('UPDATE catalogo SET dados=? WHERE tipo=? AND id=?', (json.dumps(item), 'exercicios', ident))
    return apresentar(item)


def pagina(c, ident):
    e = obter(c, ident, publico=True)
    secoes = []
    for campo, titulo in (('passos', 'Como fazer'), ('erros_comuns', 'Erros comuns'),
                          ('cuidados', 'Cuidados'), ('contraindicacoes', 'Contraindicações'), ('pare_se', 'Pare se')):
        tag = 'ol' if campo == 'passos' else 'ul'
        itens = ''.join('<li>' + escape(t) + '</li>' for t in e[campo])
        secoes.append(f'<section><h2>{titulo}</h2><{tag}>{itens}</{tag}></section>' if itens else '')
    ilustracao = (f'<figure><img src="/exercicios/{ident}.svg" alt="Movimento esquemático: {escape(e["nome"])}" width="400" height="400">'
                  '<figcaption>Ilustração do movimento. Siga a prescrição do seu fisioterapeuta.</figcaption></figure>') if e['svg'] else ''
    modelo = (ROOT / 'web' / 'exercicio.html').read_text(encoding='utf-8')
    return (modelo.replace('{{nome}}', escape(e['nome'])).replace('{{regiao}}', escape(e['regiao']))
            .replace('{{ilustracao}}', ilustracao).replace('{{secoes}}', ''.join(secoes))).encode('utf-8')


def recurso(c, rota):
    m = re.fullmatch(r'/exercicios/([a-z0-9-]+)(?:\.(svg|mp4))?', rota)
    if not m:
        raise Erro(404, 'Exercício inexistente')
    ident, extensao = m.groups()
    obter(c, ident, publico=True)
    if extensao:
        try:
            conteudo = caminho(ident, extensao).read_bytes()
        except FileNotFoundError:
            raise Erro(404, 'Arquivo indisponível')
        return ('image/svg+xml' if extensao == 'svg' else 'video/mp4'), conteudo
    return 'text/html; charset=utf-8', pagina(c, ident)
