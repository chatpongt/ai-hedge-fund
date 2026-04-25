using FruitGardenApi.Models.Garden;
using FruitGardenApi.Services.Garden;
using Microsoft.AspNetCore.Mvc;

namespace FruitGardenApi.Controllers;

[ApiController]
[Route("api/garden")]
public class GardenController(IGardenService svc) : ControllerBase
{
    [HttpGet("zones")]
    public async Task<IActionResult> GetZones() => Ok(await svc.GetZonesAsync());

    [HttpPost("zones")]
    public async Task<IActionResult> CreateZone([FromBody] GardenZone zone) =>
        CreatedAtAction(nameof(GetZones), await svc.CreateZoneAsync(zone));

    [HttpGet("plants")]
    public async Task<IActionResult> GetPlants([FromQuery] Guid? zoneId = null) =>
        Ok(await svc.GetPlantsAsync(zoneId));

    [HttpPost("plants")]
    public async Task<IActionResult> CreatePlant([FromBody] Plant plant) =>
        CreatedAtAction(nameof(GetPlantById), new { id = plant.Id }, await svc.CreatePlantAsync(plant));

    [HttpGet("plants/{id}")]
    public async Task<IActionResult> GetPlantById(Guid id)
    {
        var plant = await svc.GetPlantByIdAsync(id);
        return plant is null ? NotFound() : Ok(plant);
    }

    [HttpPut("plants/{id}")]
    public async Task<IActionResult> UpdatePlant(Guid id, [FromBody] Plant plant)
    {
        if (id != plant.Id) return BadRequest();
        return Ok(await svc.UpdatePlantAsync(plant));
    }

    [HttpPost("soil-metrics")]
    public async Task<IActionResult> RecordSoilReading([FromBody] SoilReading reading) =>
        CreatedAtAction(nameof(RecordSoilReading), await svc.RecordSoilReadingAsync(reading));

    [HttpGet("observations")]
    public async Task<IActionResult> GetObservations([FromQuery] Guid? plantId = null) =>
        Ok(await svc.GetObservationsAsync(plantId));

    [HttpPost("observations")]
    public async Task<IActionResult> CreateObservation([FromBody] GardenObservation obs) =>
        CreatedAtAction(nameof(GetObservations), await svc.RecordObservationAsync(obs));

    [HttpGet("tasks")]
    public async Task<IActionResult> GetTasks([FromQuery] string? status = null, [FromQuery] string? priority = null) =>
        Ok(await svc.GetTasksAsync(status, priority));

    [HttpPost("tasks")]
    public async Task<IActionResult> CreateTask([FromBody] GardenTask task) =>
        CreatedAtAction(nameof(GetTasks), await svc.CreateTaskAsync(task));

    [HttpPut("tasks/{id}/complete")]
    public async Task<IActionResult> CompleteTask(Guid id) =>
        Ok(await svc.CompleteTaskAsync(id));
}
