using FruitGardenApi.Models.Finance;
using FruitGardenApi.Repositories;

namespace FruitGardenApi.Services.Finance;

public class FinanceService(IFinanceRepository repo) : IFinanceService
{
    public async Task<FinanceSummary> GetSummaryAsync(DateOnly? from = null, DateOnly? to = null)
    {
        var income = await repo.GetIncomeAsync(from, to);
        var expenses = await repo.GetExpensesAsync(from, to);
        var totalIncome = income.Sum(i => i.Amount);
        var totalExpense = expenses.Sum(e => e.Amount);
        var roi = totalExpense > 0 ? Math.Round((totalIncome - totalExpense) / totalExpense * 100m, 2) : 0m;
        return new FinanceSummary(totalIncome, totalExpense, totalIncome - totalExpense, roi);
    }

    public Task<List<IncomeRecord>> GetIncomeAsync(DateOnly? from = null, DateOnly? to = null) =>
        repo.GetIncomeAsync(from, to);

    public Task<IncomeRecord> CreateIncomeAsync(IncomeRecord record) =>
        repo.CreateIncomeAsync(record);

    public Task<List<ExpenseRecord>> GetExpensesAsync(DateOnly? from = null, DateOnly? to = null, string? category = null) =>
        repo.GetExpensesAsync(from, to, category);

    public Task<ExpenseRecord> CreateExpenseAsync(ExpenseRecord record) =>
        repo.CreateExpenseAsync(record);

    public async Task<List<MonthlyReport>> GetMonthlyReportAsync(int months = 6)
    {
        var from = DateOnly.FromDateTime(DateTime.Today.AddMonths(-months));
        var income = await repo.GetIncomeAsync(from);
        var expenses = await repo.GetExpensesAsync(from);

        return Enumerable.Range(0, months)
            .Select(i => DateOnly.FromDateTime(DateTime.Today.AddMonths(-months + i + 1)))
            .Select(date =>
            {
                var monthIncome = income.Where(r => r.Date.Year == date.Year && r.Date.Month == date.Month).Sum(r => r.Amount);
                var monthExpense = expenses.Where(r => r.Date.Year == date.Year && r.Date.Month == date.Month).Sum(r => r.Amount);
                return new MonthlyReport($"{date.Year}-{date.Month:D2}", monthIncome, monthExpense, monthIncome - monthExpense);
            })
            .ToList();
    }

    public Task<BudgetPlan?> GetBudgetAsync(string period) => repo.GetBudgetAsync(period);
    public Task<BudgetPlan> UpsertBudgetAsync(BudgetPlan plan) => repo.UpsertBudgetAsync(plan);
}
