\# issueboard — Architecture



issueboard is a desktop kanban app built with Python and customtkinter that authenticates with GitHub via device flow OAuth and surfaces TODO/WIP issues into a three-column board.



\---



\## Package Structure



```

issueboard/

├── main.py                  # entry point

├── issueboard/

│   ├── app.py               # App root window, screen routing

│   ├── config.py            # load/save config (\~/.issueboard/config.json)

│   ├── models.py            # Issue dataclass

│   ├── github/

│   │   ├── auth.py          # device flow OAuth

│   │   └── api.py           # GitHub REST API calls

│   └── ui/

│       ├── colors.py        # COLORS dict, label\_color(), btn() helper

│       ├── login.py         # LoginScreen

│       ├── board.py         # BoardScreen

│       ├── column.py        # KanbanColumn

│       ├── card.py          # IssueCard

│       └── detail.py        # DetailWindow

├── assets/

&#x20;    └── icon.ico

```



\---



\## Module Dependency Graph



```mermaid

graph TD

&#x20;   main\["main.py"] --> app\["app.py"]



&#x20;   app --> config\["config.py"]

&#x20;   app --> login\["ui/login.py"]

&#x20;   app --> board\["ui/board.py"]



&#x20;   login --> colors\["ui/colors.py"]

&#x20;   login --> config

&#x20;   login --> auth\["github/auth.py"]



&#x20;   board --> colors

&#x20;   board --> config

&#x20;   board --> api\["github/api.py"]

&#x20;   board --> column\["ui/column.py"]

&#x20;   board --> detail\["ui/detail.py"]



&#x20;   column --> colors

&#x20;   column --> card\["ui/card.py"]



&#x20;   card --> colors

&#x20;   card --> models\["models.py"]



&#x20;   detail --> colors

&#x20;   detail --> models



&#x20;   api --> models

```



\---



\## Authentication Flow (Device Flow OAuth)



```mermaid

sequenceDiagram

&#x20;   actor User

&#x20;   participant App

&#x20;   participant GitHub



&#x20;   User->>App: click "Login with GitHub"

&#x20;   App->>App: choose scope (public / private)

&#x20;   App->>GitHub: POST /login/device/code

&#x20;   GitHub-->>App: device\_code + user\_code + verification\_uri



&#x20;   App->>User: show user\_code + open browser

&#x20;   User->>GitHub: visit verification\_uri, enter code, authorize



&#x20;   loop poll every N seconds

&#x20;       App->>GitHub: POST /login/oauth/access\_token

&#x20;       GitHub-->>App: authorization\_pending / token

&#x20;   end



&#x20;   App->>App: save token to \~/.issueboard/config.json

&#x20;   App->>App: navigate to BoardScreen

```



\---



\## Issue Fetching Flow



```mermaid

flowchart TD

&#x20;   A\[BoardScreen.\_load] --> B\[Thread: \_load\_user]

&#x20;   A --> C\[Thread: \_load\_issues]



&#x20;   B --> D\[GET /user]

&#x20;   D --> E\[show @login in topbar]



&#x20;   C --> F\[fetch\_todo\_issues]

&#x20;   F --> G{9 search queries}



&#x20;   G --> G1\["label:todo is:open"]

&#x20;   G --> G2\["label:wip is:open"]

&#x20;   G --> G3\["TODO in:title is:open"]

&#x20;   G --> G4\["WIP in:title is:open"]

&#x20;   G --> G5\["FIXME in:title is:open"]

&#x20;   G --> G6\["TODO in:title is:closed"]

&#x20;   G --> G7\["... etc"]



&#x20;   G1 \& G2 \& G3 \& G4 \& G5 \& G6 \& G7 --> H\[deduplicate by id]

&#x20;   H --> I\[list of Issue objects]

&#x20;   I --> J\[\_on\_loaded]

&#x20;   J --> K\[\_render → classify into columns]

```



\---



\## Issue Classification Logic



```mermaid

flowchart TD

&#x20;   A\[Issue] --> B{state == closed?}

&#x20;   B -- yes --> Done

&#x20;   B -- no --> C{id in wip\_ids?}

&#x20;   C -- yes --> InProgress\["In Progress"]

&#x20;   C -- no --> D{label in wip/doing/in progress?}

&#x20;   D -- yes --> InProgress

&#x20;   D -- no --> Open

```



`wip\_ids` is an in-memory set managed by the user clicking "Mark In Progress" in the `DetailWindow`. It resets on refresh.



\---



\## UI Component Hierarchy



```mermaid

graph TD

&#x20;   App\["App (CTk root)"]

&#x20;   App --> LoginScreen

&#x20;   App --> BoardScreen



&#x20;   LoginScreen --> ScopeSelector\["Scope selector\\n(radio buttons)"]

&#x20;   LoginScreen --> WaitingView\["Waiting view\\n(user\_code display)"]



&#x20;   BoardScreen --> TopBar\["Top bar\\n(filter, refresh, logout)"]

&#x20;   BoardScreen --> ProgressBar

&#x20;   BoardScreen --> KanbanBoard\["Kanban board (3 columns)"]



&#x20;   KanbanBoard --> Open\["KanbanColumn: Open"]

&#x20;   KanbanBoard --> InProgress\["KanbanColumn: In Progress"]

&#x20;   KanbanBoard --> Done\["KanbanColumn: Done"]



&#x20;   Open \& InProgress \& Done --> IssueCard

&#x20;   IssueCard -- click --> DetailWindow



&#x20;   DetailWindow --> OpenGitHub\["Open on GitHub ↗"]

&#x20;   DetailWindow --> ToggleWIP\["Mark In Progress / Move to Open"]

```



\---



\## Data Flow



```mermaid

flowchart LR

&#x20;   GH\["GitHub API"] -->|JSON| api\["github/api.py"]

&#x20;   api -->|Issue objects| board\["BoardScreen"]

&#x20;   board -->|classify| cols\["KanbanColumn × 3"]

&#x20;   cols -->|render| cards\["IssueCard × N"]

&#x20;   cards -->|click| detail\["DetailWindow"]

&#x20;   detail -->|toggle wip| board

&#x20;   board -->|re-render| cols

```



\---



\## Config File



Stored at `\~/.issueboard/config.json`:



```json

{

&#x20; "token": "gho\_xxxxxxxxxxxxxxxxxxxx"

}

```



The token is written after successful device flow authorization and read on app startup to skip the login screen on subsequent launches. Logout deletes the token key.



\---



\## Build \& Release



```mermaid

flowchart LR

&#x20;   src\["Source\\n(main.py + issueboard/)"]

&#x20;   spec\["issueboard.spec"]

&#x20;   pyinstaller\["PyInstaller"]

&#x20;   exe\["issueboard.exe\\n(single binary)"]

&#x20;   release\["GitHub Release\\n(tag vX.Y.Z)"]



&#x20;   src --> pyinstaller

&#x20;   spec --> pyinstaller

&#x20;   pyinstaller --> exe

&#x20;   exe --> release

```



Build command:



```bash

pyinstaller --onefile --noconsole --icon=assets/icon.ico --name=issueboard main.py

```



Output is at `dist/issueboard.exe`. The spec is configured with `console=False` (no terminal window) and bundles the icon from `assets/icon.ico`.

