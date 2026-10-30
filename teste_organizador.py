import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import organizador_logica as logica

ORIGINAL = Path(r'C:\Users\Vasco\Teste_Organizador')


def retrato(pasta):
    return {str(p.relative_to(pasta)): hashlib.sha256(p.read_bytes()).hexdigest()
            if p.is_file() else None for p in pasta.rglob('*')}


class TesteOrganizador(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.antes = retrato(ORIGINAL)

    @classmethod
    def tearDownClass(cls):
        if cls.antes != retrato(ORIGINAL):
            raise AssertionError('O ambiente original foi alterado!')

    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name) / 'copia'
        self.pasta.mkdir()
        nomes = ['relatorio.pdf', 'relatorio.txt', 'relatorio.docx', 'orcamento.xlsx',
                 'dados.csv', 'foto.jpg', 'desenho.png', 'audio.mp3', 'config.json',
                 'exemplo.py', 'pacote.zip', 'desconhecido.xyz',
                 'Documentos/ata.docx', 'Documentos/manual.pdf', 'Documentos/notas.txt',
                 'Documentos/dados.csv', 'Imagens/foto.jpg', 'Imagens/paisagem.png',
                 'Imagens/icone.png', 'Imagens/legenda.txt', 'Downloads/pacote.zip',
                 'Downloads/audio.mp3', 'Downloads/tabela.xlsx', 'Downloads/config.json',
                 'Arquivos_Antigos/relatorio.pdf', 'Arquivos_Antigos/notas.txt',
                 'Arquivos_Antigos/backup.zip', 'Outros/exemplo.py',
                 'Outros/inventario.json', 'Outros/amostra.xyz']
        for nome in nomes:
            arquivo = self.pasta / nome
            arquivo.parent.mkdir(exist_ok=True)
            arquivo.write_text(f'Conteudo sintetico para testar movimentacao: {nome}', encoding='utf-8')
        self.regras = {}

    def regra(self, ext='.txt', destino='Outros'):
        return logica.adicionar_regra(self.pasta, self.regras, ext, destino)

    def test_01_leitura(self):
        self.assertEqual(len(logica.listar_subpastas(self.pasta)), 5)
        self.assertEqual(len(logica.listar_arquivos(self.pasta)), 12)
        self.assertNotIn('ata.docx', logica.listar_arquivos(self.pasta))

    def test_02_regras(self):
        self.regra(' PDF ', 'Imagens')
        self.assertEqual(self.regras, {'.pdf': 'Imagens'})
        self.regra('.pdf', 'Outros')
        self.regra('.txt', 'Outros')
        copia = logica.consultar_regras(self.regras); copia.clear()
        self.assertEqual(len(self.regras), 2)
        self.assertTrue(logica.remover_regra(self.regras, 'PDF'))
        self.assertFalse(logica.remover_regra(self.regras, 'pdf'))

    def test_03_simulacao_nao_modifica(self):
        self.regra('.pdf', 'Imagens')
        antes = retrato(self.pasta)
        itens = logica.simular_organizacao(self.pasta, self.regras)
        self.assertEqual(antes, retrato(self.pasta))
        self.assertEqual(sum(i['status']=='previsto' for i in itens), 1)
        self.assertEqual(sum(i['status']=='sem_regra' for i in itens), 11)

    def test_04_automatico_e_subpastas_intactas(self):
        self.regra('.pdf', 'Imagens'); self.regra('.txt', 'Imagens')
        antigo = (self.pasta/'Arquivos_Antigos/relatorio.pdf').read_bytes()
        resultado = logica.organizar_arquivos(self.pasta, self.regras)
        self.assertEqual(sum(i['status']=='movido' for i in resultado), 2)
        self.assertTrue((self.pasta/'Imagens/relatorio.pdf').exists())
        self.assertEqual((self.pasta/'Arquivos_Antigos/relatorio.pdf').read_bytes(), antigo)
        self.assertTrue((self.pasta/'desconhecido.xyz').exists())

    def test_05_manual_independe_de_regra(self):
        self.regra('.txt', 'Documentos')
        destino = logica.mover_arquivo(self.pasta, 'relatorio.txt', 'Outros')
        self.assertEqual(destino, self.pasta/'Outros/relatorio.txt')
        self.assertFalse((self.pasta/'relatorio.txt').exists())

    def test_06_conflito_sem_sobrescrita(self):
        antes = retrato(self.pasta)
        self.regra('.jpg', 'Imagens')
        self.assertEqual(next(i for i in logica.organizar_arquivos(self.pasta, self.regras)
                              if i['arquivo']=='foto.jpg')['status'], 'conflito')
        with self.assertRaises(FileExistsError):
            logica.mover_arquivo(self.pasta, 'foto.jpg', 'Imagens')
        self.assertEqual(antes, retrato(self.pasta))

    def test_07_caminhos_invalidos(self):
        with self.assertRaises(FileNotFoundError):
            logica.listar_arquivos(self.pasta/'inexistente')
        with self.assertRaises(NotADirectoryError):
            logica.listar_arquivos(self.pasta/'dados.csv')
        for destino in ['../fora', str(self.pasta.parent), 'Documentos/filha', '..']:
            with self.subTest(destino=destino), self.assertRaises(ValueError):
                self.regra('.txt', destino)
        with self.assertRaises(FileNotFoundError): self.regra('.txt', 'Ausente')
        with self.assertRaises(ValueError): self.regra('.txt', 'dados.csv')
        with self.assertRaises(FileNotFoundError):
            logica.mover_arquivo(self.pasta, 'ausente.txt', 'Outros')
        with self.assertRaises(ValueError):
            logica.mover_arquivo(self.pasta, 'Documentos/ata.docx', 'Outros')
        with self.assertRaises(ValueError):
            logica.mover_arquivo(self.pasta, 'Documentos', 'Outros')

    def test_08_extensoes(self):
        for ext in ['', '.', '.tar.gz', '../txt', None]:
            with self.subTest(ext=ext), self.assertRaises(ValueError): self.regra(ext)
        self.regra('XYZ')
        resultado = logica.organizar_arquivos(self.pasta, self.regras)
        self.assertTrue(any(i['arquivo']=='desconhecido.xyz' and i['status']=='movido'
                            for i in resultado))
        (self.pasta/'MAIUSCULO.TXT').write_text('teste')
        self.regra('.txt')
        logica.organizar_arquivos(self.pasta, self.regras)
        self.assertTrue((self.pasta/'Outros/MAIUSCULO.TXT').exists())

    def test_09_destino_removido_apos_regra(self):
        self.regra('.txt', 'Outros')
        with patch.object(logica, '_subpasta', side_effect=FileNotFoundError('Destino ausente')):
            itens = logica.organizar_arquivos(self.pasta, self.regras)
        self.assertEqual(next(i for i in itens if i['arquivo']=='relatorio.txt')['status'], 'erro')

    def test_10_permissao_e_continuidade(self):
        self.regra('.txt'); self.regra('.pdf')
        mover = logica.mover_arquivo
        def falha_se_txt(pasta, arquivo, destino):
            if arquivo.endswith('.txt'): raise PermissionError('Permissão negada simulada')
            return mover(pasta, arquivo, destino)
        with patch.object(logica, 'mover_arquivo', side_effect=falha_se_txt):
            itens = logica.organizar_arquivos(self.pasta, self.regras)
        self.assertTrue(any(i['status']=='erro' for i in itens))
        self.assertTrue(any(i['status']=='movido' for i in itens))
        self.assertTrue((self.pasta/'relatorio.txt').exists())
        with patch.object(Path, 'iterdir', side_effect=PermissionError('Sem acesso')):
            with self.assertRaises(PermissionError): logica.listar_arquivos(self.pasta)

    def test_11_conflito_surgido_depois_da_simulacao(self):
        self.regra('.txt')
        with patch.object(logica, 'mover_arquivo', side_effect=FileExistsError('Conflito novo')):
            itens = logica.organizar_arquivos(self.pasta, self.regras)
        self.assertTrue(any(i['status']=='conflito' for i in itens))

    def test_12_juncao_externa(self):
        import subprocess
        fora = Path(self.temporario.name)/'fora'; fora.mkdir()
        link = self.pasta/'Atalho'
        processo = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(fora)],
                                  capture_output=True)
        if processo.returncode:
            self.skipTest('O ambiente não permite criar junções.')
        self.addCleanup(lambda: link.rmdir() if link.exists() else None)
        self.assertNotIn('Atalho', logica.listar_subpastas(self.pasta))
        with self.assertRaises(ValueError): self.regra('.txt', 'Atalho')
        (fora/'externo_ficticio.txt').write_text('nao deve aparecer na arvore')
        from UI import Interface
        arvore = MagicMock()
        Interface.__new__(Interface).preencher_arvore(arvore, '', self.pasta)
        rotulos = [chamada.kwargs['text'] for chamada in arvore.insert.call_args_list]
        self.assertFalse(any('externo_ficticio.txt' in texto or 'Atalho' in texto for texto in rotulos))
        self.assertTrue((fora/'externo_ficticio.txt').exists())


    def test_13_pendentes_sem_movimentar(self):
        pendentes = {}
        antes = retrato(self.pasta)
        logica.registrar_movimentacoes_manuais(self.pasta, pendentes,
                                             ['relatorio.txt', 'relatorio.pdf'], 'Outros')
        copia = logica.consultar_movimentacoes_manuais(pendentes)
        copia.clear()
        self.assertEqual(len(pendentes), 2)
        logica.registrar_movimentacoes_manuais(self.pasta, pendentes,
                                             ['relatorio.txt'], 'Imagens')
        self.assertEqual(pendentes['relatorio.txt'], 'Imagens')
        self.assertTrue(logica.remover_movimentacao_manual(pendentes, 'relatorio.pdf'))
        self.assertFalse(logica.remover_movimentacao_manual(pendentes, 'ausente.txt'))
        self.assertEqual(antes, retrato(self.pasta))
        self.assertEqual(self.regras, {})

    def test_14_prioridade_manual_e_previa(self):
        self.regra('.pdf', 'Documentos')
        pendentes = {'relatorio.pdf': 'Imagens'}
        antes = retrato(self.pasta)
        plano = logica.gerar_previsualizacao(self.pasta, self.regras, pendentes)
        item = next(i for i in plano['itens'] if i['arquivo']=='relatorio.pdf')
        self.assertEqual((item['origem'], item['destino'], item['status']),
                         ('manual', 'Imagens', 'previsto'))
        self.assertEqual(antes, retrato(self.pasta))
        self.assertEqual(len(plano['itens']), 12)
        resultado = logica.executar_movimentacoes(plano)
        self.assertEqual(resultado['resumo']['movido'], 1)
        self.assertEqual(resultado['resumo']['sem_regra'], 11)
        self.assertTrue((self.pasta/'Imagens/relatorio.pdf').exists())
        self.assertFalse((self.pasta/'Documentos/relatorio.pdf').exists())
        self.assertEqual(item['status'], 'previsto')

    def test_15_plano_congelado(self):
        self.regra('.txt', 'Outros')
        pendentes = {}
        plano = logica.gerar_previsualizacao(self.pasta, self.regras, pendentes)
        self.regra('.txt', 'Imagens')
        pendentes['relatorio.txt'] = 'Documentos'
        (self.pasta/'novo.txt').write_text('arquivo posterior')
        resultado = logica.executar_movimentacoes(plano)
        self.assertEqual(resultado['resumo']['movido'], 1)
        self.assertTrue((self.pasta/'Outros/relatorio.txt').exists())
        self.assertTrue((self.pasta/'novo.txt').exists())

    def test_16_duplicatas_recusadas_antes_de_mover(self):
        plano = logica.gerar_previsualizacao(self.pasta, {}, {'relatorio.txt':'Outros'})
        item = next(i for i in plano['itens'] if i['arquivo']=='relatorio.txt')
        plano['itens'].append(dict(item))
        antes = retrato(self.pasta)
        with self.assertRaises(ValueError): logica.executar_movimentacoes(plano)
        self.assertEqual(antes, retrato(self.pasta))

    def test_17_falhas_depois_da_previa(self):
        pendentes = {'relatorio.txt':'Outros', 'relatorio.pdf':'Imagens', 'dados.csv':'Outros'}
        plano = logica.gerar_previsualizacao(self.pasta, {}, pendentes)
        (self.pasta/'Outros/relatorio.txt').write_text('nao sobrescrever')
        (self.pasta/'relatorio.pdf').write_bytes(b'alterado depois da previa')
        resultado = logica.executar_movimentacoes(plano)
        self.assertEqual(resultado['resumo']['conflito'], 1)
        self.assertEqual(resultado['resumo']['erro'], 1)
        self.assertEqual(resultado['resumo']['movido'], 1)
        self.assertEqual((self.pasta/'Outros/relatorio.txt').read_text(), 'nao sobrescrever')
        self.assertTrue((self.pasta/'relatorio.pdf').exists())

    def test_18_escolha_manual_invalida_nao_cai_na_regra(self):
        self.regra('.txt', 'Imagens')
        plano = logica.gerar_previsualizacao(self.pasta, self.regras,
                                           {'relatorio.txt':'Ausente', 'sumiu.txt':'Outros'})
        resultado = logica.executar_movimentacoes(plano)
        self.assertEqual(resultado['resumo']['erro'], 2)
        self.assertEqual(resultado['resumo']['movido'], 0)
        self.assertTrue((self.pasta/'relatorio.txt').exists())

    def test_19_lotes_atomicos(self):
        logica.adicionar_regras(self.pasta, self.regras, ['PDF', '.txt'], 'Outros')
        antes = dict(self.regras)
        with self.assertRaises(ValueError):
            logica.adicionar_regras(self.pasta, self.regras, ['.jpg', '..'], 'Imagens')
        self.assertEqual(antes, self.regras)
        pendentes = {}
        with self.assertRaises(FileNotFoundError):
            logica.registrar_movimentacoes_manuais(self.pasta, pendentes,
                                                 ['relatorio.txt', 'ausente.txt'], 'Outros')
        self.assertEqual(pendentes, {})
        with self.assertRaises(ValueError):
            logica.registrar_movimentacoes_manuais(self.pasta, pendentes,
                                                 ['relatorio.txt'], '../fora')

    def test_20_reexecucao_nao_duplica(self):
        plano = logica.gerar_previsualizacao(self.pasta, {}, {'relatorio.txt':'Outros'})
        logica.executar_movimentacoes(plano)
        antes = retrato(self.pasta)
        resultado = logica.executar_movimentacoes(plano)
        self.assertEqual(resultado['resumo']['movido'], 0)
        self.assertEqual(resultado['resumo']['erro'], 1)
        self.assertEqual(antes, retrato(self.pasta))

    def test_21_previa_conjunta_conflitos_e_automaticos(self):
        self.regra('.pdf', 'Imagens')
        plano = logica.gerar_previsualizacao(self.pasta, self.regras, {'foto.jpg':'Imagens'})
        por_nome = {i['arquivo']:i for i in plano['itens']}
        self.assertEqual(por_nome['foto.jpg']['status'], 'conflito')
        self.assertEqual(por_nome['foto.jpg']['origem'], 'manual')
        self.assertEqual(por_nome['relatorio.pdf']['origem'], 'automatica')
        self.assertIsNone(por_nome['desconhecido.xyz']['origem'])
        self.assertEqual(sum(logica.resumir_resultados(plano['itens'])[s]
                             for s in ('previsto','movido','erro','conflito','sem_regra')), 12)

    def test_22_destino_invalido_na_execucao(self):
        plano = logica.gerar_previsualizacao(self.pasta, {}, {'relatorio.txt':'Outros'})
        with patch.object(logica, '_subpasta', side_effect=PermissionError('Sem acesso')):
            resultado = logica.executar_movimentacoes(plano)
        self.assertEqual(resultado['resumo']['erro'], 1)
        self.assertTrue((self.pasta/'relatorio.txt').exists())


    def test_23_listar_extensoes(self):
        extensoes = logica.listar_extensoes(self.pasta)
        (self.pasta/'OUTRO.PDF').write_text('teste')
        (self.pasta/'sem_extensao').write_text('teste')
        (self.pasta/'Documentos/interno.unico').write_text('teste')
        self.assertEqual(logica.listar_extensoes(self.pasta), extensoes)
        self.assertIn('.xyz', extensoes)
        self.assertEqual(len(extensoes), 12)

    def test_24_lote_de_cinco_extensoes(self):
        (self.pasta/'Destino').mkdir()
        extensoes = ['.pdf', '.txt', '.docx', '.xlsx', '.jpg']
        for extensao in extensoes:
            for numero in range(3):
                (self.pasta/f'lote_{numero}{extensao}').write_text('teste ficticio')
        logica.adicionar_regras(self.pasta, self.regras, extensoes, 'Destino')
        resultado = logica.executar_movimentacoes(
            logica.gerar_previsualizacao(self.pasta, self.regras, {})
        )
        self.assertEqual(resultado['resumo']['movido'], 20)
        self.assertEqual(len(logica.listar_arquivos(self.pasta/'Destino')), 20)
        self.assertTrue((self.pasta/'Imagens/foto.jpg').exists())


    def test_25_arvore_mostra_nomes_de_pastas(self):
        from UI import Interface
        arvore = MagicMock()
        Interface.__new__(Interface).preencher_arvore(arvore, '', self.pasta)
        rotulos = [chamada.kwargs['text'] for chamada in arvore.insert.call_args_list]
        self.assertIn('📁 Documentos', rotulos)
        self.assertIn('📁 Imagens', rotulos)
        self.assertIn('📄 relatorio.txt', rotulos)
        self.assertIn('📄 ata.docx', rotulos)

    def test_26_arvore_trata_pasta_removida(self):
        from UI import Interface
        arvore = MagicMock()
        Interface.__new__(Interface).preencher_arvore(arvore, '', self.pasta/'Removida')
        self.assertEqual(arvore.insert.call_args.kwargs['values'][0], 'Erro')

    def test_27_arvore_trata_permissao(self):
        from UI import Interface
        arvore = MagicMock()
        with patch.object(Path, 'iterdir', side_effect=PermissionError('Acesso negado')):
            Interface.__new__(Interface).preencher_arvore(arvore, '', self.pasta)
        self.assertEqual(arvore.insert.call_args.kwargs['values'][0], 'Erro')
        self.assertIn('Acesso negado', arvore.insert.call_args.kwargs['text'])

    def test_28_conclusao_distingue_conflitos(self):
        import UI
        app = UI.Interface.__new__(UI.Interface)
        app.master = MagicMock()
        app.corFundo = '#1e1e2e'
        app.telaPasta = MagicMock()
        app.centralizar = MagicMock()
        for movidos, conflitos, titulo in [
            ([('a.pdf', 'Documentos')], [('b.pdf', 'Ja existe')], 'Concluído com 1 conflito(s)'),
            ([], [('b.pdf', 'Ja existe')], 'Nenhum arquivo movido: há conflitos'),
            ([('a.pdf', 'Documentos')], [], 'Organização concluída com sucesso!'),
        ]:
            with self.subTest(titulo=titulo), patch.multiple(
                UI, Frame=MagicMock(), Button=MagicMock(), Label=MagicMock()
            ), patch.multiple(UI.ttk, Style=MagicMock(), Treeview=MagicMock(), Scrollbar=MagicMock()):
                app.mostrar_conclusao(str(self.pasta), movidos, [], conflitos, 0)
                self.assertEqual(UI.Label.call_args_list[0].kwargs['text'], titulo)


if __name__ == '__main__':
    unittest.main(verbosity=2)
