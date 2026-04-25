using FruitGardenApi.Models.Garden;
using FruitGardenApi.Models.Finance;
using FruitGardenApi.Models.HR;
using FruitGardenApi.Models.Equipment;

namespace FruitGardenApi.Data;

public static class DataSeeder
{
    public static async Task SeedAsync(AppDbContext db)
    {
        if (db.GardenZones.Any()) return;

        var today = DateOnly.FromDateTime(DateTime.Today);
        var rng = new Random(42);

        // ── Zones ──────────────────────────────────────────────────────────
        var zone1 = new GardenZone
        {
            Id = Guid.NewGuid(), Name = "โซนมะม่วง", Description = "พื้นที่ปลูกมะม่วงและทุเรียน",
            AreaSqm = 2000, SoilType = "loam", IrrigationType = "drip"
        };
        var zone2 = new GardenZone
        {
            Id = Guid.NewGuid(), Name = "โซนส้ม", Description = "พื้นที่ปลูกส้มและผลไม้เมืองร้อน",
            AreaSqm = 1500, SoilType = "sandy", IrrigationType = "sprinkler"
        };
        db.GardenZones.AddRange(zone1, zone2);

        // ── Plants ─────────────────────────────────────────────────────────
        var plants = new List<Plant>
        {
            new() { Id = Guid.NewGuid(), ZoneId = zone1.Id, Name = "มะม่วงน้ำดอกไม้ #1", Species = "Mangifera indica", Variety = "น้ำดอกไม้", PlantedDate = today.AddYears(-5), GrowthStage = "bearing", HealthStatus = "healthy", PositionX = 100, PositionY = 100 },
            new() { Id = Guid.NewGuid(), ZoneId = zone1.Id, Name = "มะม่วงน้ำดอกไม้ #2", Species = "Mangifera indica", Variety = "น้ำดอกไม้", PlantedDate = today.AddYears(-4), GrowthStage = "bearing", HealthStatus = "stressed", PositionX = 200, PositionY = 100 },
            new() { Id = Guid.NewGuid(), ZoneId = zone1.Id, Name = "ทุเรียนหมอนทอง #1",  Species = "Durio zibethinus",  Variety = "หมอนทอง",   PlantedDate = today.AddYears(-7), GrowthStage = "bearing", HealthStatus = "healthy", PositionX = 100, PositionY = 200 },
            new() { Id = Guid.NewGuid(), ZoneId = zone1.Id, Name = "ลำไยอีดอ #1",        Species = "Dimocarpus longan",  Variety = "อีดอ",       PlantedDate = today.AddYears(-6), GrowthStage = "bearing", HealthStatus = "healthy", PositionX = 300, PositionY = 150 },
            new() { Id = Guid.NewGuid(), ZoneId = zone2.Id, Name = "ส้มโอขาวน้ำผึ้ง #1", Species = "Citrus maxima",     Variety = "ขาวน้ำผึ้ง", PlantedDate = today.AddYears(-3), GrowthStage = "mature",  HealthStatus = "healthy", PositionX = 100, PositionY = 100 },
            new() { Id = Guid.NewGuid(), ZoneId = zone2.Id, Name = "มะนาวแป้น #1",        Species = "Citrus aurantiifolia", Variety = "แป้น",   PlantedDate = today.AddYears(-2), GrowthStage = "bearing", HealthStatus = "diseased", PositionX = 200, PositionY = 100 },
            new() { Id = Guid.NewGuid(), ZoneId = zone2.Id, Name = "มะละกอฮอลแลนด์ #1",  Species = "Carica papaya",     Variety = "ฮอลแลนด์",  PlantedDate = today.AddYears(-1), GrowthStage = "bearing", HealthStatus = "healthy", PositionX = 100, PositionY = 200 },
            new() { Id = Guid.NewGuid(), ZoneId = zone2.Id, Name = "กล้วยหอมทอง #1",     Species = "Musa acuminata",    Variety = "หอมทอง",    PlantedDate = today.AddMonths(-8), GrowthStage = "mature", HealthStatus = "healthy", PositionX = 300, PositionY = 150 },
        };
        db.Plants.AddRange(plants);

        // ── Soil Readings (30 days each) ───────────────────────────────────
        var soilReadings = new List<SoilReading>();
        foreach (var plant in plants)
        {
            for (int d = 29; d >= 0; d--)
            {
                soilReadings.Add(new SoilReading
                {
                    Id = Guid.NewGuid(), PlantId = plant.Id,
                    ReadingDate = today.AddDays(-d),
                    Ph = 6.0f + (float)rng.NextDouble() * 1.0f,
                    MoisturePct = 40f + (float)rng.NextDouble() * 30f,
                    NitrogenPpm = 120f + (float)rng.NextDouble() * 60f,
                    PhosphorusPpm = 30f + (float)rng.NextDouble() * 20f,
                    PotassiumPpm = 150f + (float)rng.NextDouble() * 100f,
                });
            }
        }
        db.SoilReadings.AddRange(soilReadings);

        // ── Weather Log (30 days) ──────────────────────────────────────────
        var weatherLogs = Enumerable.Range(0, 30).Select(d => new WeatherLog
        {
            Id = Guid.NewGuid(), LogDate = today.AddDays(-29 + d),
            TempHigh = 32f + (float)rng.NextDouble() * 6f,
            TempLow = 22f + (float)rng.NextDouble() * 4f,
            RainfallMm = d % 4 == 0 ? (float)rng.NextDouble() * 20f : 0f,
            HumidityPct = 65f + (float)rng.NextDouble() * 20f,
            WillRain = d % 3 == 0,
        }).ToList();
        db.WeatherLogs.AddRange(weatherLogs);

        // ── Observations ───────────────────────────────────────────────────
        var obsTypes = new[] { "pest", "disease", "growth", "general" };
        var severities = new[] { "low", "low", "low", "medium", "high" };
        var observations = new List<GardenObservation>();
        foreach (var plant in plants)
        {
            for (int i = 0; i < 5; i++)
            {
                var obsType = obsTypes[rng.Next(obsTypes.Length)];
                observations.Add(new GardenObservation
                {
                    Id = Guid.NewGuid(), PlantId = plant.Id,
                    ObservationDate = today.AddDays(-rng.Next(1, 30)),
                    Observer = "ผู้จัดการสวน",
                    ObsType = obsType,
                    Severity = severities[rng.Next(severities.Length)],
                    Notes = obsType switch
                    {
                        "pest"    => "พบเพลี้ยอ่อนบริเวณใบอ่อน ควรพ่นยาฆ่าแมลง",
                        "disease" => "ใบมีจุดสีน้ำตาล อาจเป็นโรคราสนิม",
                        "growth"  => "การเจริญเติบโตปกติ ดอกเริ่มแย้มออก",
                        _         => "ตรวจสอบสภาพทั่วไป ไม่พบความผิดปกติ",
                    },
                });
            }
        }
        db.Observations.AddRange(observations);

        // ── Tasks ──────────────────────────────────────────────────────────
        var tasks = new List<GardenTask>
        {
            new() { Id = Guid.NewGuid(), PlantId = plants[1].Id, TaskType = "water",     Priority = "urgent", DueDate = today, Status = "pending",    Instructions = "รดน้ำ 20 ลิตรต่อต้น เนื่องจากดินแห้ง" },
            new() { Id = Guid.NewGuid(), PlantId = plants[5].Id, TaskType = "spray",     Priority = "high",   DueDate = today, Status = "pending",    Instructions = "พ่นยาป้องกันโรคราสนิม อัตรา 2 ml/L" },
            new() { Id = Guid.NewGuid(), PlantId = plants[2].Id, TaskType = "fertilize", Priority = "medium", DueDate = today.AddDays(2), Status = "pending", Instructions = "ใส่ปุ๋ยสูตร 15-15-15 อัตรา 500 g/ต้น" },
            new() { Id = Guid.NewGuid(), PlantId = plants[0].Id, TaskType = "harvest",   Priority = "high",   DueDate = today.AddDays(3), Status = "pending", Instructions = "เก็บเกี่ยวมะม่วงน้ำดอกไม้ ผลสุก 80%" },
            new() { Id = Guid.NewGuid(), PlantId = plants[6].Id, TaskType = "harvest",   Priority = "urgent", DueDate = today, Status = "pending",    Instructions = "เก็บมะละกอ ผลสุกพร้อมเก็บเกี่ยว" },
            new() { Id = Guid.NewGuid(), PlantId = null,         TaskType = "prune",     Priority = "low",    DueDate = today.AddDays(7), Status = "pending", Instructions = "ตัดแต่งกิ่งทั่วสวน กิ่งแห้งและกิ่งที่ขัดกัน" },
        };
        db.GardenTasks.AddRange(tasks);

        // ── Workers ────────────────────────────────────────────────────────
        var workers = new List<Worker>
        {
            new() { Id = Guid.NewGuid(), Name = "สมชาย ใจดี",   Role = "supervisor",      DailyWage = 600m, StartDate = today.AddYears(-3), Status = "active", Contact = "081-234-5678" },
            new() { Id = Guid.NewGuid(), Name = "สมหญิง รักงาน", Role = "general_worker",  DailyWage = 400m, StartDate = today.AddYears(-2), Status = "active", Contact = "082-345-6789" },
            new() { Id = Guid.NewGuid(), Name = "ประสิทธิ์ ขยัน", Role = "specialist",     DailyWage = 500m, StartDate = today.AddYears(-1), Status = "active", Contact = "083-456-7890" },
            new() { Id = Guid.NewGuid(), Name = "มาลี สวยงาม",   Role = "seasonal",        DailyWage = 350m, StartDate = today.AddMonths(-3), Status = "active", Contact = "084-567-8901" },
            new() { Id = Guid.NewGuid(), Name = "วิชัย ตั้งใจ",  Role = "general_worker",  DailyWage = 400m, StartDate = today.AddMonths(-6), Status = "active", Contact = "085-678-9012" },
        };
        db.Workers.AddRange(workers);

        // ── Attendance (last 7 days) ───────────────────────────────────────
        var attendances = new List<AttendanceLog>();
        foreach (var w in workers)
        {
            for (int d = 6; d >= 0; d--)
            {
                var absent = rng.Next(10) == 0;
                attendances.Add(new AttendanceLog
                {
                    Id = Guid.NewGuid(), WorkerId = w.Id, Date = today.AddDays(-d),
                    ClockIn = absent ? null : "08:00", ClockOut = absent ? null : "17:00",
                    HoursWorked = absent ? 0 : 8f,
                    AbsenceReason = absent ? "sick" : null,
                });
            }
        }
        db.AttendanceLogs.AddRange(attendances);

        // ── Finance (3 months) ─────────────────────────────────────────────
        var incomes = new List<IncomeRecord>
        {
            new() { Id = Guid.NewGuid(), PlantId = plants[0].Id, Date = today.AddMonths(-2), Amount = 15000m, Source = "harvest_sale", QuantityKg = 300f, PricePerKg = 50m, Notes = "ขายมะม่วงน้ำดอกไม้ ตลาดสด" },
            new() { Id = Guid.NewGuid(), PlantId = plants[2].Id, Date = today.AddMonths(-1), Amount = 45000m, Source = "harvest_sale", QuantityKg = 150f, PricePerKg = 300m, Notes = "ขายทุเรียนหมอนทอง" },
            new() { Id = Guid.NewGuid(), PlantId = plants[3].Id, Date = today.AddMonths(-1), Amount = 12000m, Source = "harvest_sale", QuantityKg = 200f, PricePerKg = 60m, Notes = "ขายลำไยอีดอ" },
            new() { Id = Guid.NewGuid(), PlantId = plants[6].Id, Date = today.AddDays(-5),   Amount = 3000m,  Source = "harvest_sale", QuantityKg = 100f, PricePerKg = 30m, Notes = "ขายมะละกอ" },
        };
        var expenses = new List<ExpenseRecord>
        {
            new() { Id = Guid.NewGuid(), Date = today.AddMonths(-2), Amount = 8000m,  Category = "labor",      Description = "ค่าแรงคนงานเดือนที่แล้ว" },
            new() { Id = Guid.NewGuid(), Date = today.AddMonths(-2), Amount = 3500m,  Category = "fertilizer", Description = "ซื้อปุ๋ยสูตร 15-15-15 จำนวน 100 kg", Vendor = "ร้านเกษตรกรสุข" },
            new() { Id = Guid.NewGuid(), Date = today.AddMonths(-1), Amount = 8000m,  Category = "labor",      Description = "ค่าแรงคนงานเดือนที่แล้ว" },
            new() { Id = Guid.NewGuid(), Date = today.AddMonths(-1), Amount = 2200m,  Category = "pesticide",  Description = "ยาฆ่าแมลง+ยาป้องกันโรค", Vendor = "ร้านเกษตรสมบูรณ์" },
            new() { Id = Guid.NewGuid(), Date = today.AddMonths(-1), Amount = 1500m,  Category = "water",      Description = "ค่าน้ำประปาสำหรับระบบรดน้ำ" },
            new() { Id = Guid.NewGuid(), Date = today.AddDays(-10),  Amount = 4500m,  Category = "equipment",  Description = "ซ่อมเครื่องพ่นยา", Vendor = "อู่ซ่อมเกษตรภาคเหนือ" },
        };
        db.IncomeRecords.AddRange(incomes);
        db.ExpenseRecords.AddRange(expenses);

        var budget = new BudgetPlan
        {
            Id = Guid.NewGuid(), Period = $"{today.Year}-Q{(today.Month - 1) / 3 + 1}",
            TotalBudget = 50000m,
            CategoriesJson = """{"fertilizer":10000,"pesticide":5000,"labor":25000,"water":3000,"equipment":7000}"""
        };
        db.BudgetPlans.Add(budget);

        // ── Equipment ─────────────────────────────────────────────────────
        var equipment = new List<Equipment>
        {
            new() { Id = Guid.NewGuid(), Name = "รถไถคูโบต้า L3408",   EquipmentType = "tractor",          Brand = "Kubota",  Model = "L3408",  PurchaseDate = today.AddYears(-4), PurchaseCost = 480000m, Status = "operational", TotalHoursUsed = 850f,  NextMaintenanceHours = 1000f, NextMaintenanceDate = today.AddMonths(2) },
            new() { Id = Guid.NewGuid(), Name = "เครื่องพ่นยาแบบสะพาย", EquipmentType = "sprayer",          Brand = "Honda",   Model = "WJR-700", PurchaseDate = today.AddYears(-2), PurchaseCost = 15000m, Status = "operational", TotalHoursUsed = 320f,  NextMaintenanceHours = 500f,  NextMaintenanceDate = today.AddMonths(1) },
            new() { Id = Guid.NewGuid(), Name = "ปั๊มน้ำไฟฟ้า 2 HP",    EquipmentType = "irrigation_pump",  Brand = "Grundfos", Model = "CM3-5",  PurchaseDate = today.AddYears(-3), PurchaseCost = 12000m, Status = "operational", TotalHoursUsed = 1200f, NextMaintenanceHours = 1500f, NextMaintenanceDate = today.AddDays(15) },
            new() { Id = Guid.NewGuid(), Name = "รถบรรทุกขนาดเล็ก",     EquipmentType = "vehicle",          Brand = "Isuzu",   Model = "TFR",    PurchaseDate = today.AddYears(-6), PurchaseCost = 550000m, Status = "maintenance", TotalHoursUsed = 3200f, NextMaintenanceHours = 3500f, NextMaintenanceDate = today.AddDays(-5) },
        };
        db.Equipment.AddRange(equipment);

        var maintenances = new List<MaintenanceRecord>
        {
            new() { Id = Guid.NewGuid(), EquipmentId = equipment[0].Id, MaintenanceDate = today.AddMonths(-3), MaintenanceType = "oil_change",  Cost = 800m,  DoneBy = "ช่างกุ้ง",  Notes = "เปลี่ยนน้ำมันเครื่อง + กรองน้ำมัน",       NextDueDate = today.AddMonths(3) },
            new() { Id = Guid.NewGuid(), EquipmentId = equipment[1].Id, MaintenanceDate = today.AddMonths(-1), MaintenanceType = "inspection",  Cost = 300m,  DoneBy = "สมชาย ใจดี", Notes = "ตรวจสอบหัวพ่น ทำความสะอาดระบบ",             NextDueDate = today.AddMonths(2) },
            new() { Id = Guid.NewGuid(), EquipmentId = equipment[3].Id, MaintenanceDate = today.AddDays(-5),  MaintenanceType = "oil_change",  Cost = 1200m, DoneBy = "อู่เกษตร",   Notes = "เปลี่ยนน้ำมันเครื่อง+กรองอากาศ",           NextDueDate = today.AddMonths(3) },
        };
        db.MaintenanceRecords.AddRange(maintenances);

        var repairs = new List<RepairRecord>
        {
            new() { Id = Guid.NewGuid(), EquipmentId = equipment[1].Id, ReportedDate = today.AddDays(-15), RepairedDate = today.AddDays(-10), IssueDescription = "ท่อพ่นยาแตก รั่ว", RepairCost = 450m, RepairedBy = "อู่ซ่อมเกษตรภาคเหนือ", Status = "completed" },
            new() { Id = Guid.NewGuid(), EquipmentId = equipment[3].Id, ReportedDate = today.AddDays(-3),  RepairedDate = null,               IssueDescription = "แบตเตอรี่อ่อน สตาร์ทยาก",  RepairCost = 0m,    RepairedBy = "",                       Status = "in_repair" },
        };
        db.RepairRecords.AddRange(repairs);

        await db.SaveChangesAsync();
    }
}
