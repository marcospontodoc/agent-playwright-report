# Contexto funcional do projeto: Hora do QA

## Finalidade e limites deste contexto

Hora do QA é uma aplicação web pública com páginas de login e criação de conta. Este contexto descreve somente o que foi possível observar nas páginas públicas consultadas. Os elementos e textos visíveis são evidência da interface apresentada; não comprovam o comportamento do servidor, regras de negócio adicionais, armazenamento de dados ou o resultado de uma autenticação.

Use este documento como referência contextual ao interpretar uma execução Playwright do projeto. Os resultados efetivamente observados devem vir do relatório daquela execução e, quando disponíveis, dos fontes de teste e de outras evidências. Não trate o nome de um teste ou um status aprovado isoladamente como comprovação de uma regra funcional específica.

## Identificação observada

- Nome exibido: **Hora do QA**.
- Descrição apresentada: **“Testar. Encontrar. Entender.”**
- A interface identifica o produto como **“QA_SYSTEM v1.0.0”** e exibe os indicadores **“STATUS: READY BUILD_001”** nas páginas consultadas. Esses textos são conteúdo visível da interface e não confirmam versão de implantação, estado operacional do backend ou ambiente da execução.
- URL pública consultada: [página de login](https://horadoqa.github.io/login/index.html).
- A página de criação de conta está disponível em [cadastro](https://horadoqa.github.io/login/pages/cadastro.html).

## Login — elementos visíveis

A página de login apresenta o título **“Entrar”**, a instrução **“Acesse seu espaço de testes.”**, campos identificados como **E-MAIL** e **SENHA**, e o botão **“Entrar”**. Também exibe um link **“Criar conta”** que direciona à página de cadastro.

Não foi confirmado por documentação ou interação o formato aceito para credenciais, as mensagens de sucesso ou erro, regras de validação, mecanismo de autenticação, destino após login, persistência da sessão ou conteúdo de uma área autenticada. Não presumir esses comportamentos ao avaliar falhas.

## Criação de conta — elementos visíveis

A página de cadastro apresenta o título **“Criar conta”**, a instrução **“Crie seu acesso ao espaço de testes.”**, campos identificados como **NOME COMPLETO**, **E-MAIL**, **SENHA** e **CONFIRMAR SENHA**, e o botão **“Criar conta”**. Um link **“Fazer login”** retorna à página de login.

Não foram confirmadas regras de obrigatoriedade, formato ou unicidade dos dados, requisitos de senha, validação de correspondência entre senha e confirmação, mensagens de retorno, persistência do cadastro ou fluxo posterior ao envio.

## Orientação para interpretar resultados Playwright

- Os nomes e rótulos dos elementos acima podem ajudar a contextualizar cenários, mas não demonstram quais campos ou fluxos foram cobertos.
- Um teste falho em login ou cadastro é uma falha de teste; só deve ser descrito como bug confirmado quando as evidências mostrarem uma divergência reproduzível em relação a um comportamento esperado documentado ou de outra forma confirmado.
- Na ausência de critérios de aceitação, fontes de teste ou evidências suficientes, descrever objetivamente o resultado observado e indicar que a falha precisa de investigação. Não inventar credenciais, regras, mensagens, severidades ou causas.
- A interface visualmente observada não permite afirmar a tecnologia de implementação, arquitetura, API utilizada nem a existência de páginas autenticadas adicionais.

## Informações não confirmadas

As páginas públicas não fornecem documentação funcional detalhada. Permanecem não confirmados: regras de negócio e critérios de aceitação; validações e mensagens esperadas; credenciais de teste; comportamento de sucesso e erro; permissões e recursos após autenticação; integrações e persistência; ambiente e versão efetiva da aplicação usada em cada execução. Usar somente dados fornecidos para a execução ou demonstrados por evidências pertinentes.

## Referências e escopo da consulta

Consulta visual das páginas públicas de login e cadastro em **20/10/2026**. Os campos e textos deste documento refletem o conteúdo apresentado nessas páginas no momento da consulta; não equivalem a uma especificação funcional completa.

- [Hora do QA — Login](https://horadoqa.github.io/login/index.html)
- [Hora do QA — Cadastro](https://horadoqa.github.io/login/pages/cadastro.html)
