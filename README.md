\# BPMN AI Agent



An AI-powered agentic application that converts natural-language business process descriptions into structured BPMN 2.0 workflows, generates BPMN XML, and validates the resulting process models.



\## Project Overview



The BPMN AI Agent helps users transform business requirements into standardized Business Process Model and Notation (BPMN 2.0) diagrams using an AI-driven workflow.



Users describe a business process in natural language, and the agent analyzes the requirements, generates a process structure, creates BPMN XML, and validates the generated model.



\## Key Features



\- Natural-language business process understanding

\- Agentic AI-based process generation

\- BPMN 2.0 XML generation

\- Automated BPMN validation

\- Gateway and workflow structure handling

\- Parallel and exclusive gateway support

\- Process modeling and structural checks

\- Interactive Streamlit interface

\- BPMN schema-based validation



\## Project Architecture



```text

BPMN AI Agent

│

├── app.py

│   └── Streamlit user interface

│

├── agent.py

│   └── Agentic AI orchestration

│

├── bpmn\_generator.py

│   └── BPMN XML generation

│

├── bpmn\_validator.py

│   └── BPMN validation and structural checks

│

├── bpmn\_schemas/

│   └── BPMN 2.0 XSD schemas

│

└── generated\_bpmn/

&#x20;   └── Generated BPMN process files

```



\## Technology Stack



\- Python

\- Streamlit

\- LangChain

\- LangGraph

\- Ollama

\- Large Language Models (LLMs)

\- BPMN 2.0

\- XML / XSD validation



\## Installation



\### 1. Clone the repository



```bash

git clone YOUR\_GITHUB\_REPOSITORY\_URL

cd ai-agent

```



\### 2. Create a virtual environment



```bash

python -m venv venv

```



\### 3. Activate the environment



Windows:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



\### 4. Install dependencies



```bash

pip install -r requirements.txt

```



\### 5. Set up Ollama



Install Ollama and download the model configured in the project.



For example:



```bash

ollama pull qwen2.5:3b

```



Ensure Ollama is running before starting the application.



\### 6. Run the application



```bash

streamlit run app.py

```



\## Usage



1\. Launch the Streamlit application.

2\. Enter a business process description in natural language.

3\. Allow the agent to analyze the requirements.

4\. Generate the BPMN 2.0 process model.

5\. Validate the generated BPMN XML.

6\. Review the generated output.



\## Project Status



Under active development.



\## Future Enhancements



\- Custom fine-tuned BPMN reasoning model

\- Advanced multi-agent orchestration

\- Improved gateway and exception-handling intelligence

\- Enhanced BPMN diagram visualization

\- Expanded BPMN 2.0 compliance testing



\## Author



\*\*Sarthak Karade\*\*



AI \& Data Science | Agentic AI | Machine Learning | Python



\[LinkedIn](https://linkedin.com/in/sarthak-karade)



