# BPMN AI Agent

An AI-powered application that transforms natural-language business process requirements into structured BPMN 2.0 workflows using locally hosted language models and agentic AI.

## Overview

The BPMN AI Agent simplifies business process modeling by allowing users to describe workflows in natural language. It uses LangChain, Ollama and Qwen 2.5 3B to analyze requirements, generate BPMN XML and validate process models.

## Key Features

- Natural-language business process understanding
- Tool-based AI agent architecture
- Automated BPMN 2.0 XML generation
- Structural and XSD schema-based validation
- Exclusive and parallel gateway support
- Interactive Streamlit interface
- Local LLM inference
- BPMN file export
- No external LLM API key required

## System Architecture

```text
Natural Language Input
        |
        v
Streamlit Interface
        |
        v
LangChain AI Agent <--> Qwen 2.5 3B (Ollama)
        |
        v
BPMN XML Generator
        |
        v
BPMN Validator
        |
        v
BPMN 2.0 Output File
```

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| LangChain | AI agent and tool integration |
| Ollama | Local LLM inference |
| Qwen 2.5 3B | Language understanding and reasoning |
| Streamlit | Interactive frontend |
| lxml | XML processing and validation |
| BPMN 2.0 | Business process modeling standard |
| XSD | Schema-based validation |

## Project Structure

```text
bpmn-ai-agent/
|-- agent.py
|-- app.py
|-- bpmn_generator.py
|-- bpmn_validator.py
|-- bpmn_schemas/
|   |-- BPMN20.xsd
|   |-- BPMNDI.xsd
|   |-- DC.xsd
|   |-- DI.xsd
|   |-- Semantic.xsd
|-- generated_bpmn/
|   |-- bpmn_workflow.bpmn
|-- requirements.txt
|-- .gitignore
|-- README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Sarthakkk231/bpmn-ai-agent.git
cd bpmn-ai-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Install Ollama

Download Ollama from https://ollama.com/download.

### 6. Download the language model

```bash
ollama pull qwen2.5:3b
```

Ensure Ollama is running before launching the application.

### 7. Launch the application

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## How It Works

1. Enter a business process requirement in natural language.
2. The AI agent analyzes the requirement and identifies BPMN elements.
3. The generator creates BPMN 2.0 XML.
4. The validator performs structural and schema-based checks.
5. Review and export the generated workflow.

## Example Input

Create a leave approval process where an employee submits a leave request. The manager reviews the request. If approved, HR updates the leave records. If rejected, the employee receives a rejection notification. Both paths end the process.

## Expected Output

- Start and end events
- Process activities and tasks
- Decision gateways
- Sequence flows
- BPMN 2.0 XML file
- Workflow validation results

## Sample BPMN Output

[View Sample BPMN File](generated_bpmn/bpmn_workflow.bpmn)

The generated file can be opened in compatible BPMN modeling tools such as Camunda Modeler.

## Use Cases

- Business process automation
- Enterprise workflow modeling
- AI-assisted process design
- Business requirement analysis
- Workflow documentation

## Privacy and Local Execution

The application uses Qwen 2.5 3B through Ollama for local AI inference, without requiring an external LLM API key.

## Future Enhancements

- Custom fine-tuned BPMN language model
- Advanced agentic reasoning and planning
- Multi-agent orchestration
- Enhanced BPMN diagram visualization
- Automated workflow correction
- Advanced semantic validation
- Expanded BPMN compliance testing

## Project Status

Under active development.

## Author

**Sarthak Karade**

AI & Data Science | Agentic AI | Machine Learning | AI Automation

- [LinkedIn](https://linkedin.com/in/sarthak-karade)
- [GitHub](https://github.com/Sarthakkk231)
