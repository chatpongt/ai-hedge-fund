namespace FruitGardenApi.Models.Garden;

public class GardenSignal
{
    public string Signal { get; set; } = "";
    public float Confidence { get; set; }
    public string Reasoning { get; set; } = "";
    public string? RecommendedAction { get; set; }
}

public class PlantAnalysisResult
{
    public Guid PlantId { get; set; }
    public string PlantName { get; set; } = "";
    public GardenSignal Watering { get; set; } = new();
    public GardenSignal PestDetection { get; set; } = new();
    public GardenSignal HarvestPrediction { get; set; } = new();
    public GardenSignal DiseaseMonitor { get; set; } = new();
}

public class GardenActionPlan
{
    public Guid RunId { get; set; } = Guid.NewGuid();
    public DateTime AnalyzedAt { get; set; } = DateTime.UtcNow;
    public List<PlantAnalysisResult> PlantResults { get; set; } = [];
    public List<GardenTask> PrioritizedTasks { get; set; } = [];
    public string Summary { get; set; } = "";
}

public class AnalysisRun
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public DateTime RunDate { get; set; } = DateTime.UtcNow;
    public string Status { get; set; } = "pending"; // pending, running, completed, failed
    public string? ResultJson { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
