# BioForma Studio

Português (Brasil) · [English](README.md)

**Versão 0.3.0 — aplicativo desktop bilíngue para Windows e Linux.**

Edite DNA, inspecione uma hélice idealizada, abra coordenadas PDB e programe um modelo
didático de expressão gênica em JSON. O uso básico é local e offline, sem conta, API paga ou telemetria. A consulta opcional ao NCBI exige internet.
O escopo é educacional e computacional; não há previsão de um organismo completo a partir do genoma.

## Instalação

Requer Python 3.10 ou superior com Tkinter. Recomenda-se Python 3.12.

**Windows 10/11:** extraia o pacote completo, execute `INSTALAR_WINDOWS.cmd` e abra o atalho.
A versão 0.3 é copiada para `%LOCALAPPDATA%\BioFormaStudio\app-0.3.0`, preservando as instalações anteriores.
O atalho BioForma passa a abrir a 0.3. O Python precisa permanecer instalado.
Para abrir sem instalar, use `ABRIR_SEM_INSTALAR.cmd` ou `py -3 main.py`.

**Linux com ambiente gráfico:** instale Python/Tkinter pelo gerenciador da distribuição.
Em Ubuntu, Linux Mint e Debian, o pacote gráfico é `python3-tk`.
Execute `bash INSTALAR_LINUX.sh`. O instalador cria a pasta do aplicativo no diretório de dados
do usuário, um lançador em `~/.local/bin` e uma entrada no menu de aplicativos.
Para abrir sem instalar, use `bash ABRIR_LINUX.sh` ou `python3 main.py`.
É necessária uma sessão gráfica X11/Wayland com suporte Tk; ambiente sem tela exige uma tela virtual.

Teste Tkinter com `python -m tkinter` no Windows ou `python3 -m tkinter` no Linux.
Os instaladores do aplicativo não precisam de administrador. A instalação de pacotes da
distribuição segue as permissões normais do sistema.

O pacote inclui código-fonte e scripts, sem executáveis nativos pré-compilados.
Os scripts de compilação e o workflow preparado permitem gerar os executáveis em cada sistema.

## Português e inglês

Escolha **Português (Brasil)** ou **English** no topo. Rótulos, guia, mensagens do aplicativo,
gráficos e detalhes dos objetos mudam imediatamente. A troca preserva conteúdo dos editores,
histórico de desfazer, cursor, dados do projeto e resultados numéricos. A preferência é reutilizada.

Também é possível abrir com `python main.py --language en` ou `--language pt`.
DNA, campos JSON, nomes de projetos definidos pelo usuário e identificadores CSV permanecem iguais.
As colunas CSV são `time_au`, `mrna_au` e `protein_au` nos dois idiomas.
Diálogos nativos e detalhes de erros do sistema podem seguir o idioma do sistema operacional.

Preferência no Windows: `%LOCALAPPDATA%\BioFormaStudio\settings.json`.
No Linux: `$XDG_CONFIG_HOME/bioforma-studio/settings.json`, por padrão em `~/.config`.
Logs ficam na pasta Windows correspondente ou em `$XDG_STATE_HOME/bioforma-studio/logs`,
por padrão sob `~/.local/state`.

## Funções e interpretação

| Área | Disponível | Limite científico |
|---|---|---|
| DNA | Validação IUPAC, GC%, reverso complementar, comparação por posição | Não descobre genes nem faz alinhamento evolutivo |
| Tradução | Código padrão; quadros +1/+2/+3; paradas e ambiguidade | Não prevê expressão, splicing, função ou dobramento |
| Importação | FASTA com um/vários registros; sequência ORIGIN GenBank | Não preserva FEATURES e outros metadados GenBank |
| DNA 3D | Rotação, zoom, deslocamento, seleção e SVG | Bases esquemáticas; não calcula deformação atômica |
| PDB | Primeiro modelo; nuvem de átomos/traço Cα; alternativas A/vazia | Coordenadas existentes; não prevê dobramento ou montagens |
| Circuitos | Produção/degradação com entradas constantes; AND/OR/NOT_A/XOR | Modelo didático determinístico sem calibração |
| Projetos | JSON; compatibilidade com formato 0.1 | Um registro de DNA por vez; não salva a câmera |
| Reprodução | JSON com entradas/resultados e hashes SHA-256 | Não certifica testes ou validade biológica |

Limites: 100 mil bases por sequência; 12 MB por arquivo/projeto; 160 bases por janela da hélice;
50 mil átomos no parser e 1.800 pontos no visor. Cortes são informados. A coloração do editor
abrange as primeiras 6 mil posições de texto. RNA com U e alinhamentos com lacunas não são aceitos.
O visor usa CPU/Tkinter, sem exigir CUDA. Não há salvamento automático.

## Exemplos

