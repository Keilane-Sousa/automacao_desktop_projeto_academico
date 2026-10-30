from pathlib import Path
import os


regras = {}


def _pasta(caminho):
    pasta = Path(caminho).resolve(strict=True)
    if not pasta.is_dir():
        raise NotADirectoryError(f'Não é uma pasta: {pasta}')
    return pasta


def _nome(nome):
    texto = str(nome)
    if not texto or texto in ('.', '..') or any(c in texto for c in '/\\:'):
        raise ValueError('Informe somente o nome, sem caminhos ou unidades.')
    if Path(texto).name != texto:
        raise ValueError('Nome inválido.')
    return texto


def _subpasta(pasta, nome):
    destino = pasta / _nome(nome)
    if destino.is_symlink() or destino.is_junction():
        raise ValueError('Links e junções não são destinos permitidos.')
    real = destino.resolve(strict=True)
    if real.parent != pasta or not real.is_dir():
        raise ValueError('O destino deve ser uma subpasta direta existente.')
    return real


def _extensao(extensao):
    if not isinstance(extensao, str):
        raise ValueError('A extensão deve ser texto.')
    ext = extensao.strip().lower()
    if not ext.startswith('.'):
        ext = '.' + ext
    if len(ext) < 2 or any(c in ext[1:] for c in '. /\\:*?"<>|\t\n\r'):
        raise ValueError('Use uma extensão simples, como .pdf ou .txt.')
    return ext


def listar_subpastas(pasta_principal):
    pasta = _pasta(pasta_principal)
    return sorted((p.name for p in pasta.iterdir()
                   if not p.is_symlink() and not p.is_junction() and p.is_dir()),
                  key=str.casefold)


def listar_arquivos(pasta_principal):
    pasta = _pasta(pasta_principal)
    return sorted((p.name for p in pasta.iterdir()
                   if not p.is_symlink() and p.is_file()), key=str.casefold)


def listar_extensoes(pasta_principal):
    return sorted({Path(nome).suffix.lower() for nome in listar_arquivos(pasta_principal)
                   if Path(nome).suffix})


def adicionar_regra(pasta_principal, regras, extensao, subpasta):
    pasta = _pasta(pasta_principal)
    ext = _extensao(extensao)
    destino = _subpasta(pasta, subpasta)
    regras[ext] = destino.name
    return consultar_regras(regras)


def remover_regra(regras, extensao):
    return regras.pop(_extensao(extensao), None) is not None


def consultar_regras(regras):
    return dict(regras)


def _registro(arquivo, destino, status, mensagem):
    return {'arquivo': arquivo, 'destino': destino,
            'status': status, 'mensagem': mensagem}


def _avaliar_movimentacao(pasta, nome, destino, registrar_assinatura=False):
    item = _registro(nome, destino, 'previsto', 'Arquivo seria movido.')
    try:
        alvo = _subpasta(pasta, destino) / nome
        if registrar_assinatura:
            item['assinatura'] = _assinatura(pasta / nome)
        if os.path.lexists(alvo):
            item.update(status='conflito', mensagem='Já existe um item com esse nome.')
    except (OSError, ValueError) as erro:
        item.update(status='erro', mensagem=str(erro))
    return item


def simular_organizacao(pasta_principal, regras):
    pasta = _pasta(pasta_principal)
    resultado = []
    for nome in listar_arquivos(pasta):
        destino = regras.get(Path(nome).suffix.lower())
        item = (_registro(nome, None, 'sem_regra', 'Nenhuma regra cadastrada.')
                if destino is None else _avaliar_movimentacao(pasta, nome, destino))
        resultado.append(item)
    return resultado


def mover_arquivo(pasta_principal, arquivo, subpasta):
    pasta = _pasta(pasta_principal)
    origem = pasta / _nome(arquivo)
    if origem.is_symlink():
        raise ValueError('Links não podem ser movidos.')
    if not origem.exists():
        raise FileNotFoundError(f'Arquivo não encontrado: {origem.name}')
    if not origem.is_file():
        raise ValueError('A origem deve ser um arquivo da pasta principal.')
    destino = _subpasta(pasta, subpasta) / origem.name
    if os.path.lexists(destino):
        raise FileExistsError(f'Já existe no destino: {destino.name}')
    if os.name == 'nt':
        origem.rename(destino)
    else:
        os.link(origem, destino)
        origem.unlink()
    return destino


