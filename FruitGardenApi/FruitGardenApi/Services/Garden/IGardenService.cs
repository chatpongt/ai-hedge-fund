using FruitGardenApi.Models.Garden;

namespace FruitGardenApi.Services.Garden;

public interface IGardenService
{
    Task<List<GardenZone>> GetZonesAsync();
    Task<GardenZone> CreateZoneAsync(GardenZone zone);
    Task<List<Plant>> GetPlantsAsync(Guid? zoneId = null);
    Task<Plant?> GetPlantByIdAsync(Guid id);
    Task<Plant> CreatePlantAsync(Plant plant);
    Task<Plant> UpdatePlantAsync(Plant plant);
    Task<SoilReading> RecordSoilReadingAsync(SoilReading reading);
    Task<GardenObservation> RecordObservationAsync(GardenObservation obs);
    Task<List<GardenObservation>> GetObservationsAsync(Guid? plantId = null);
    Task<List<GardenTask>> GetTasksAsync(string? status = null, string? priority = null);
    Task<GardenTask> CreateTaskAsync(GardenTask task);
    Task<GardenTask> CompleteTaskAsync(Guid taskId);
}
