# Backend Architecture

FastAPI Layer

职责：

-   接收请求
-   调用NEMT Engine
-   返回JSON

结构：

backend/

main.py

routes/

services/

nemt_adapter/

未来：

FastAPI

↓

Authentication

↓

Database

↓

Execution Agent
