# ⚙️ Setup Guide

This guide will walk you through installing and running the Turnstile Solver API.

---

# Requirements

Before starting, ensure you have:

* Python 3.10+
* Git
* Windows, Linux, or macOS

Verify Python installation:

```bash
python --version
```

Expected output:

```text
Python 3.10+
```

---

# Clone the Repository

```bash
git clone https://github.com/zkamo/turnstile-solver.git
cd turnstile-solver
```

---

# Create a Virtual Environment

Creating a virtual environment is recommended to keep dependencies isolated.

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

After activation, your terminal should display:

```text
(venv)
```

---

# Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

---

# Configure the Server

```text
config.json
```

Example configuration:

```json
{
  "pool_size": 3,
  "headless": true,
  "solve_timeout": 45,
  "host": "127.0.0.1",
  "port": 8080
}
```

### Configuration Options

| Setting       | Description                   |
| ------------- | ----------------------------- |
| pool_size     | Number of persistent browsers |
| headless      | Run browsers without GUI      |
| solve_timeout | Maximum solve time in seconds |
| host          | API bind address              |
| port          | API bind port                 |

---

# Start the API

Launch the server:

```bash
python server.py
```

You should see output similar to:

```text
[INFO] Browser pool initialized
[INFO] API listening on 127.0.0.1:8080
```

---

# Verify Installation

Open your browser and visit:

```text
http://127.0.0.1:8080/health
```

Expected response:

```json
{
  "status": "ok",
  "poolSize": 3,
  "queueDepth": 0,
  "activeTasks": 0
}
```

---

# Quick Test

Submit a solve task:

```bash
curl -X POST http://127.0.0.1:8080/solve \
-H "Content-Type: application/json" \
-d '{
  "sitekey":"SITE_KEY",
  "site":"https://example.com"
}'
```

Example response:

```json
{
  "taskId": "a1b2c3d4",
  "status": "processing"
}
```

Check task status:

```bash
curl http://127.0.0.1:8080/tasks/a1b2c3d4
```

---

# Troubleshooting

## Camoufox Fails to Launch

Ensure all browser dependencies are installed and your system supports browser automation.

Try running with:

```json
{
  "headless": false
}
```

to view browser errors.

---

## Port Already In Use

Change the port in `config.json`:

```json
{
  "port": 8081
}
```

---

## Slow Solves

Increase the browser pool size:

```json
{
  "pool_size": 5
}
```

Higher values allow more concurrent solve operations.

---

# Updating

Pull the latest changes:

```bash
git pull
```

Update dependencies:

```bash
pip install -U -r requirements.txt
```

Restart the server after updating.

---

# Next Steps

Once setup is complete, see:

* README.md → Project overview
* Configuration → Tuning options