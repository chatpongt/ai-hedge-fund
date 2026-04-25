using FruitGardenApi.Models.Equipment;
using FruitGardenApi.Repositories;

namespace FruitGardenApi.Services.Equipment;

public class EquipmentService(IEquipmentRepository repo) : IEquipmentService
{
    public Task<List<Equipment>> GetAllAsync() => repo.GetAllAsync();
    public Task<Equipment?> GetByIdAsync(Guid id) => repo.GetByIdAsync(id);
    public Task<Equipment> CreateAsync(Equipment equipment) => repo.CreateAsync(equipment);
    public Task<Equipment> UpdateAsync(Equipment equipment) => repo.UpdateAsync(equipment);
    public Task<UsageLog> LogUsageAsync(UsageLog log) => repo.CreateUsageLogAsync(log);
    public Task<List<UsageLog>> GetUsageLogsAsync(Guid equipmentId) => repo.GetUsageLogsAsync(equipmentId);
    public Task<MaintenanceRecord> RecordMaintenanceAsync(MaintenanceRecord record) => repo.CreateMaintenanceAsync(record);
    public Task<List<MaintenanceRecord>> GetMaintenanceHistoryAsync(Guid equipmentId) => repo.GetMaintenanceAsync(equipmentId);
    public Task<RepairRecord> RecordRepairAsync(RepairRecord record) => repo.CreateRepairAsync(record);
    public Task<List<RepairRecord>> GetRepairHistoryAsync(Guid equipmentId) => repo.GetRepairsAsync(equipmentId);
    public Task<List<Equipment>> GetMaintenanceDueAsync() => repo.GetMaintenanceDueAsync();

    public async Task<(decimal MaintenanceCost, decimal RepairCost)> GetCostSummaryAsync(DateOnly? from = null, DateOnly? to = null)
    {
        var allEquipment = await repo.GetAllAsync();
        decimal mCost = 0, rCost = 0;
        foreach (var e in allEquipment)
        {
            var maintenance = await repo.GetMaintenanceAsync(e.Id);
            var repairs = await repo.GetRepairsAsync(e.Id);
            mCost += maintenance.Where(m => (!from.HasValue || m.MaintenanceDate >= from) && (!to.HasValue || m.MaintenanceDate <= to)).Sum(m => m.Cost);
            rCost += repairs.Where(r => (!from.HasValue || r.ReportedDate >= from) && (!to.HasValue || r.ReportedDate <= to)).Sum(r => r.RepairCost);
        }
        return (mCost, rCost);
    }
}
