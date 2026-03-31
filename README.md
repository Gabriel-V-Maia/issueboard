<p align="center">
  <img src="assets/icon_png.png" width="212" />
</p>




<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue">
  <img src="https://img.shields.io/badge/status-active-success">
  <img src="https://img.shields.io/badge/platform-desktop-lightgrey">
  <img src="https://img.shields.io/badge/gui-customtkinter-informational">
  <img src="https://img.shields.io/badge/license-MIT-green">
  <img src="https://img.shields.io/github/v/release/Gabriel-V-Maia/issueboard">
</p>


Kanban desktop para acompanhar TODOs e WIPs distribuídos entre repositórios no GitHub.

O issueboard é uma aplicação desktop construída em Python com customtkinter que autentica via GitHub (Device Flow OAuth) e organiza issues em um board Kanban de três colunas.

---

## Features

- Autenticação com GitHub via Device Flow OAuth
- Cache de Issues já coletados (5m)
- Board Kanban com colunas: Open, In Progress, Done
- Agregação de issues de múltiplos repositórios
- Busca por padrões comuns: TODO, WIP, FIXME e labels
- Classificação automática de issues
- Interface desktop simples e direta
- Abertura rápida da issue no GitHub
- Marcação manual de "In Progress" em tempo de execução
- Carregamento assíncrono com threads

---

### Autenticação

O login é feito usando o fluxo de dispositivo do GitHub:

1. O usuário inicia o login
2. O app solicita um device_code ao GitHub
3. O usuário autoriza via navegador
4. O app faz polling até receber o token
5. O token é salvo localmente

---

### Coleta de Issues

O sistema realiza múltiplas queries na API do GitHub para identificar tarefas relevantes:

- Issues abertas com label "todo"
- Issues abertas com label "wip"
- Issues com "TODO", "WIP", "FIXME" no título
- Issues fechadas com esses mesmos padrões

Os resultados são:

- Agregados
- Deduplicados por ID
- Convertidos em objetos internos (`Issue`)

---

### Classificação

As issues são distribuídas em três colunas com base na seguinte lógica:

- `Done`: issues com estado `closed`
- `In Progress`:
  - IDs presentes em `wip_ids` (estado em memória)
  - Labels como `wip`, `doing`, `in progress`
- `Open`: todas as demais

Observação: `wip_ids` é resetado a cada refresh.

---

### Interface

A UI é composta por:

- Tela de login
- Board principal com:
  - Top bar (filtros, refresh, logout)
  - Barra de progresso
  - Três colunas Kanban
- Cards clicáveis para abrir detalhes
- Janela de detalhes com ações:
  - Abrir no GitHub
  - Marcar como "In Progress"

---

## Fluxo de Dados

1. A API do GitHub retorna JSON
2. Os dados são convertidos em objetos `Issue`
3. O board classifica os dados
4. As colunas renderizam os cards
5. Interações do usuário atualizam o estado local

---
## Configs

**Arquivos de configs são guardados em ``~/.issueboard/config.json``**

---

# Licença 
[MIT](https://github.com/Gabriel-V-Maia/issueboard/blob/main/LICENSE)
