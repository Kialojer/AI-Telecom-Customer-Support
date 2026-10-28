# Portfólio de Atendimento com Agentes para Telecomunicações

Projeto independente de portfólio educacional inspirado no atendimento ao cliente
no setor brasileiro de telecomunicações. Sem vínculo com a Claro ou a Vivo. Todos
os clientes, planos, preços e valores de faturas são fictícios. O projeto não inclui
credenciais nem números de telefone pessoais. Foi desenvolvido para apresentação
no GitHub e no currículo; a implantação não é necessária.

## Arquivos

| Arquivo | Finalidade |
| --- | --- |
| `architecture.drawio` | Arquitetura de alto nível (HLD) editável no diagrams.net, em XML sem compressão |
| `graph.py` | Classificação e fluxos de perguntas frequentes, faturamento, ofertas e suporte com LangGraph |
| `postgres.py` | Perfis fictícios aleatórios de clientes, DDL de referência e consulta SQL opcional |
| `main.py` | Entrada da demonstração com FastAPI e resposta JSON tipada |
| `requirements.txt` | Faixas de versões das dependências; não é um arquivo de versões fixadas (lockfile) |
| `VERIFICATION.md` | Versões verificadas em execução, resultados e limitações restantes |
| `tests/test_integration.py` | Testes de integração da API HTTP com o grafo, consentimento, contrato do adaptador e HLD |
| `requirements-dev.txt` | Dependências de execução e cliente HTTP para testes |
| `.github/workflows/tests.yml` | Verificações de integração com Python 3.11 e 3.13 |

## Arquitetura e escopo

1. A demonstração recebe uma mensagem por `POST /webhook/demo`.
2. `get_random_customer()` seleciona um dos três perfis fictícios.
3. O FastAPI passa os dados desse perfil ao fluxo compilado do LangGraph.
4. Um classificador simples por palavras-chave em português direciona a mensagem
   para perguntas frequentes, faturamento, ofertas ou suporte. A correspondência
   ignora acentos e diferenças entre maiúsculas e minúsculas, respeita os limites
   das palavras e aceita espaços em branco repetidos nas expressões. A prioridade
   é suporte, depois faturamento, ofertas e, por último, perguntas frequentes.
5. O grafo retorna uma resposta e, quando aplicável, uma fila simulada de
   encaminhamento para atendimento humano, em JSON.

Os nós do grafo não fazem consultas ao banco de dados. O adaptador opcional para
PostgreSQL usa uma consulta parametrizada e fica separado do fluxo padrão com
dados fictícios. O DDL está definido em `postgres.py`; nenhuma tabela é criada
automaticamente.

O fluxo de ofertas exige consentimento explícito de marketing, com o valor
booleano `True`, em cada requisição, antes de acessar o cache do catálogo.
Consentimento ausente ou em formato inválido impede a apresentação de ofertas.
O fluxo usa um cache limitado na aplicação para textos de catálogo previamente
carregados, com chaves formadas pelos interesses e pela versão do catálogo. Isso
ilustra uma forma de reutilização de contexto inspirada em CAG. Não há chamadas
a LLMs, contagem de tokens, cache de prompts/KV de provedores, embeddings, banco
vetorial nem memória persistente de conversas. Portanto, esta demonstração não
apresenta economia medida de tokens nem geração de conteúdo por IA. Alterar
`CATALOGUE_VERSION` faz com que novas chaves de cache sejam usadas; reiniciar a
aplicação também limpa o cache.

Cada requisição seleciona um novo perfil aleatório. Não há identificação da
conversa nem histórico entre requisições. O encaminhamento do suporte é indicado
por um campo na resposta; não cria um chamado nem transfere a conversa para um
atendente real. O faturamento apenas lê os dados fictícios do perfil recebido.

## Abrir o HLD editável

