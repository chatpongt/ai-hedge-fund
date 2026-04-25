using FruitGardenApi.Data;
using FruitGardenApi.Models.Garden;
using Microsoft.EntityFrameworkCore;

namespace FruitGardenApi.Repositories;

public class GardenRepository(AppDbContext db) : IGardenRepository
{
    public Task<List<GardenZone>> GetZonesAsync() =>
        db.GardenZones.Include(z => z.Plants).ToListAsync();

    public Task<GardenZone?> GetZoneByIdAsync(Guid id) =>
        db.GardenZones.Include(z => z.Plants).FirstOrDefaultAsync(z => z.Id == id);

    public async Task<GardenZone> CreateZoneAsync(GardenZone zone)
    {
        db.GardenZones.Add(zone);
        await db.SaveChangesAsync();
        return zone;
    }

    public Task<List<Plant>> GetPlantsAsync(Guid? zoneId = null)
    {
        var q = db.Plants.Include(p => p.Zone).AsQueryable();
        if (zoneId.HasValue) q = q.Where(p => p.ZoneId == zoneId.Value);
        return q.ToListAsync();
    }

    public Task<Plant?> GetPlantByIdAsync(Guid id) =>
        db.Plants.Include(p => p.Zone).Include(p => p.SoilReadings.OrderByDescending(s => s.ReadingDate).Take(1)).FirstOrDefaultAsync(p => p.Id == id);

    public async Task<Plant> CreatePlantAsync(Plant plant)
    {
        db.Plants.Add(plant);
        await db.SaveChangesAsync();
        return plant;
    }

    public async Task<Plant> UpdatePlantAsync(Plant plant)
    {
        plant.UpdatedAt = DateTime.UtcNow;
        db.Plants.Update(plant);
        await db.SaveChangesAsync();
        return plant;
    }

    public Task<SoilReading?> GetLatestSoilReadingAsync(Guid plantId) =>
        db.SoilReadings.Where(s => s.PlantId == plantId).OrderByDescending(s => s.ReadingDate).FirstOrDefaultAsync();

    public Task<List<SoilReading>> GetSoilReadingsAsync(Guid plantId, int days = 30)
    {
        var cutoff = DateOnly.FromDateTime(DateTime.Today.AddDays(-days));
        return db.SoilReadings.Where(s => s.PlantId == plantId && s.ReadingDate >= cutoff).OrderBy(s => s.ReadingDate).ToListAsync();
    }

    public async Task<SoilReading> CreateSoilReadingAsync(SoilReading reading)
    {
        db.SoilReadings.Add(reading);
        await db.SaveChangesAsync();
        return reading;
    }

    public Task<List<WeatherLog>> GetWeatherLogsAsync(int days = 7)
    {
        var cutoff = DateOnly.FromDateTime(DateTime.Today.AddDays(-days));
        return db.WeatherLogs.Where(w => w.LogDate >= cutoff).OrderBy(w => w.LogDate).ToListAsync();
    }

    public async Task<WeatherLog> CreateWeatherLogAsync(WeatherLog log)
    {
        db.WeatherLogs.Add(log);
        await db.SaveChangesAsync();
        return log;
    }

    public Task<List<GardenObservation>> GetObservationsAsync(Guid? plantId = null)
    {
        var q = db.Observations.Include(o => o.Plant).AsQueryable();
        if (plantId.HasValue) q = q.Where(o => o.PlantId == plantId.Value);
        return q.OrderByDescending(o => o.ObservationDate).ToListAsync();
    }

    public async Task<GardenObservation> CreateObservationAsync(GardenObservation obs)
    {
        db.Observations.Add(obs);
        await db.SaveChangesAsync();
        return obs;
    }

    public Task<List<GardenTask>> GetTasksAsync(string? status = null, string? priority = null)
    {
        var q = db.GardenTasks.Include(t => t.Plant).AsQueryable();
        if (status != null) q = q.Where(t => t.Status == status);
        if (priority != null) q = q.Where(t => t.Priority == priority);
        return q.OrderBy(t => t.DueDate).ToListAsync();
    }

    public Task<GardenTask?> GetTaskByIdAsync(Guid id) =>
        db.GardenTasks.Include(t => t.Plant).FirstOrDefaultAsync(t => t.Id == id);

    public async Task<GardenTask> CreateTaskAsync(GardenTask task)
    {
        db.GardenTasks.Add(task);
        await db.SaveChangesAsync();
        return task;
    }

    public async Task<GardenTask> UpdateTaskAsync(GardenTask task)
    {
        db.GardenTasks.Update(task);
        await db.SaveChangesAsync();
        return task;
    }

    public async Task<AnalysisRun> CreateAnalysisRunAsync(AnalysisRun run)
    {
        db.AnalysisRuns.Add(run);
        await db.SaveChangesAsync();
        return run;
    }

    public Task<AnalysisRun?> GetAnalysisRunAsync(Guid id) =>
        db.AnalysisRuns.FindAsync(id).AsTask();

    public async Task<AnalysisRun> UpdateAnalysisRunAsync(AnalysisRun run)
    {
        db.AnalysisRuns.Update(run);
        await db.SaveChangesAsync();
        return run;
    }
}
