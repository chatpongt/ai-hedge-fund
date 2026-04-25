using FruitGardenApi.Data;
using Microsoft.AspNetCore.Mvc;

namespace FruitGardenApi.Controllers;

[ApiController]
[Route("api/mock")]
public class MockController(AppDbContext db) : ControllerBase
{
    [HttpPost("seed")]
    public async Task<IActionResult> Seed()
    {
        await DataSeeder.SeedAsync(db);
        return Ok(new { message = "ข้อมูลตัวอย่างถูกสร้างเรียบร้อยแล้ว" });
    }

    [HttpDelete("reset")]
    public async Task<IActionResult> Reset()
    {
        await db.Database.EnsureDeletedAsync();
        await db.Database.EnsureCreatedAsync();
        await DataSeeder.SeedAsync(db);
        return Ok(new { message = "รีเซ็ตและสร้างข้อมูลตัวอย่างใหม่แล้ว" });
    }
}
