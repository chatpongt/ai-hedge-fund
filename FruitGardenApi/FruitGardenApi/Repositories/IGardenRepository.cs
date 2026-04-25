using FruitGardenApi.Models.Garden;

namespace FruitGardenApi.Repositories;

public interface IGardenRepository
{
    // Zones
    Task<List<GardenZone>> GetZonesAsync();
    Task<GardenZone?> GetZoneByIdAsync(Guid id);
    Task<GardenZone> CreateZoneAsync(GardenZone zone);

    // Plants
    Task<List<Plant>> GetPlantsAsync(Guid? zoneId = null);
    Task<Plant?> GetPlantByIdAsync(Guid id);
    Task<Plant> CreatePlantAsync(Plant plant);
    Task<Plant> UpdatePlantAsync(Plant plant);

    // Soil readings
    Task<SoilReading?> GetLatestSoilReadingAsync(Guid plantId);
    Task<List<SoilReading>> GetSoilReadingsAsync(Guid plantId, int days = 30);
    Task<SoilReading> CreateSoilReadingAsync(SoilReading reading);

    // Weather
    Task<List<WeatherLog>> GetWeatherLogsAsync(int days = 7);
    Task<WeatherLog> CreateWeatherLogAsync(WeatherLog log);

    // Observations
    Task<List<GardenObservation>> GetObservationsAsync(Guid? plantId = null);
    Task<GardenObservation> CreateObservationAsync(GardenObservation obs);

    // Tasks
    Task<List<GardenTask>> GetTasksAsync(string? status = null, string? priority = null);
    Task<GardenTask?> GetTaskByIdAsync(Guid id);
    Task<GardenTask> CreateTaskAsync(GardenTask task);
    Task<GardenTask> UpdateTaskAsync(GardenTask task);

    // Analysis Runs
    Task<AnalysisRun> CreateAnalysisRunAsync(AnalysisRun run);
    Task<AnalysisRun?> GetAnalysisRunAsync(Guid id);
    Task<AnalysisRun> UpdateAnalysisRunAsync(AnalysisRun run);
}