def _executar_itens(pasta, itens, verificar_assinatura=False):
    for item in itens:
        if item['status'] != 'previsto':
            continue
        try:
            if verificar_assinatura:
                origem = pasta / item['arquivo']
                if origem.is_symlink() or _assinatura(origem) != item.get('assinatura'):
                    raise ValueError('Arquivo mudou desde a prévia. Gere uma nova prévia.')
            mover_arquivo(pasta, item['arquivo'], item['destino'])
            item.update(status='movido', mensagem='Arquivo movido.')
        except FileExistsError as erro:
            item.update(status='conflito', mensagem=str(erro))
        except (OSError, ValueError) as erro:
            item.update(status='erro', mensagem=str(erro))


def organizar_arquivos(pasta_principal, regras):
    resultado = simular_organizacao(pasta_principal, regras)
    _executar_itens(pasta_principal, resultado)
    return resultado


def adicionar_regras(pasta_principal, regras, extensoes, subpasta):
    if isinstance(extensoes, str):
        raise ValueError('Informe uma lista de extensões.')
    extensoes = [_extensao(extensao) for extensao in extensoes]
    if extensoes:
        destino = _subpasta(_pasta(pasta_principal), subpasta)
        regras.update(dict.fromkeys(extensoes, destino.name))
    return consultar_regras(regras)


def registrar_movimentacoes_manuais(pasta_principal, pendentes, arquivos, subpasta):
    pasta = _pasta(pasta_principal)
    destino = _subpasta(pasta, subpasta)
    if isinstance(arquivos, str):
        raise ValueError('Informe uma lista de nomes de arquivos.')
    disponiveis = {os.path.normcase(nome): nome for nome in listar_arquivos(pasta)}
    novos = {}
    for arquivo in arquivos:
        nome = _nome(arquivo)
        if os.path.normcase(nome) not in disponiveis:
            raise FileNotFoundError(f'Arquivo direto não encontrado: {nome}')
        novos[disponiveis[os.path.normcase(nome)]] = destino.name
    pendentes.update(novos)
    return consultar_movimentacoes_manuais(pendentes)


def remover_movimentacao_manual(pendentes, arquivo):
    nome = os.path.normcase(_nome(arquivo))
    for chave in list(pendentes):
        if os.path.normcase(chave) == nome:
            del pendentes[chave]
            return True
    return False


def consultar_movimentacoes_manuais(pendentes):
    return dict(pendentes)


def _assinatura(arquivo):
    dados = arquivo.stat()
    return (dados.st_dev, dados.st_ino, dados.st_size, dados.st_mtime_ns)


def gerar_previsualizacao(pasta_principal, regras, pendentes):
    pasta = _pasta(pasta_principal)
    manuais = {}
    for arquivo, destino in pendentes.items():
        chave = os.path.normcase(_nome(arquivo))
        if chave in manuais:
            raise ValueError('Existe mais de uma escolha manual para o mesmo arquivo.')
        manuais[chave] = (arquivo, destino)
    nomes = listar_arquivos(pasta)
    vistos = set()
    itens = []
    for nome in nomes:
        chave = os.path.normcase(nome)
        vistos.add(chave)
        if chave in manuais:
            destino = manuais[chave][1]
            origem = 'manual'
        else:
            destino = regras.get(Path(nome).suffix.lower())
            origem = 'automatica' if destino is not None else None
        item = _registro(nome, destino, 'sem_regra', 'Nenhuma regra ou escolha manual.')
        item['origem'] = origem
        if origem is not None:
            item.update(_avaliar_movimentacao(pasta, nome, destino, registrar_assinatura=True))
        itens.append(item)
    for chave, (nome, destino) in manuais.items():
        if chave not in vistos:
            item = _registro(nome, destino, 'erro', 'Arquivo manual ausente ou não permitido na raiz.')
            item['origem'] = 'manual'
            itens.append(item)
    return {'pasta_principal': str(pasta), 'itens': itens}


def resumir_resultados(itens):
    contagens = {status: 0 for status in
                 ('previsto', 'movido', 'sem_regra', 'conflito', 'erro')}
    for item in itens:
        contagens[item['status']] += 1
    return {'total': len(itens), **contagens}


def executar_movimentacoes(plano):
    pasta = _pasta(plano['pasta_principal'])
    itens = [dict(item) for item in plano['itens']]
    vistos = set()
    for item in itens:
        chave = os.path.normcase(_nome(item['arquivo']))
        if chave in vistos:
            raise ValueError('Plano contém movimentações duplicadas. Gere uma nova prévia.')
        vistos.add(chave)
        if item['status'] not in ('previsto', 'sem_regra', 'conflito', 'erro'):
            raise ValueError('Status inválido no plano. Gere uma nova prévia.')
    _executar_itens(pasta, itens, verificar_assinatura=True)
    return {'pasta_principal': str(pasta), 'itens': itens,
            'resumo': resumir_resultados(itens)}
