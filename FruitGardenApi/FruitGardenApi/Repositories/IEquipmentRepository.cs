using FruitGardenApi.Models.Equipment;

namespace FruitGardenApi.Repositories;

public interface IEquipmentRepository
{
    Task<List<Equipment>> GetAllAsync();
    Task<Equipment?> GetByIdAsync(Guid id);
    Task<Equipment> CreateAsync(Equipment equipment);
    Task<Equipment> UpdateAsync(Equipment equipment);
    Task<UsageLog> CreateUsageLogAsync(UsageLog log);
    Task<List<UsageLog>> GetUsageLogsAsync(Guid equipmentId);
    Task<MaintenanceRecord> CreateMaintenanceAsync(MaintenanceRecord record);
    Task<List<MaintenanceRecord>> GetMaintenanceAsync(Guid equipmentId);
    Task<RepairRecord> CreateRepairAsync(RepairRecord record);
    Task<List<RepairRecord>> GetRepairsAsync(Guid equipmentId);
    Task<List<Equipment>> GetMaintenanceDueAsync();
}
