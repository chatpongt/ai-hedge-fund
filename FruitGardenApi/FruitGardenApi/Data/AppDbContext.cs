using FruitGardenApi.Models.Garden;
using FruitGardenApi.Models.Finance;
using FruitGardenApi.Models.HR;
using FruitGardenApi.Models.Equipment;
using Microsoft.EntityFrameworkCore;

namespace FruitGardenApi.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    // Garden
    public DbSet<GardenZone> GardenZones => Set<GardenZone>();
    public DbSet<Plant> Plants => Set<Plant>();
    public DbSet<SoilReading> SoilReadings => Set<SoilReading>();
    public DbSet<WeatherLog> WeatherLogs => Set<WeatherLog>();
    public DbSet<GardenObservation> Observations => Set<GardenObservation>();
    public DbSet<GardenTask> GardenTasks => Set<GardenTask>();
    public DbSet<AnalysisRun> AnalysisRuns => Set<AnalysisRun>();

    // Finance
    public DbSet<IncomeRecord> IncomeRecords => Set<IncomeRecord>();
    public DbSet<ExpenseRecord> ExpenseRecords => Set<ExpenseRecord>();
    public DbSet<BudgetPlan> BudgetPlans => Set<BudgetPlan>();

    // HR
    public DbSet<Worker> Workers => Set<Worker>();
    public DbSet<WorkAssignment> WorkAssignments => Set<WorkAssignment>();
    public DbSet<AttendanceLog> AttendanceLogs => Set<AttendanceLog>();
    public DbSet<PayrollRecord> PayrollRecords => Set<PayrollRecord>();

    // Equipment
    public DbSet<Equipment> Equipment => Set<Equipment>();
    public DbSet<UsageLog> UsageLogs => Set<UsageLog>();
    public DbSet<MaintenanceRecord> MaintenanceRecords => Set<MaintenanceRecord>();
    public DbSet<RepairRecord> RepairRecords => Set<RepairRecord>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Plant>()
            .HasOne(p => p.Zone)
            .WithMany(z => z.Plants)
            .HasForeignKey(p => p.ZoneId);

        modelBuilder.Entity<SoilReading>()
            .HasOne(s => s.Plant)
            .WithMany(p => p.SoilReadings)
            .HasForeignKey(s => s.PlantId);

        modelBuilder.Entity<GardenObservation>()
            .HasOne(o => o.Plant)
            .WithMany(p => p.Observations)
            .HasForeignKey(o => o.PlantId);

        modelBuilder.Entity<GardenTask>()
            .HasOne(t => t.Plant)
            .WithMany(p => p.Tasks)
            .HasForeignKey(t => t.PlantId)
            .IsRequired(false);

        modelBuilder.Entity<WorkAssignment>()
            .HasOne(a => a.Worker)
            .WithMany(w => w.Assignments)
            .HasForeignKey(a => a.WorkerId);

        modelBuilder.Entity<AttendanceLog>()
            .HasOne(a => a.Worker)
            .WithMany(w => w.AttendanceLogs)
            .HasForeignKey(a => a.WorkerId);

        modelBuilder.Entity<PayrollRecord>()
            .HasOne(p => p.Worker)
            .WithMany()
            .HasForeignKey(p => p.WorkerId);

        modelBuilder.Entity<UsageLog>()
            .HasOne(u => u.Equipment)
            .WithMany(e => e.UsageLogs)
            .HasForeignKey(u => u.EquipmentId);

        modelBuilder.Entity<MaintenanceRecord>()
            .HasOne(m => m.Equipment)
            .WithMany(e => e.MaintenanceRecords)
            .HasForeignKey(m => m.EquipmentId);

        modelBuilder.Entity<RepairRecord>()
            .HasOne(r => r.Equipment)
            .WithMany(e => e.RepairRecords)
            .HasForeignKey(r => r.EquipmentId);
    }
}
