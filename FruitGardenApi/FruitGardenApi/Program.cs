using FruitGardenApi.Data;
using FruitGardenApi.Repositories;
using FruitGardenApi.Services.Garden;
using FruitGardenApi.Services.Finance;
using FruitGardenApi.Services.HR;
using FruitGardenApi.Services.Equipment;
using FruitGardenApi.Agents;
using Microsoft.EntityFrameworkCore;
using Microsoft.SemanticKernel;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "Fruit Garden API", Version = "v1", Description = "ระบบบริหารจัดการสวนผลไม้" });
});

// Database
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection")));

// CORS
var allowedOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>() ?? [];
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
        policy.WithOrigins(allowedOrigins)
              .AllowAnyHeader()
              .AllowAnyMethod());
});

// Repositories
builder.Services.AddScoped<IGardenRepository, GardenRepository>();
builder.Services.AddScoped<IFinanceRepository, FinanceRepository>();
builder.Services.AddScoped<IHRRepository, HRRepository>();
builder.Services.AddScoped<IEquipmentRepository, EquipmentRepository>();

// Services
builder.Services.AddScoped<IGardenService, GardenService>();
builder.Services.AddScoped<IAnalysisService, AnalysisService>();
builder.Services.AddScoped<IFinanceService, FinanceService>();
builder.Services.AddScoped<IHRService, HRService>();
builder.Services.AddScoped<IEquipmentService, EquipmentService>();

// Semantic Kernel
var openAiKey = builder.Configuration["SemanticKernel:OpenAI:ApiKey"];
var modelId = builder.Configuration["SemanticKernel:OpenAI:ModelId"] ?? "gpt-4o-mini";

if (!string.IsNullOrEmpty(openAiKey))
{
    builder.Services.AddSingleton(sp =>
        Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(modelId, openAiKey)
            .Build());
}
else
{
    // No LLM key — agents will use rule-based scoring
    builder.Services.AddSingleton<Kernel?>(_ => null);
}

// SK Plugins (scoped so they can inject repositories)
builder.Services.AddScoped<WateringPlugin>();
builder.Services.AddScoped<PestDetectionPlugin>();
builder.Services.AddScoped<HarvestPredictorPlugin>();
builder.Services.AddScoped<DiseaseMonitorPlugin>();
builder.Services.AddScoped<GardenAnalysisOrchestrator>();

var app = builder.Build();

// Migrate and seed database on startup
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated();
    await FruitGardenApi.Data.DataSeeder.SeedAsync(db);
}

app.UseSwagger();
app.UseSwaggerUI(c =>
{
    c.SwaggerEndpoint("/swagger/v1/swagger.json", "Fruit Garden API v1");
    c.RoutePrefix = "swagger";
});

app.UseHttpsRedirection();
app.UseCors();
app.UseAuthorization();
app.MapControllers();

app.Run();
