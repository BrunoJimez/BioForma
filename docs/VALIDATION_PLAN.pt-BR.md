# Protocolo proposto de validação computacional

Status: **plano prospectivo**, preparado em 10/10/2026. Não é relato de estudo já executado.
Objeto: BioForma Studio como aplicativo educacional para sequências, coordenadas e modelos.

## Questões de pesquisa

1. As operações suportadas concordam com implementações de referência independentes?
2. O parser preserva as coordenadas do primeiro modelo PDB e a política declarada de conformações?
3. A solução analítica do circuito concorda com integração numérica independente?
4. Salvamento e troca de idioma preservam entradas e resultados?
5. Os usuários distinguem esquemas, coordenadas existentes e previsões de modelos?

## Congelamento e seleção

Escolher uma versão real, tag e commit. Arquivar fontes, dependências, fixtures e hashes.
Registrar Python, Tk, sistema, arquitetura, escala de tela e hardware. Usar os mesmos arquivos
nos dois idiomas e sistemas. Fixar regras de seleção e exclusão antes de observar os resultados.
Documentar desvios com data e motivo; não tratar decisões posteriores como prévias.

O corpus de sequências deve incluir DNA canônico, todos os 64 códons, fronteiras de quadros,
ambiguidades IUPAC, FASTA múltiplo, GenBank ORIGIN e casos explicitamente não suportados.
O corpus PDB deve conter arquivos públicos com procedência e termos de uso conhecidos,
múltiplos modelos/cadeias, altloc, TER, coordenadas ausentes e ausência de Cα.
Manter exemplos artificiais identificados e separar fixtures não usadas no desenvolvimento.
Definir tamanho e amostragem por metas de cobertura antes da execução. Não inventar número
de participantes ou alegar poder estatístico sem cálculo justificado.

## Comparadores independentes

Fixar uma versão do Biopython para importação/tradução, igualando código genético, quadro e
política de ambiguidade. O BioForma sempre devolve X para códon ambíguo; algumas ferramentas
resolvem parte dessas ambiguidades. Avaliar essa diferença pela política declarada.
GenBank é avaliado apenas para ORIGIN; preservação de anotações não é uma função implementada.

Para PDB, usar Biopython ou Gemmi com versão fixada e igualar primeiro modelo, altloc A/vazia
e identidade dos resíduos/átomos. Investigar discordâncias e comparar antes do corte do visor.
Defaults diferentes entre ferramentas não constituem automaticamente erros.

Para o circuito, usar solve_ivp ou RK4 implementado independentemente, incluindo degradações
iguais/quase iguais, produção nula, extremos lógicos, entradas intermediárias e fronteiras de taxas/tempo.
Registrar tolerâncias e conferir a convergência do comparador.

## Desfechos primários sugeridos, a fixar antes de executar

| Desfecho | Critério proposto |
|---|---|
| Importação/tradução canônica suportada | Igualdade exata de sequência e resultado |
| Validação de entrada | Aceitar casos suportados e rejeitar entradas inválidas/não suportadas explicitamente |
| Extração de coordenadas PDB | Identidades selecionadas iguais; erro de coordenada ≤ 0,001 Å |
| Circuito versus integração independente | Erro absoluto ≤ 1e-7 + 1e-6 × valor absoluto de referência; comparador convergido |
| Salvar/reabrir | Igualdade exata dos dados canônicos do projeto |
| Idiomas PT/EN | Resultados e hashes iguais para o mesmo projeto |

Esses critérios são propostas, não resultados demonstrados. Revisar e congelar antes de colher
o conjunto de validação. A tolerância PDB se refere à precisão do formato legado, não à validade
biológica. Relatar erros absolutos/relativos, contagens e falhas individuais.

## Desfechos secundários e interpretação

Medir tempos de abertura/importação/análise e memória em máquinas documentadas, com regra
de aquecimento e repetições previamente definida. Execuções na mesma máquina são observações
repetidas, não amostras biológicas independentes. Em testes determinísticos pequenos, contagens
exatas podem ser mais úteis do que valores-p sem hipótese justificada.

Para avaliação educacional, definir tarefas e rubrica antes de recrutar usuários. Medir se
interpretam hélice/circuito ilustrativos como previsão validada de organismo. Determinar requisitos
institucionais aplicáveis de ética e consentimento antes de envolver participantes.
Não alegar eficácia educacional apenas com demonstrações dos desenvolvedores.

## Escopo das alegações e materiais para artigo

Distinguir testes internos, validação independente, compatibilidade, usabilidade e calibração
biológica. Relatar somente etapas efetivamente realizadas. O software não contém modelo completo
genótipo-fenótipo, predição de dobramento, circuito calibrado experimentalmente ou protocolo de bancada.
O título, resumo e métodos de uma futura submissão devem refletir esse escopo.

Disponibilizar repositório/tag/commit, fonte arquivada, DOI somente quando efetivamente atribuído,
fixtures/licenças, protocolo, versões dos comparadores, tabelas CSV/JSON, inventário de falhas e
ambientes. Registros exportados ajudam a reproduzir, mas não certificam o estudo.
Descrever desenvolvimento assistido por IA conforme a política vigente do periódico escolhido.
Definir periódico, autoria e alegações a partir das evidências obtidas.

Referências primárias: NCBI genetic codes, wwPDB coordinate format, Biopython SeqIO,
Python/Tkinter e GitHub Python CI, com os links reunidos no README e no protocolo inglês.
