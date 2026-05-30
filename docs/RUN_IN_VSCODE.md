# Run In VS Code

## 1. Open The Project

Open VS Code, then choose:

```text
File -> Open Folder
```

Select:

```text
C:\Users\ASUS\OneDrive\Desktop\UPI-Fraud-Risk-Intelligence-Platform
```

## 2. Run With Two Terminals

Open two terminals inside VS Code:

```text
Terminal -> New Terminal
```

### Terminal 1: Backend

```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

### Terminal 2: Frontend

```powershell
cd frontend
npm run dev
```

Dashboard URL:

```text
http://127.0.0.1:5173
```

## 3. Optional: Run With VS Code Tasks

Press:

```text
Ctrl + Shift + P
```

Search:

```text
Tasks: Run Task
```

Run these two tasks:

```text
Backend: run FastAPI
Frontend: run dashboard
```

If packages are missing, run:

```text
Backend: install requirements
Frontend: install packages
```
