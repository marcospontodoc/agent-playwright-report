# Contexto funcional do projeto: ServeRest

## Finalidade e limites deste contexto

O ServeRest é uma API REST que simula uma loja virtual e se destina ao estudo de testes de API, conforme a documentação oficial. Este documento resume o comportamento que a documentação descreve para apoiar a interpretação dos relatórios Playwright.

As regras abaixo são **comportamento documentado**, não evidência de que uma execução específica as testou. Para concluir o que foi efetivamente coberto ou observado, consultar os títulos, resultados, mensagens, anexos e fontes de teste disponíveis para aquela execução. Um status aprovado do Playwright, sem asserções ou resposta capturada, não comprova por si só que uma regra funcional específica foi validada.

## Autenticação e login — comportamento documentado

- `POST /login` recebe `email` e `password`.
- A documentação descreve `200` para login bem-sucedido, com `message` e `authorization`, e `401` para e-mail e/ou senha inválidos.
- O valor de `authorization` deve ser enviado no cabeçalho `Authorization` para rotas protegidas. O valor normalmente tem o prefixo `Bearer`.
- O token tem duração padrão documentada de 600 segundos (10 minutos); token expirado resulta em `401`. A documentação informa opções de configuração do token para instâncias iniciadas via NPM. A configuração efetiva de uma execução precisa ser confirmada separadamente.
- Rotas de produtos para criação, edição e exclusão exigem token de usuário administrador (`administrador = true`). As operações de carrinho que alteram dados exigem autenticação, mas não exigem usuário administrador.
- Respostas documentadas para autenticação protegida incluem `401` para token ausente, inválido ou expirado; rotas administrativas podem retornar `403` para usuário não administrador.

## Usuários — comportamento documentado

| Método e rota | Comportamento e respostas descritos |
|---|---|
| `GET /usuarios` | Lista usuários; aceita filtros por `_id`, `nome`, `email`, `password` e `administrador`; resposta `200` contém `quantidade` e `usuarios`. |
| `GET /usuarios/{_id}` | Busca por ID; `200` para usuário encontrado e `400` com mensagem de usuário não encontrado. |
| `POST /usuarios` | Cadastra usuário com `nome`, `email`, `password` e `administrador`; `201` no cadastro e `400` quando o e-mail já está em uso. A documentação proíbe reutilizar e-mail. |
| `PUT /usuarios/{_id}` | Atualiza usuário (`200`); se o ID não for encontrado, a documentação diz que cria um novo (`201`). E-mail já utilizado resulta em `400`. |
| `DELETE /usuarios/{_id}` | `200` quando exclui ou quando nenhum registro é excluído; `400` quando o usuário tem carrinho cadastrado. |

A documentação modela `administrador` como string com valores `"true"` ou `"false"`. Não presumir uma validação de campos obrigatórios ou regras adicionais além das descritas no esquema e nas respostas publicadas.

## Produtos — comportamento documentado

| Método e rota | Comportamento e respostas descritos |
|---|---|
| `GET /produtos` | Lista produtos; aceita filtros por `_id`, `nome`, `preco`, `descricao` e `quantidade`; resposta `200` contém `quantidade` e `produtos`. A documentação especifica preço inteiro maior ou igual a 1 e quantidade inteira maior ou igual a 0 para os filtros correspondentes. |
| `GET /produtos/{_id}` | Busca por ID; `200` quando encontrado e `400` com mensagem de produto não encontrado. |
| `POST /produtos` | Requer token e usuário administrador. Campos exemplificados: `nome`, `preco`, `descricao` e `quantidade`. Retorna `201` ao cadastrar; `400` para nome já utilizado; `401` para token ausente/inválido/expirado; `403` para usuário sem permissão administrativa. |
| `PUT /produtos/{_id}` | Requer token e usuário administrador. Retorna `200` ao atualizar; se o ID não existir, a documentação descreve criação com `201`. Nome já utilizado resulta em `400`; erros de autenticação/permissão podem resultar em `401`/`403`. |
| `DELETE /produtos/{_id}` | Requer token e usuário administrador. Retorna `200` quando exclui ou quando nenhum registro é excluído; `400` quando o produto faz parte de carrinho; erros de autenticação/permissão podem resultar em `401`/`403`. |

## Carrinhos — comportamento documentado

