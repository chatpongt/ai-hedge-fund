# Fruit Garden Management System — Backend

ASP.NET Core 8 Web API สำหรับระบบบริหารจัดการสวนผลไม้

## Tech Stack
- **C# / .NET 8** + ASP.NET Core Web API
- **Entity Framework Core 8** + SQLite
- **Microsoft Semantic Kernel** — AI agent orchestration
- **Swagger/OpenAPI** — API documentation

## Quick Start

```bash
cd FruitGardenApi
dotnet restore
dotnet run
```

API will start at `http://localhost:5000`  
Swagger UI at `http://localhost:5000/swagger`

The database is auto-created and seeded with Thai fruit garden mock data on first run.

## Modules

| Module | Route | Description |
|--------|-------|-------------|
| Garden | `/api/garden/*` | Plants, zones, tasks, soil readings |
| AI Analysis | `/api/analysis/*` | Run Semantic Kernel agents |
| Finance | `/api/finance/*` | Income, expenses, ROI, budget |
| HR | `/api/hr/*` | Workers, assignments, attendance, payroll |
| Equipment | `/api/equipment/*` | Inventory, usage, maintenance, repairs |
| Mock Data | `/api/mock/seed` | Seed Thai fruit garden sample data |

## AI Agents (Semantic Kernel)

Four rule-based agents run in parallel via `Task.WhenAll()`:

1. **WateringPlugin** — soil moisture + rainfall → `water_needed|adequate|over_watered`
2. **PestDetectionPlugin** — observations + humidity → `pest_detected|high_risk|low_risk`
3. **HarvestPredictorPlugin** — growth stage + age → `harvest_ready|harvest_urgent|not_ready`
4. **DiseaseMonitorPlugin** — health status + weather → `treatment_needed|disease_risk|healthy`

To enable LLM-augmented reasoning, set `SemanticKernel:OpenAI:ApiKey` in `appsettings.json`.

## Environment

```json
{
  "ConnectionStrings": {
    "DefaultConnection": "Data Source=fruit_garden.db"
  },
  "SemanticKernel": {
    "OpenAI": { "ApiKey": "sk-...", "ModelId": "gpt-4o-mini" }
  }
}
```
