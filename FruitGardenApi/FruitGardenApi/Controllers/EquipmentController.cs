using FruitGardenApi.Models.Equipment;
using FruitGardenApi.Services.Equipment;
using Microsoft.AspNetCore.Mvc;

namespace FruitGardenApi.Controllers;

[ApiController]
[Route("api/equipment")]
public class EquipmentController(IEquipmentService svc) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> GetAll() => Ok(await svc.GetAllAsync());

    [HttpPost]
    public async Task<IActionResult> Create([FromBody] Equipment equipment) =>
        CreatedAtAction(nameof(GetById), new { id = equipment.Id }, await svc.CreateAsync(equipment));

    [HttpGet("{id}")]
    public async Task<IActionResult> GetById(Guid id)
    {
        var e = await svc.GetByIdAsync(id);
        return e is null ? NotFound() : Ok(e);
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(Guid id, [FromBody] Equipment equipment)
    {
        if (id != equipment.Id) return BadRequest();
        return Ok(await svc.UpdateAsync(equipment));
    }

    [HttpPost("{id}/usage")]
    public async Task<IActionResult> LogUsage(Guid id, [FromBody] UsageLog log)
    {
        log.EquipmentId = id;
        return CreatedAtAction(nameof(GetUsageLogs), new { id }, await svc.LogUsageAsync(log));
    }

    [HttpGet("{id}/usage")]
    public async Task<IActionResult> GetUsageLogs(Guid id) =>
        Ok(await svc.GetUsageLogsAsync(id));

    [HttpGet("maintenance/due")]
    public async Task<IActionResult> GetMaintenanceDue() =>
        Ok(await svc.GetMaintenanceDueAsync());

    [HttpPost("{id}/maintenance")]
    public async Task<IActionResult> RecordMaintenance(Guid id, [FromBody] MaintenanceRecord record)
    {
        record.EquipmentId = id;
        return CreatedAtAction(nameof(GetMaintenanceHistory), new { id }, await svc.RecordMaintenanceAsync(record));
    }

    [HttpGet("{id}/maintenance")]
    public async Task<IActionResult> GetMaintenanceHistory(Guid id) =>
        Ok(await svc.GetMaintenanceHistoryAsync(id));

    [HttpPost("{id}/repair")]
    public async Task<IActionResult> RecordRepair(Guid id, [FromBody] RepairRecord record)
    {
        record.EquipmentId = id;
        return CreatedAtAction(nameof(GetRepairHistory), new { id }, await svc.RecordRepairAsync(record));
    }

    [HttpGet("{id}/repair")]
    public async Task<IActionResult> GetRepairHistory(Guid id) =>
        Ok(await svc.GetRepairHistoryAsync(id));

    [HttpGet("costs/summary")]
    public async Task<IActionResult> GetCostSummary([FromQuery] DateOnly? from = null, [FromQuery] DateOnly? to = null)
    {
        var (maintenance, repair) = await svc.GetCostSummaryAsync(from, to);
        return Ok(new { maintenanceCost = maintenance, repairCost = repair, totalCost = maintenance + repair });
    }
}
