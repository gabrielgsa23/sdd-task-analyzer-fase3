# CONTEXT_RULES — Regras de Governança para Agentes de IA

Estas regras são a fundação de governança do projeto **TaskAnalyzer** (Bootcamp III).
Todo assistente de IA que gerar ou alterar código neste repositório deve receber este arquivo
e o `specs/system_design_document.pdf` como contexto e segui-los integralmente.

## 1. Diretrizes arquiteturais (obrigatórias)

- **Versão do ambiente:** código compatível com e escrito para **Python 3.11 ou superior**.
- **Tipagem estática:** type hints em **100%** das assinaturas de funções, métodos e variáveis complexas.
- **Clean Code:** princípio da Responsabilidade Única (SRP) e PEP 8. Funções atômicas, pequenas e coesas.
- **Documentação:** docstrings formais no **Google style** para módulos, classes, funções e parâmetros.
- **Observabilidade:** logs estruturados com o módulo padrão `logging`. Não usar `print()`.
- **Resiliência:** tratamento de exceções granular, capturando erros específicos (nunca `except Exception` amplo),
  com mensagens autoexplicativas.

## 2. Proibições explícitas

1. **NÃO** importar bibliotecas externas de terceiros para a lógica. Usar apenas a biblioteca padrão
   (`pytest` é permitido exclusivamente como framework de testes).
2. **NÃO** alterar, adaptar ou remover os critérios dos cenários de teste da especificação.
3. **NÃO** modificar a árvore de pastas predefinida.
4. **NÃO** injetar persistência (escrita em arquivos físicos ou bancos de dados). O foco é análise em memória.
5. **NÃO** refatorar ou renomear a assinatura dos métodos/funções públicos sem deliberação e autorização humana.
   Assinatura pública atual: `analyze_tasks(tasks)` e a exceção `TaskValidationError`.
6. **NÃO** gerar features sem os respectivos testes unitários.
7. **NÃO** inserir lógica duplicada, dead code ou assumir comportamentos de negócio que não constem no contrato SDD.

## 3. Homologação humana (gates obrigatórios antes do merge)

1. **Verificação funcional:** `pytest` com 100% de aprovação.
2. **Auditoria de contrato:** conferir aderência ao contrato SDD e a este arquivo.
3. **Análise estática de qualidade:** legibilidade, manutenibilidade, tratamento de erros, PEP 8.
4. **Avaliação de bordas:** testes manuais adicionais em edge cases.
5. **Merge e versionamento:** somente após o aval humano em todos os pontos acima. A decisão final é sempre humana.
