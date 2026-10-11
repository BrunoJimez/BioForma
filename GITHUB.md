# BioForma no GitHub

Repositório público: https://github.com/BrunoJimez/BioForma

A versão 0.3 é enviada depois de passar no protocolo local `validacao/PROTOCOL.md`,
na comparação independente, nos testes do núcleo e no fluxo nativo Linux PT/EN.
A publicação dessa versão de desenvolvimento não certifica validade biológica.
`VALIDACAO.md` distingue evidências locais, relato do usuário e testes remotos.

## Reproduzir

```sh
git clone https://github.com/BrunoJimez/BioForma.git
cd BioForma
python -m unittest discover -s tests -v
python -m pip install -r requirements-validation.txt
python scripts/validate_independent.py --output local-results/independent.json
python verificar_interface.py
```

O último comando exige display; no Linux CI, usa Xvfb. O CI prepara testes do
núcleo/interface em Windows e Linux com Python 3.10/3.12 e comparação científica
com Python 3.12. Resultados das execuções ficam na aba Actions.
O workflow de build nativo é manual e não cria release automaticamente.

Não versionar projetos privados, credenciais, ambientes ou resultados locais
exploratórios. O relatório congelado em `validacao/` documenta apenas os testes
medidos desta versão. Relatórios posteriores do CI ficam nos artifacts da execução.

Um futuro paper e depósito arquivado com DOI exigem um estudo concluído e estão
descritos em `docs/RESEARCH_ROADMAP.md`. Ainda não foram publicados.
