# issueboard — Architecture

issueboard is a desktop kanban app built with Python and customtkinter that authenticates with GitHub via device flow OAuth and surfaces TODO/WIP issues into a three-column board.

---

## Package Structure
```
issueboard/
├── main.py
├── issueboard/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── github/
│   │   ├── auth.py
│   │   └── api.py
│   └── ui/
│       ├── colors.py
│       ├── login.py
│       ├── board.py
│       ├── column.py
│       ├── card.py
│       └── detail.py
└── assets/
    └── icon.ico
```

---

## Module Dependency Graph
```mermaid
graph TD
    main --> app
    app --> config
    app --> login
    app --> board
    login --> colors
    login --> config
    login --> auth
    board --> colors
    board --> config
    board --> api
    board --> column
    board --> detail
    column --> colors
    column --> card
    card --> colors
    card --> models
    detail --> colors
    detail --> models
    api --> models
```

---

## Authentication Flow
```mermaid
sequenceDiagram
    actor User
    participant App
    participant GitHub

    User->>App: click Login with GitHub
    App->>App: choose scope public or private
    App->>GitHub: POST /login/device/code
    GitHub-->>App: device_code + user_code + verification_uri
    App->>User: show user_code and open browser
    User->>GitHub: visit verification_uri enter code and authorize

    loop poll every N seconds
        App->>GitHub: POST /login/oauth/access_token
        GitHub-->>App: authorization_pending or token
    end

    App->>App: save token to config.json
    App->>App: navigate to BoardScreen
```

---

## Issue Fetching Flow

Cache uses a stale-while-revalidate strategy with a 5-minute TTL stored at `~/.issueboard/cache.json`.
```mermaid
flowchart TD
    A[BoardScreen._load] --> B{cache exists?}
    B -- no --> C[show progress bar]
    C --> D[Thread _load_user]
    C --> E[Thread _load_issues]
    B -- yes --> F{cache fresh?\nage < 5 min}
    F -- yes --> G[render from cache instantly]
    G --> Z[done]
    F -- no --> H[render from cache instantly]
    H --> I[Thread _load_user]
    H --> J[Thread _load_issues background]
    E & J --> K[fetch_todo_issues]
    K --> L[7 parallel search queries\nThreadPoolExecutor max_workers=4]
    L --> L1[label:todo is:open]
    L --> L2[label:wip is:open]
    L --> L3[TODO in:title is:open]
    L --> L4[WIP in:title is:open]
    L --> L5[FIXME in:title is:open]
    L --> L6[TODO in:title is:closed]
    L --> L7[WIP in:title is:closed]
    L1 & L2 & L3 & L4 & L5 & L6 & L7 --> M[deduplicate by id]
    M --> N[list of Issue objects]
    N --> O[save_cache to disk]
    O --> P[_on_loaded]
    P --> Q[_render and classify into columns]
```

---

## Issue Classification Logic
```mermaid
flowchart TD
    A[Issue] --> B{state is closed?}
    B -- yes --> Done
    B -- no --> C{id in wip_ids?}
    C -- yes --> InProgress[In Progress]
    C -- no --> D{label is wip or doing or in progress?}
    D -- yes --> InProgress
    D -- no --> Open
```

`wip_ids` is an in-memory set managed by the user clicking Mark In Progress in the DetailWindow. It resets on refresh.

---

## UI Component Hierarchy
```mermaid
graph TD
    App --> LoginScreen
    App --> BoardScreen
    LoginScreen --> ScopeSelector[Scope selector radio buttons]
    LoginScreen --> WaitingView[Waiting view user_code display]
    BoardScreen --> TopBar[Top bar filter refresh logout]
    BoardScreen --> ProgressBar
    BoardScreen --> KanbanBoard[Kanban board 3 columns]
    KanbanBoard --> ColOpen[KanbanColumn Open]
    KanbanBoard --> ColWIP[KanbanColumn In Progress]
    KanbanBoard --> ColDone[KanbanColumn Done]
    ColOpen & ColWIP & ColDone --> IssueCard
    IssueCard -- click --> DetailWindow
    DetailWindow --> OpenGitHub[Open on GitHub]
    DetailWindow --> ToggleWIP[Mark In Progress or Move to Open]
```

---

## Data Flow
```mermaid
flowchart LR
    GH[GitHub API] -->|JSON| api[github/api.py]
    api -->|Issue objects| board[BoardScreen]
    board -->|save| cache[(cache.json)]
    cache -->|instant render| board
    board -->|classify| cols[KanbanColumn x3]
    cols -->|render| cards[IssueCard xN]
    cards -->|click| detail[DetailWindow]
    detail -->|toggle wip| board
    board -->|re-render| cols
```

---

## Config Files

Both stored at `~/.issueboard/`:

**`config.json`** — authentication token, written after device flow and read on startup to skip login. Logout deletes the token key.
```json
{
  "token": "gho_xxxxxxxxxxxxxxxxxxxx"
}
```

**`cache.json`** — serialized issue list with timestamp. Written after every successful fetch. Read on startup for instant rendering before the API responds.
```json
{
  "ts": 1743000000.0,
  "issues": [
    {
      "id": 123456,
      "title": "TODO: fix thing",
      "url": "https://github.com/...",
      "state": "open",
      "labels": ["todo"],
      "repo": "owner/repo",
      "number": 42,
      "assignee": null,
      "created_at": "2025-01-01",
      "body": "..."
    }
  ]
}
```

---

## Build and Release
```mermaid
flowchart LR
    src[main.py + issueboard/] --> pyinstaller[PyInstaller]
    pyinstaller --> exe[issueboard.exe]
    exe --> release[GitHub Release vX.Y.Z]
```

Build command:
```bash
pyinstaller --onefile --noconsole --icon=assets/icon.ico --name=issueboard main.py
```

Output is at `dist/issueboard.exe`.
