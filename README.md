# Semantic Agent - Workflow Automation with Semantic Kernel

This project is a high-performance automation agent built using **Microsoft Semantic Kernel**, **FastAPI**, and **Pydantic**. It is designed to orchestrate complex data processing workflows—Assessment, Parsing, and Mapping—either for single items or in batch mode via a queue system.

## 🚀 Key Features

* **Workflow Orchestration**: Enforces a strict linear process: `Assessment` → `Parsing` → `Mapping`.
* **Batch Processing**: Handles multiple `project_id` and `workbook_id` pairs simultaneously using a specialized Queue Plugin.
* **Semantic Kernel Integration**: Uses an AI-driven approach to select tools and manage chat history.
* **External API Integration**: Connects with OpenRouter for LLM services and multiple microservices for data processing.
* **Centralized Logging**: Automatically logs all batch execution results and errors to a MongoDB-backed logging API.

## 🛠 Project Structure

* **`main.py`**: The entry point; defines FastAPI endpoints for chat-based interaction (`/chat`) and direct batch processing (`/invoke-batch`).
* **`kernel/kernel_setup.py`**: Configures the Semantic Kernel, sets up the AI service via OpenRouter, and registers the plugins.
* **`plugins/`**: Contains the core logic for the agent's capabilities:
    * **`assessment.py`**: Validates project and workbook IDs via an assessment API.
    * **`parsing.py`**: Handles XML data parsing requests.
    * **`mapping.py`**: Manages data mapping operations.
    * **`queue_handler.py`**: Orchestrates sequential execution for batch requests and logs results to MongoDB.
* **`config/`**:
    * **`settings.py`**: Manages environment variables and API endpoints using Pydantic Settings.
    * **`prompts.py`**: Defines the `SYSTEM_PROMPT` that governs the agent's behavior and workflow rules.
* **`models/schemas.py`**: Defines Pydantic models for request and response validation, including Queue and Chat schemas.
* **`services/http_client.py`**: Provides a shared, optimized `httpx.AsyncClient` for all outgoing API calls.

## 📋 Prerequisites

* Python 3.10+
* An OpenRouter API Key
* Access to the required microservices (Assessment, Parsing, Mapping, and MongoDB Log APIs)

## ⚙️ Setup

1.  **Clone the repository.**
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Includes `fastapi`, `semantic-kernel`, `httpx`, and `pydantic-settings`)*.
3.  **Configure Environment Variables**: Create a `.env` file in the root directory (excluded by `.gitignore`) with the following keys:
    ```env
    OPENROUTER_API_KEY=your_key_here
    OPENROUTER_BASE_URL=[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)
    ASSESSMENT_API_URL=http://your-service-url
    PARSING_API_URL=http://your-service-url
    MAPPING_API_URL=http://your-service-url
    MONGODB_LOG_API_URL=http://your-log-service-url
    REQUEST_TIMEOUT=60.0
    ```
    *(Refer to `config/settings.py` for all required fields)*.

## 🚀 Running the Application

Start the server using Uvicorn:
```bash
python main.py

The API will be available at http://0.0.0.0:9000.

🔌 API Endpoints
1. Batch Invocation (/invoke-batch)
Directly triggers the processing queue for multiple items without going through the LLM.

Method: POST

Payload:

JSON

{
  "items": [
    {"project_id": "uuid1", "workbook_id": "uuid2"},
    {"project_id": "uuid3", "workbook_id": "uuid4"}
  ]
}
2. AI Chat (/chat)
Engage with the agent using natural language. The agent will decide whether to run a single workflow or a batch queue based on your input.

Method: POST

Payload: {"message": "Process these projects..."}

3. Health Check (/health)
Returns the status of the kernel and conversation history.

🤖 Workflow Logic
The agent follows a strict execution policy defined in the system prompt:

Single Item: Sequentially calls run_assessment → parse_xml_data → run_mapping.

Lists/Arrays: Extracts all IDs and delegates the entire batch to the process_items_queue tool in QueuePlugin to ensure efficiency and automated logging.  