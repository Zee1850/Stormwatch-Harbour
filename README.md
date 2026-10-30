# Stormwatch Harbour

## Project Description
Stormwatch Harbour is a Python-based harbour simulation for an Agentic AI assignment. It compares a baseline Dockworker policy, a model-based policy, and an LLM-based Harbour Master.

The simulation includes ships, cargo, Dockworkers, berths, and storms. The main goal is to deliver cargo while keeping workers safe.

## Project Files

- `run.py` – Runs the baseline and model-based simulations.
- `harbour_master_sim.py` – Runs the simulation with the Groq LLM Harbour Master.
- `task3.py` – Earlier Task 3 simulation version.
- `test_groq.py` – Tests the Groq API connection.

## Requirements
- Python
- Internet connection for the Groq API
- Groq API key for the LLM-based simulation

## How to Run

Run the baseline and model-based simulations:

```bash
python run.py
```

For the LLM-based Harbour Master, first set your Groq API key in PowerShell:

```powershell
$env:GROQ_API_KEY="YOUR_API_KEY"
```

Then run:

```bash
python harbour_master_sim.py
```

Replace `YOUR_API_KEY` with your own key. Do not share or upload your API key.

## Testing
The project was tested using seeds 11, 12, and 13. The LLM actions were also checked using validation and safety tests.