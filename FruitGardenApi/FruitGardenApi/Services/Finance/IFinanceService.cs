using FruitGardenApi.Models.Finance;

namespace FruitGardenApi.Services.Finance;

public record FinanceSummary(decimal TotalIncome, decimal TotalExpense, decimal NetProfit, decimal ROI);
public record MonthlyReport(string Month, decimal Income, decimal Expense, decimal Profit);

public interface IFinanceService
{
    Task<FinanceSummary> GetSummaryAsync(DateOnly? from = null, DateOnly? to = null);
    Task<List<IncomeRecord>> GetIncomeAsync(DateOnly? from = null, DateOnly? to = null);
    Task<IncomeRecord> CreateIncomeAsync(IncomeRecord record);
    Task<List<ExpenseRecord>> GetExpensesAsync(DateOnly? from = null, DateOnly? to = null, string? category = null);
    Task<ExpenseRecord> CreateExpenseAsync(ExpenseRecord record);
    Task<List<MonthlyReport>> GetMonthlyReportAsync(int months = 6);
    Task<BudgetPlan?> GetBudgetAsync(string period);
    Task<BudgetPlan> UpsertBudgetAsync(BudgetPlan plan);
}