Abra `exemplos/demo.bioforma.json`. O fragmento de DNA incluído é inventado, sem função validada.
`geometria_artificial.pdb` tem coordenadas artificiais identificadas; não é proteína real ou predita.
Para estudar uma estrutura existente, obtenha um PDB de uma fonte científica, como o
[RCSB PDB](https://www.rcsb.org/), e confira a procedência na fonte.

## Pesquisa e reprodução

Na aba de guia, **Exportar registro de reprodução** grava projeto completo, parâmetros,
resumos de DNA/circuito/PDB, versões do aplicativo/Python, plataforma, idioma, algoritmo,
data UTC e hashes das entradas/resultados. Para o mesmo projeto, o idioma não muda os resultados
nem seus hashes. O arquivo exportado inclui os dados do projeto; revise-o antes de compartilhar.

[VALIDACAO.md](VALIDACAO.md) informa evidências obtidas.
[O protocolo de estudo proposto](docs/VALIDATION_PLAN.pt-BR.md) orienta uma futura avaliação.
Ele não descreve experimentos já realizados. Os testes atuais verificam computação e interface;
calibração e validação biológica não foram executadas.
O usuário confirmou que a versão 0.2 funcionou no Windows. Os testes locais da 0.3 passaram no Linux.
Veja VALIDACAO.md para resultados independentes e situação dos testes remotos e do sistema de destino.

## Referências públicas na versão 0.3

Abra **04 Referências públicas** e escolha um dos exemplos incluídos, disponíveis offline:

| Referência | Dado | Interpretação |
|---|---|---|
| NR_027552.1 | Locus parcial 16S rRNA de Bacillus subtilis, 1.517 bases | Referência bacteriana; não é genoma completo |
| NC_001422.1 | Genoma do bacteriófago PhiX174, 5.386 bases | DNA de fita simples; o duplex desenhado é idealizado |
| 1CRN | Crambina do RCSB PDB, 327 átomos | Coordenadas de raios X; independentes do DNA aberto |

Os arquivos originais FASTA/GenBank/PDB ficam em `referencias/`. O manifesto guarda acesso,
versão, URLs, coleta UTC e SHA-256. Abrir um exemplo confere seu hash. Projetos e registros
preservam a origem e indicam se o DNA atual ainda corresponde à sequência importada.
“Fixar referência” muda só a comparação posicional e conserva a origem histórica. Hashes
demonstram identidade de dados; não certificam validade biológica ou autenticidade de um
projeto editado externamente.

**Buscar FASTA no NCBI** aceita um acesso com versão e funciona em segundo plano. Envia apenas
o acesso informado ao NCBI; nenhum conteúdo do projeto é enviado. Não exige conta ou chave.
Limites: 20 segundos, 12 MB e 100 mil bases por sequência. Falhas preservam o projeto. Genomas
bacterianos maiores precisam de segmentos ou de uma futura interface para genomas completos.
Não há análise de genes/CDS anotados ou de outros códigos genéticos. Traduzir rRNA ou um genoma
em quadro arbitrário não demonstra expressão de proteínas reais.

A validação independente usa Biopython 1.86, SciPy 1.17.0 e NumPy 2.3.5, apenas para testes:

```sh
python -m pip install -r requirements-validation.txt
python scripts/validate_independent.py --output local-results/independent.json
```

Veja `validacao/PROTOCOL.md` e `validacao/results_v0.3.0.json`. Os 64 códons canônicos
coincidiram com Biopython. Das 3.375 combinações IUPAC, 127 apresentam diferenças intencionais:
BioForma usa X para qualquer códon ambíguo; Biopython consegue resolver alguns deles.
O circuito passou em 113 casos, com 56.613 instantes comparados e tolerância
`1e-7 + 1e-6*abs(referência)`. Isso é evidência computacional em amostra pequena.
Validação biológica e previsão de organismos continuam não realizadas.

## Pesquisa e publicação

Repositório: [BrunoJimez/BioForma](https://github.com/BrunoJimez/BioForma).
O roteiro científico e os próximos critérios estão em [RESEARCH_ROADMAP.md](docs/RESEARCH_ROADMAP.md).
O artigo e o depósito público com DOI são etapas futuras, após um estudo definido.
Não foi realizada submissão de artigo, nem há aceite ou DOI declarado.

## Testes e executáveis

Núcleo/catálogo: `python -m unittest discover -s tests -v`.
Interface gráfica: `python verificar_interface.py` em sessão gráfica.
Windows: `TESTAR.cmd` e `TESTAR_INTERFACE.cmd`. Linux: `bash TESTAR_LINUX.sh`.

Compilação nativa: `GERAR_EXE.cmd` no Windows ou `bash GERAR_BINARIO_LINUX.sh` no Linux.
Essa etapa baixa a versão fixada do PyInstaller e exige internet. O script comum
`build_executable.py` gera uma pasta de execução completa e um arquivo compactado por plataforma.
Distribua toda a pasta gerada. Não há garantia de compatibilidade do binário Linux com todas
as distribuições: ele depende da ABI do ambiente de compilação.

Os workflows preparados testam Windows/Linux com Python 3.10 e 3.12 e oferecem compilação manual
nos dois sistemas. Eles só executarão remotamente depois da publicação do repositório.
Os binários serão artifacts do Actions; o workflow não cria automaticamente uma release pública.

## GitHub e citação

O pacote inclui licença MIT, `CITATION.cff`, histórico de versões, guia de contribuição,
template de erro, regras de arquivos ignorados, documentação bilíngue e workflows.
Leia [GITHUB.md](GITHUB.md) para publicar. Nenhum repositório, DOI ou resultado remoto foi inventado.
A autoria atual é Bruno Jimez; inclua colaboradores efetivos antes da versão destinada à publicação.

Referências: [NCBI](https://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi),
[wwPDB](https://www.wwpdb.org/documentation/file-format-content/format33/sect9.html),
[Tkinter](https://docs.python.org/3/library/tkinter.html),
[GitHub CI](https://docs.github.com/en/actions/tutorials/build-and-test-code/python) e
[PyInstaller](https://pyinstaller.org/en/stable/).
