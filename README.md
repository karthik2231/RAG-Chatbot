# 📄 VectorDoc — Local RAG PDF Chatbot

A private, local AI chatbot that lets you upload PDF documents and ask questions about them. Answers include exact page numbers and quotes from your documents.

Everything runs **100% locally on your computer** using [Ollama](https://ollama.com/) — no API keys or internet connection required!

---

## ✨ Features

- **🔒 100% Private & Local**: Your documents and questions never leave your computer.
- **📄 Chat with any PDF**: Upload multiple PDFs and ask questions across all of them or just selected ones.
- **🎯 Accurate Citations**: Every answer shows the source document name, page number, and relevant excerpt.
- **💾 Conversation History**: Saves your past chats so you can continue conversations anytime.
- **⏹️ Stop Generating Anytime**: Easily stop long responses with one click.
- **🌙 Clean Dark Mode**: A fast, distraction-free modern interface.

---

## 🚀 Quick Start (Docker)

The fastest way to get started is using Docker Desktop.

### 1. Copy the environment file
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

### 2. Start the application
```bash
docker compose up --build -d
```

> **Note**: On the first run, it will automatically download the local AI model (`llama3.2:1b`). This may take a few minutes depending on your internet connection.

### 3. Open in your browser
- **Frontend App**: [http://localhost:5173](http://localhost:5173)
- **Backend API & Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧠 How It Works (In 4 Simple Steps)

```mermaid
flowchart LR
    A[📄 Upload PDF] --> B[✂️ Split into Chunks]
    B --> C[🔍 Vector Search (FAISS)]
    C --> D[🤖 Local AI (Ollama)]
    D --> E[💬 Answer with Page Citations]
```

1. **Upload**: You upload a PDF document.
2. **Read & Split**: The system reads text page by page and splits it into small, readable chunks.
3. **Smart Search**: When you ask a question, the vector database (**FAISS**) finds the most relevant paragraphs from your PDFs.
4. **Answer**: The local AI (**Ollama**) reads those paragraphs and writes a clear answer with page numbers.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend (UI)"]
        UI["React + Vite Web App<br/>(Port 5173)"]
    end

    subgraph Backend ["Backend (API)"]
        API["FastAPI REST Server<br/>(Port 8000)"]
        Auth["JWT Security & Auth"]
        DocEngine["PyMuPDF Extraction & Text Chunking"]
        Embedder["Sentence-Transformers<br/>(all-MiniLM-L6-v2)"]
    end

    subgraph Storage ["Storage & Vector Database"]
        DB[("PostgreSQL<br/>(Users, Documents & Chat History)")]
        VectorStore[("FAISS Vector Store<br/>(Per-User Isolated Index)")]
    end

    subgraph Inference ["Local LLM Server"]
        Ollama["Ollama Inference Engine<br/>(llama3.2:1b Model)"]
    end

    UI <-->|REST API + JWT| API
    API --> Auth
    API <--> DB
    API --> DocEngine
    DocEngine --> Embedder
    Embedder --> VectorStore
    API <-->|Semantic Search (Top-K Chunks)| VectorStore
    API <-->|Prompt Context & Completion| Ollama
```

---

## 🛠️ Tech Stack

- **Frontend**: React, Vite, Tailwind CSS
- **Backend**: Python, FastAPI
- **Database**: PostgreSQL (for users, documents, and chat history)
- **Search & Embeddings**: FAISS & Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Local AI Model**: Ollama (`llama3.2:1b`)

---

## 💻 Manual Setup (Without Docker)

If you prefer to run services manually on your host machine:

<details>
<summary><b>Click to expand manual setup instructions</b></summary>

### 1. Start Ollama
Make sure Ollama is installed and running:
```bash
ollama run llama3.2:1b
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
cp ../.env.example .env

# Run database migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
</details>

---

## 📋 Common Commands

```bash
# View running status
docker compose ps

# View backend logs
docker compose logs -f backend

# View Ollama logs
docker compose logs -f ollama

# Stop all services
docker compose down
```

---

## ⚙️ Key Configuration (`.env`)

You can customize the most common settings in your `.env` file:

| Setting | Default | What it does |
| --- | --- | --- |
| `OLLAMA_MODEL` | `llama3.2:1b` | The AI model used for answering questions |
| `MAX_UPLOAD_SIZE_MB` | `25` | Maximum PDF file size allowed (in MB) |
| `TOP_K_RESULTS` | `5` | Number of document chunks to use for each answer |
| `JWT_SECRET_KEY` | *(random key)* | Secret key used for user login tokens |

---

