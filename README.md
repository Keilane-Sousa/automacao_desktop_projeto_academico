# Automação de desktop - Projeto academico

projeto de automação de desktop, baseado em paradigma de programação em python.


## Objetivo:
Criar de maneira simples uma automação que organize em pastas separadas arquivos salvos, por meio do seu tipo.


## Criadores:
* Ygor do Amaral
* Keilane de Sousa
* Matheus de Vasconcelos
* Allan dos santos
*  Cláudio Max

  
## Funcionalidades: 
* selecionar pasta
* Gerenciar regras
* Organizar arquivos
* Pré-visualização
* Configurações



## Como executar

Requer Python 3.12 ou superior com Tkinter. O projeto utiliza somente a biblioteca padrão do Python.

```powershell
python UI.py
```

Selecione a pasta principal, associe as extensões às subpastas existentes em **Regras de Organização** e confira a prévia antes de confirmar. As regras ficam em memória durante o uso da pasta selecionada. Somente arquivos da pasta principal são organizados; arquivos das subpastas permanecem intactos. Arquivos sem regra e conflitos de nome não são movidos, e arquivos existentes não são sobrescritos.

## Testes

```powershell
python -m unittest -v teste_organizador
```

Os testes criam arquivos fictícios em diretórios temporários. Para definir o destino de um arquivo individual, use **+ Arquivo específico** na tela de regras. Essa escolha tem prioridade sobre a regra por extensão e passa pela prévia e confirmação antes da movimentação.