Acesse [diagrams.net](https://app.diagrams.net/) e escolha
**File > Open From > Device** (Arquivo > Abrir de > Dispositivo). Em seguida,
selecione `architecture.drawio`. As formas, os rótulos e os conectores são editáveis.
Setas contínuas representam os fluxos implementados na demonstração. Caixas e
setas tracejadas representam integrações opcionais ou futuras, incluindo WhatsApp
e PostgreSQL.

## Revisar sem executar

Abra o diagrama e os três arquivos Python no GitHub ou em um editor. A API e o
grafo compilado foram testados no mesmo processo, com dados fictícios. Não foram
verificadas a implantação, uma conexão real com PostgreSQL ou a integração com
WhatsApp. Consulte `VERIFICATION.md` para conhecer o escopo exato das verificações.

## Demonstração local

Use Python 3.11 ou superior em um ambiente virtual. Na pasta do projeto:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Abra [a documentação local da API](http://127.0.0.1:8000/docs) e envie este corpo
para `POST /webhook/demo`:

```json
{"message": "Minha internet esta lenta, preciso de um atendente"}
```

Rota esperada: `support`, com `handoff: true` e `queue: "customer_service"`.
Experimente `Quero ver minha fatura` para faturamento, `Tem alguma oferta?` para
uma oferta (ou recusa por falta de consentimento) e `Ola` para a apresentação de
perguntas frequentes.

As faixas de versões das dependências indicam a compatibilidade pretendida;
não constituem um lockfile nem garantem que todas as combinações de versões
funcionem. As versões exatas testadas estão em `VERIFICATION.md`.

## Executar as verificações de integração

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

Os testes usam o cliente HTTP do FastAPI no mesmo processo e o grafo real compilado
do LangGraph. Para verificar faturamento, vendas e consentimento, selecionam os
perfis fictícios de forma determinística; um teste separado verifica a função
real de seleção aleatória. Os testes de contrato do adaptador PostgreSQL simulam
apenas a conexão, portanto não exigem credenciais de banco de dados. A integração
contínua (CI) executa esse comando com Python 3.11 e 3.13 após uma nova instalação
das dependências.

O suporte, incluindo problemas técnicos, cancelamento e pedidos para falar com
um atendente, sempre retorna um encaminhamento simulado. Na API JSON, `offer` é
a intenção correspondente a vendas. O consentimento vem dos dados do perfil do
cliente; a API não aceita nem persiste alterações de consentimento. O classificador
por palavras-chave é intencionalmente limitado e não interpreta livremente a
linguagem natural.

## Integração opcional com PostgreSQL

Para integrar o banco posteriormente, crie `portfolio_customers` usando
`SCHEMA_SQL`, insira registros fictícios, configure `DATABASE_URL` de forma privada
e chame `load_customer_from_postgres(customer_id)` antes de `respond(...)`.
Um identificador desconhecido retorna `None`, e o código que chama a função deve
tratar esse caso. Nunca inclua strings de conexão nos commits. O adaptador não
está exposto pelo endpoint HTTP da demonstração.

## Integração futura com WhatsApp

O endpoint JSON da demonstração não é um webhook da API do WhatsApp Cloud da Meta.
Um adaptador precisaria interpretar os payloads reais, responder ao desafio de
verificação, validar assinaturas, identificar clientes autenticados, eliminar
eventos duplicados e implementar o envio de mensagens pela API. Mantenha essas
responsabilidades fora do grafo. A consulta de faturas reais exige identidade
verificada e autorização; a demonstração com perfis aleatórios deve continuar
restrita a dados fictícios.

## Referências de projeto

- [API de grafos do LangGraph](https://reference.langchain.com/python/langgraph/graph)
- [Corpos de requisição no FastAPI](https://fastapi.tiangolo.com/tutorial/body/)
- [Uso básico do Psycopg](https://www.psycopg.org/psycopg3/docs/basic/usage.html)
- [Linhas como dicionários no Psycopg](https://www.psycopg.org/psycopg3/docs/advanced/rows.html)

## Texto sugerido para o currículo

Protótipo de portfólio de atendimento para telecomunicações com LangGraph,
FastAPI e adaptador PostgreSQL: roteamento por intenção, contexto de cliente
simulado, cache de ofertas e encaminhamento simulado para atendimento humano.
