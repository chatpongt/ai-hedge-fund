using FruitGardenApi.Models.Garden;
using FruitGardenApi.Repositories;

namespace FruitGardenApi.Services.Garden;

public class GardenService(IGardenRepository repo) : IGardenService
{
    public Task<List<GardenZone>> GetZonesAsync() => repo.GetZonesAsync();
    public Task<GardenZone> CreateZoneAsync(GardenZone zone) => repo.CreateZoneAsync(zone);
    public Task<List<Plant>> GetPlantsAsync(Guid? zoneId = null) => repo.GetPlantsAsync(zoneId);
    public Task<Plant?> GetPlantByIdAsync(Guid id) => repo.GetPlantByIdAsync(id);
    public Task<Plant> CreatePlantAsync(Plant plant) => repo.CreatePlantAsync(plant);
    public Task<Plant> UpdatePlantAsync(Plant plant) => repo.UpdatePlantAsync(plant);
    public Task<SoilReading> RecordSoilReadingAsync(SoilReading reading) => repo.CreateSoilReadingAsync(reading);
    public Task<GardenObservation> RecordObservationAsync(GardenObservation obs) => repo.CreateObservationAsync(obs);
    public Task<List<GardenObservation>> GetObservationsAsync(Guid? plantId = null) => repo.GetObservationsAsync(plantId);
    public Task<List<GardenTask>> GetTasksAsync(string? status = null, string? priority = null) => repo.GetTasksAsync(status, priority);
    public Task<GardenTask> CreateTaskAsync(GardenTask task) => repo.CreateTaskAsync(task);

    public async Task<GardenTask> CompleteTaskAsync(Guid taskId)
    {
        var task = await repo.GetTaskByIdAsync(taskId) ?? throw new KeyNotFoundException($"Task {taskId} not found");
        task.Status = "completed";
        task.CompletedAt = DateTime.UtcNow;
        return await repo.UpdateTaskAsync(task);
    }
}
