using FruitGardenApi.Models.Finance;
using FruitGardenApi.Services.Finance;
using Microsoft.AspNetCore.Mvc;

namespace FruitGardenApi.Controllers;

[ApiController]
[Route("api/finance")]
public class FinanceController(IFinanceService svc) : ControllerBase
{
    [HttpGet("summary")]
    public async Task<IActionResult> GetSummary([FromQuery] DateOnly? from = null, [FromQuery] DateOnly? to = null) =>
        Ok(await svc.GetSummaryAsync(from, to));

    [HttpGet("income")]
    public async Task<IActionResult> GetIncome([FromQuery] DateOnly? from = null, [FromQuery] DateOnly? to = null) =>
        Ok(await svc.GetIncomeAsync(from, to));

    [HttpPost("income")]
    public async Task<IActionResult> CreateIncome([FromBody] IncomeRecord record) =>
        CreatedAtAction(nameof(GetIncome), await svc.CreateIncomeAsync(record));

    [HttpGet("expenses")]
    public async Task<IActionResult> GetExpenses([FromQuery] DateOnly? from = null, [FromQuery] DateOnly? to = null, [FromQuery] string? category = null) =>
        Ok(await svc.GetExpensesAsync(from, to, category));

    [HttpPost("expenses")]
    public async Task<IActionResult> CreateExpense([FromBody] ExpenseRecord record) =>
        CreatedAtAction(nameof(GetExpenses), await svc.CreateExpenseAsync(record));

    [HttpGet("reports/monthly")]
    public async Task<IActionResult> GetMonthlyReport([FromQuery] int months = 6) =>
        Ok(await svc.GetMonthlyReportAsync(months));

    [HttpGet("budget")]
    public async Task<IActionResult> GetBudget([FromQuery] string period)
    {
        var budget = await svc.GetBudgetAsync(period);
        return budget is null ? NotFound() : Ok(budget);
    }

    [HttpPut("budget")]
    public async Task<IActionResult> UpsertBudget([FromBody] BudgetPlan plan) =>
        Ok(await svc.UpsertBudgetAsync(plan));
}