| Método e rota | Comportamento e respostas descritos |
|---|---|
| `GET /carrinhos` | Lista carrinhos; aceita filtros por `_id`, `precoTotal`, `quantidadeTotal` e `idUsuario`; resposta `200`. A documentação diz que os carrinhos retornados são únicos por usuário. |
| `GET /carrinhos/{_id}` | Busca carrinho por ID; `200` quando encontrado e `400` com mensagem de carrinho não encontrado. |
| `POST /carrinhos` | Requer token, e o carrinho fica vinculado ao usuário desse token. Só pode haver um carrinho por usuário. A solicitação contém produtos com `idProduto` e `quantidade`. A documentação descreve `201` no cadastro; `400` para produto duplicado, mais de um carrinho, produto inexistente ou estoque insuficiente; `401` para token inválido/ausente/expirado. Ao cadastrar com sucesso, reduz o estoque dos produtos. |
| `DELETE /carrinhos/concluir-compra` | Requer token e exclui o carrinho associado ao usuário do token. `200` indica exclusão ou ausência de carrinho; `401` para token inválido/ausente/expirado. |
| `DELETE /carrinhos/cancelar-compra` | Requer token; exclui o carrinho associado ao usuário e repõe o estoque dos produtos. `200` indica exclusão ou ausência de carrinho; `401` para token inválido/ausente/expirado. |

## Relatório Playwright de exemplo — resultados e metadados observados

O único arquivo de execução encontrado no escopo do projeto é `docs/exemplo-playwright/report-test.html`. Ele contém resultados incorporados associados a cinco nomes de arquivo de especificação, com 63 resultados no total: 21 por projeto (`chromium`, `firefox` e `webkit`). O resumo do relatório marca os 63 como `expected`, com zero `unexpected`, `flaky` ou `skipped`.

Os nomes registrados e respectivas quantidades são metadados observados no relatório:

- `apiSetup.spec.ts`: 3 resultados.
- `login.spec.ts`: 18 resultados.
- `register.spec.ts`: 15 resultados.
- `registerProduct.spec.ts`: 24 resultados.
- `shopping-list.spec.ts`: 3 resultados.

Os títulos individuais também estão registrados no relatório, mas são rótulos e não evidência de asserções. Não se deve deduzir deles quais funcionalidades, endpoints, regras de negócio ou respostas foram testados, nem classificar a suíte como teste de interface, API ou outro tipo.

### Verificação de disponibilidade dos fontes

Foi feita uma busca recursiva em todos os arquivos visíveis do projeto, além de uma busca que inclui arquivos ocultos e ignorados por Git, procurando fontes de teste (`*.spec.*`, `*.test.*`), configuração Playwright e manifestos/dependências comuns. No escopo acessível do projeto foram encontrados apenas `AGENTS.md`, `docs/contexto-projeto.md`, `docs/exemplo-playwright/report-test.html` e `templates/modelo-relatorio.md`. Não foram encontrados fontes dos testes, configuração Playwright ou manifesto de dependências. Os nomes de especificação embutidos no relatório não substituem os arquivos fonte.

Assim, permanecem indisponíveis os passos executados, tipos de teste, chamadas e valores enviados, asserções, critérios de aceitação e correspondência entre mensagens esperadas e as respostas documentadas. O relatório de exemplo não contém teste com status de falha. Essa conclusão se limita ao escopo acessível do projeto verificado; não afirma que fontes não existam em outro local não acessível.

## Informações ainda pendentes por execução

Antes de atribuir contexto operacional ou interpretar cobertura, procurar nas fontes da execução ou solicitar ao responsável:

- versão/build do ServeRest efetivamente usado; a versão `3.2.2` exibida no documento OpenAPI consultado não confirma a versão do servidor da execução;
- URL/base URL e ambiente (online, local via NPM, Docker ou outro), incluindo configuração que afete autenticação, persistência ou dados;
- escopo planejado e critérios de aceitação específicos da suíte, além dos nomes dos testes;
- fontes dos testes, configuração Playwright e asserções, se a avaliação exigir comprovação funcional;
- identificação de quais testes são API, interface ou outro fluxo, quando isso não estiver explícito nas fontes;
- fuso horário pretendido para exibir horários, caso não possa ser determinado pela origem.

Não inferir esses dados a partir da documentação, do nome de uma especificação, do navegador do Playwright ou da URL da documentação.

## Referências documentais

Consulta realizada em **15/10/2026**. O documento OpenAPI oficial consultado exibe `info.version` **3.2.2**. Esse número identifica somente a versão informada naquele documento OpenAPI; não é uma versão confirmada do servidor usado em qualquer execução.

- [Documentação oficial ServeRest em português](https://serverest.dev/?lang=pt-BR)
- [Documento OpenAPI oficial (Swagger JSON)](https://serverest.dev/swagger.json?lang=pt-BR)
- [Repositório oficial ServeRest — informações de ambientes e projeto](https://github.com/ServeRest/ServeRest)
