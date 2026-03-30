\# issueboard — Architecture



issueboard is a desktop kanban app built with Python and customtkinter that authenticates with GitHub via device flow OAuth and surfaces TODO/WIP issues into a three-column board.



\---



\## Package Structure



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

&#x20;   └── icon.ico

```



\---



\## Module Dependency Graph



```mermaid

graph TD

&#x20;   main --> app

&#x20;   app --> config

&#x20;   app --> login

&#x20;   app --> board

&#x20;   login --> colors

&#x20;   login --> config

&#x20;   login --> auth

&#x20;   board --> colors

&#x20;   board --> config

&#x20;   board --> api

&#x20;   board --> column

&#x20;   board --> detail

&#x20;   column --> colors

&#x20;   column --> card

&#x20;   card --> colors

&#x20;   card --> models

&#x20;   detail --> colors

&#x20;   detail --> models

&#x20;   api --> models

```



\---



\## Authentication Flow



```mermaid

sequenceDiagram

&#x20;   actor User

&#x20;   participant App

&#x20;   participant GitHub



&#x20;   User->>App: click Login with GitHub

&#x20;   App->>App: choose scope public or private

&#x20;   App->>GitHub: POST /login/device/code

&#x20;   GitHub-->>App: device\_code + user\_code + verification\_uri

&#x20;   App->>User: show user\_code and open browser

&#x20;   User->>GitHub: visit verification\_uri enter code and authorize



&#x20;   loop poll every N seconds

&#x20;       App->>GitHub: POST /login/oauth/access\_token

&#x20;       GitHub-->>App: authorization\_pending or token

&#x20;   end



&#x20;   App->>App: save token to config.json

&#x20;   App->>App: navigate to BoardScreen

```



\---



\## Issue Fetching Flow



```mermaid

flowchart TD

&#x20;   A\[BoardScreen.\_load] --> B\[Thread \_load\_user]

&#x20;   A --> C\[Thread \_load\_issues]

&#x20;   B --> D\[GET /user]

&#x20;   D --> E\[show login in topbar]

&#x20;   C --> F\[fetch\_todo\_issues]

&#x20;   F --> G\[9 search queries]

&#x20;   G --> G1\[label todo is open]

&#x20;   G --> G2\[label wip is open]

&#x20;   G --> G3\[TODO in title is open]

&#x20;   G --> G4\[WIP in title is open]

&#x20;   G --> G5\[FIXME in title is open]

&#x20;   G --> G6\[TODO in title is closed]

&#x20;   G --> G7\[WIP in title is closed]

&#x20;   G1 \& G2 \& G3 \& G4 \& G5 \& G6 \& G7 --> H\[deduplicate by id]

&#x20;   H --> I\[list of Issue objects]

&#x20;   I --> J\[\_on\_loaded]

&#x20;   J --> K\[\_render and classify into columns]

```



\---



\## Issue Classification Logic



```mermaid

flowchart TD

&#x20;   A\[Issue] --> B{state is closed?}

&#x20;   B -- yes --> Done

&#x20;   B -- no --> C{id in wip\_ids?}

&#x20;   C -- yes --> InProgress\[In Progress]

&#x20;   C -- no --> D{label is wip or doing or in progress?}

&#x20;   D -- yes --> InProgress

&#x20;   D -- no --> Open

```



`wip\_ids` is an in-memory set managed by the user clicking Mark In Progress in the DetailWindow. It resets on refresh.



\---



\## UI Component Hierarchy



```mermaid

graph TD

&#x20;   App --> LoginScreen

&#x20;   App --> BoardScreen

&#x20;   LoginScreen --> ScopeSelector\[Scope selector radio buttons]

&#x20;   LoginScreen --> WaitingView\[Waiting view user\_code display]

&#x20;   BoardScreen --> TopBar\[Top bar filter refresh logout]

&#x20;   BoardScreen --> ProgressBar

&#x20;   BoardScreen --> KanbanBoard\[Kanban board 3 columns]

&#x20;   KanbanBoard --> ColOpen\[KanbanColumn Open]

&#x20;   KanbanBoard --> ColWIP\[KanbanColumn In Progress]

&#x20;   KanbanBoard --> ColDone\[KanbanColumn Done]

&#x20;   ColOpen \& ColWIP \& ColDone --> IssueCard

&#x20;   IssueCard -- click --> DetailWindow

&#x20;   DetailWindow --> OpenGitHub\[Open on GitHub]

&#x20;   DetailWindow --> ToggleWIP\[Mark In Progress or Move to Open]

```



\---



\## Data Flow



```mermaid

flowchart LR

&#x20;   GH\[GitHub API] -->|JSON| api\[github/api.py]

&#x20;   api -->|Issue objects| board\[BoardScreen]

&#x20;   board -->|classify| cols\[KanbanColumn x3]

&#x20;   cols -->|render| cards\[IssueCard xN]

&#x20;   cards -->|click| detail\[DetailWindow]

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



The token is written after successful device flow authorization and read on startup to skip the login screen. Logout deletes the token key.



\---



\## Build and Release



```mermaid

flowchart LR

&#x20;   src\[main.py + issueboard/] --> pyinstaller\[PyInstaller]

&#x20;   pyinstaller --> exe\[issueboard.exe]

&#x20;   exe --> release\[GitHub Release vX.Y.Z]

```



Build command:



```bash

pyinstaller --onefile --noconsole --icon=assets/icon.ico --name=issueboard main.py

```



Output is at `dist/issueboard.exe`.

