# Evidências / Evidence — BioForma Studio 0.3.0

## Resultados locais medidos em 2026-10-11

Linux, Python 3.12.14; Biopython 1.86, SciPy 1.17.0, NumPy 2.3.5.
O usuário confirmou anteriormente que a versão 0.2 funcionou em seu Windows.
Esse relato é distinto dos testes automatizados da 0.3.

| Verificação | Resultado observado |
|---|---|
| Núcleo, projeto, idioma, instalador Linux e referências | 35 testes passaram, 0 falhas |
| Interface nativa Linux, português e inglês | Ambos os fluxos passaram com Xvfb |
| FASTA/GenBank ORIGIN de NR_027552.1 e NC_001422.1 | Sequências idênticas à leitura independente de Biopython |
| Tamanho, GC, reverso complementar e três quadros | Concordância nos dois registros |
| 64 códons canônicos | Concordância exata com Biopython |
| 3.375 códons IUPAC | Política declarada conferida; 127 diferenças intencionais do consenso Biopython |
| 1CRN | 327 átomos, identidades iguais; erro máximo de coordenadas 9,46045e-7 Å; limite 0,001 Å |
| Traço Cα de 1CRN | 46 pontos, 45 conexões |
| Circuito contra SciPy DOP853 | 113 casos passaram; 56.613 instantes comparados |
| Critério numérico do circuito | Erro <= 1e-7 + 1e-6*abs(referência) em cada componente |
| Consulta real ao NCBI, NR_027552.1 | 1.517 bases; igual à referência congelada |

O máximo erro absoluto contra o integrador foi 1,74685e-5; o máximo quociente
erro/tolerância foi 0,559201 (aprovação requer <=1). A tolerância inclui termo
relativo, portanto o erro absoluto máximo não deve ser comparado apenas com 1e-7.
A comparação mede concordância computacional, não erro biológico.

### Correções demonstradas

Uma comparação exploratória da 0.2 encontrou cancelamento numérico quando
decay_m=0,2 e decay_p=0,2+1,1e-10 (erro máximo 5,80425e-6; falha no critério).
A 0.3 usa expm1 em uma diferença dividida estável. A suíte completa passou depois
da correção. Outro ajuste preserva exatamente o tempo final para evitar que o
arredondamento coloque o último instante fora do intervalo do integrador.
Nenhuma tolerância foi relaxada. O diagnóstico original e o protocolo estão
registrados em `validacao/PROTOCOL.md`.

### Escopo da interface

Os fluxos nativos verificaram abertura de cada referência, origem, hashes,
salvar/reabrir, exportar registro e SVG, troca PT/EN, dados e resultados
invariantes, rascunho/cursor/desfazer preservados, suspensão de resultados
em entradas inválidas, e sucesso/erro de busca assíncrona com respostas simuladas.
A consulta real ao NCBI foi verificada separadamente e documentada.
A instalação Linux em diretório temporário com espaços e o launcher foram testados.
Não foi produzido ou validado um executável nativo nesta etapa; o pacote contém
código e instaladores dependentes de Python/Tkinter.

## Reproduzir / reproduce

```sh
python -m unittest discover -s tests -v
python -m pip install -r requirements-validation.txt
python scripts/validate_independent.py --output local-results/independent.json
python verificar_interface.py
```

O teste da interface exige display; CI Linux usa `xvfb-run -a`. Dependências
científicas são só para validação; o aplicativo mantém runtime de biblioteca padrão.
Resultados medidos completos: `validacao/results_v0.3.0.json`.
Evidências da interface: `validacao/desktop_checks.json`. Consulta real:
`validacao/live_ncbi_check.json`. Fontes/bytes: `referencias/manifest.json`.
Hashes de código, protocolo e arquivos permitem conferir a versão que foi medida.
Reexecutar pode mudar tempo, ambiente e pequenos erros numéricos do integrador;
o critério de aceitação permanece explícito.

## Limites científicos e pendências

É uma verificação conduzida pelo desenvolvedor em amostra de conveniência pequena:
dois registros de nucleotídeos e uma estrutura. Não há estimativa de acurácia
geral, revisão por pares, avaliação com participantes, validação biológica ou
previsão de organismos. FEATURES não são interpretadas. O PDB testado não cobre
complexidade de conformações alternativas ou montagens biológicas. O código
genético é o padrão; outros códigos exigem implementação e validação próprias.

BioForma usa X em qualquer códon ambíguo. Biopython resolve alguns deles, incluindo
códons degenerados que codificam um único aminoácido. As 127 diferenças estão
listadas no JSON; não são ocultadas como concordância. O dado bacteriano é um
locus rRNA parcial, sem significado proteico na tradução arbitrária. PhiX174 tem
DNA de fita simples; o duplex da interface é uma ilustração.

O usuário confirmou a 0.2 no Windows. O pacote 0.3 ainda precisa de uso manual no
computador de destino. O workflow remoto testa Windows e Linux; verificar seu
resultado na aba Actions depois do envio. Não declarar resultados remotos antes
de observá-los. O paper e o DOI são etapas futuras em `docs/RESEARCH_ROADMAP.md`.

## English evidence summary

35 local core/localization/reference/Linux-install tests passed. Both native Linux
PT/EN GUI flows passed. Two NCBI nucleotide fixtures matched Biopython for import,
GC, reverse complement and all three forward-frame translations. All 64 canonical
codons matched; 127 intentional conservative ambiguity-policy differences among
3,375 IUPAC codons are disclosed. Crambin PDB identities/count/coordinates and CA
trace matched the reference on the measured fixture. 113 ODE cases passed the
predefined mixed absolute/relative tolerance at 56,613 times. A live NCBI retrieval
matched the frozen bacterial fixture. This is small-corpus computational evidence,
not biological validation, independent human review or a completed paper study.
Windows 0.2 was user-confirmed; v0.3 target-machine checks and remote CI evidence
are separate. Full machine-readable results and code/data hashes are provided.

## Histórico do CI remoto

A primeira execução remota, commit `349a231`, confirmou os testes do núcleo
em Windows, mas falhou no script de interface ao ler SVG UTF-8 com a codificação
padrão cp1252. A leitura do verificador foi corrigida para UTF-8 explícito;
o aplicativo já exportava o arquivo em UTF-8. O validador científico também
passou a declarar UTF-8 ao ler os fixtures e o manifesto. Não houve alteração
no motor, nos dados ou nas tolerâncias numéricas.
Execução original: https://github.com/BrunoJimez/BioForma/actions/runs/38117969544
A execução após a correção deve ser conferida em Actions; não presumir aprovação.

A segunda execução (commit `8a98e14`, run 38118075402) passou nos seis jobs:
interface/núcleo em Windows e Linux com Python 3.10/3.12 e validação independente
os dois sistemas. Ao conferir os artifacts, os hashes das dependências textuais
e do manifesto no Windows diferiram apenas pela conversão Git de LF para CRLF.
Foi verificado que a conversão explica exatamente cada diferença. Os fixtures
biológicos continuaram byte a byte iguais e todos os critérios passaram.
Para padronizar a rastreabilidade, `.gitattributes` agora fixa JSON/TXT em LF;
relatórios originais baixados do CI são preservados sem conversão. Os cálculos
e critérios permanecem iguais. O relatório Windows dessa execução fica em
`validacao/results_v0.3.0_windows_ci_initial.json`; o arquivo final é gerado
pela execução após a padronização.
