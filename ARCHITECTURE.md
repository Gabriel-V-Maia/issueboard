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

```mermaid
flowchart TD
    A[BoardScreen._load] --> B[Thread _load_user]
    A --> C[Thread _load_issues]
    B --> D[GET /user]
    D --> E[show login in topbar]
    C --> F[fetch_todo_issues]
    F --> G[9 search queries]
    G --> G1[label todo is open]
    G --> G2[label wip is open]
    G --> G3[TODO in title is open]
    G --> G4[WIP in title is open]
    G --> G5[FIXME in title is open]
    G --> G6[TODO in title is closed]
    G --> G7[WIP in title is closed]
    G1 & G2 & G3 & G4 & G5 & G6 & G7 --> H[deduplicate by id]
    H --> I[list of Issue objects]
    I --> J[_on_loaded]
    J --> K[_render and classify into columns]
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
    board -->|classify| cols[KanbanColumn x3]
    cols -->|render| cards[IssueCard xN]
    cards -->|click| detail[DetailWindow]
    detail -->|toggle wip| board
    board -->|re-render| cols
```

---

## Config File

Stored at `~/.issueboard/config.json`:

```json
{
  "token": "gho_xxxxxxxxxxxxxxxxxxxx"
}
```

The token is written after successful device flow authorization and read on startup to skip the login screen. Logout deletes the token key.

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
