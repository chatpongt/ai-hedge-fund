using FruitGardenApi.Models.Equipment;

namespace FruitGardenApi.Services.Equipment;

public interface IEquipmentService
{
    Task<List<Equipment>> GetAllAsync();
    Task<Equipment?> GetByIdAsync(Guid id);
    Task<Equipment> CreateAsync(Equipment equipment);
    Task<Equipment> UpdateAsync(Equipment equipment);
    Task<UsageLog> LogUsageAsync(UsageLog log);
    Task<List<UsageLog>> GetUsageLogsAsync(Guid equipmentId);
    Task<MaintenanceRecord> RecordMaintenanceAsync(MaintenanceRecord record);
    Task<List<MaintenanceRecord>> GetMaintenanceHistoryAsync(Guid equipmentId);
    Task<RepairRecord> RecordRepairAsync(RepairRecord record);
    Task<List<RepairRecord>> GetRepairHistoryAsync(Guid equipmentId);
    Task<List<Equipment>> GetMaintenanceDueAsync();
    Task<(decimal MaintenanceCost, decimal RepairCost)> GetCostSummaryAsync(DateOnly? from = null, DateOnly? to = null);
}
