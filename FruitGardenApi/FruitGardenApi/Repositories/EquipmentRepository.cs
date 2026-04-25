using FruitGardenApi.Data;
using FruitGardenApi.Models.Equipment;
using Microsoft.EntityFrameworkCore;

namespace FruitGardenApi.Repositories;

public class EquipmentRepository(AppDbContext db) : IEquipmentRepository
{
    public Task<List<Equipment>> GetAllAsync() => db.Equipment.ToListAsync();

    public Task<Equipment?> GetByIdAsync(Guid id) =>
        db.Equipment.Include(e => e.UsageLogs).Include(e => e.MaintenanceRecords).Include(e => e.RepairRecords).FirstOrDefaultAsync(e => e.Id == id);

    public async Task<Equipment> CreateAsync(Equipment equipment)
    {
        db.Equipment.Add(equipment);
        await db.SaveChangesAsync();
        return equipment;
    }

    public async Task<Equipment> UpdateAsync(Equipment equipment)
    {
        equipment.UpdatedAt = DateTime.UtcNow;
        db.Equipment.Update(equipment);
        await db.SaveChangesAsync();
        return equipment;
    }

    public async Task<UsageLog> CreateUsageLogAsync(UsageLog log)
    {
        db.UsageLogs.Add(log);
        var equip = await db.Equipment.FindAsync(log.EquipmentId);
        if (equip != null)
        {
            equip.TotalHoursUsed += log.HoursUsed;
            equip.UpdatedAt = DateTime.UtcNow;
        }
        await db.SaveChangesAsync();
        return log;
    }

    public Task<List<UsageLog>> GetUsageLogsAsync(Guid equipmentId) =>
        db.UsageLogs.Where(u => u.EquipmentId == equipmentId).OrderByDescending(u => u.UsageDate).ToListAsync();

    public async Task<MaintenanceRecord> CreateMaintenanceAsync(MaintenanceRecord record)
    {
        db.MaintenanceRecords.Add(record);
        var equip = await db.Equipment.FindAsync(record.EquipmentId);
        if (equip != null)
        {
            equip.Status = "operational";
            equip.NextMaintenanceDate = record.NextDueDate;
            equip.UpdatedAt = DateTime.UtcNow;
        }
        await db.SaveChangesAsync();
        return record;
    }

    public Task<List<MaintenanceRecord>> GetMaintenanceAsync(Guid equipmentId) =>
        db.MaintenanceRecords.Where(m => m.EquipmentId == equipmentId).OrderByDescending(m => m.MaintenanceDate).ToListAsync();

    public async Task<RepairRecord> CreateRepairAsync(RepairRecord record)
    {
        db.RepairRecords.Add(record);
        var equip = await db.Equipment.FindAsync(record.EquipmentId);
        if (equip != null)
        {
            equip.Status = record.Status == "completed" ? "operational" : "repair";
            equip.UpdatedAt = DateTime.UtcNow;
        }
        await db.SaveChangesAsync();
        return record;
    }

    public Task<List<RepairRecord>> GetRepairsAsync(Guid equipmentId) =>
        db.RepairRecords.Where(r => r.EquipmentId == equipmentId).OrderByDescending(r => r.ReportedDate).ToListAsync();

    public Task<List<Equipment>> GetMaintenanceDueAsync()
    {
        var today = DateOnly.FromDateTime(DateTime.Today);
        return db.Equipment.Where(e =>
            e.Status != "retired" &&
            (e.NextMaintenanceDate.HasValue && e.NextMaintenanceDate <= today.AddDays(7) ||
             e.TotalHoursUsed >= e.NextMaintenanceHours - 50)
        ).ToListAsync();
    }
}
