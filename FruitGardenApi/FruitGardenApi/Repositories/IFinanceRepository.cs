using FruitGardenApi.Models.Finance;

namespace FruitGardenApi.Repositories;

public interface IFinanceRepository
{
    Task<List<IncomeRecord>> GetIncomeAsync(DateOnly? from = null, DateOnly? to = null);
    Task<IncomeRecord> CreateIncomeAsync(IncomeRecord record);
    Task<List<ExpenseRecord>> GetExpensesAsync(DateOnly? from = null, DateOnly? to = null, string? category = null);
    Task<ExpenseRecord> CreateExpenseAsync(ExpenseRecord record);
    Task<BudgetPlan?> GetBudgetAsync(string period);
    Task<BudgetPlan> UpsertBudgetAsync(BudgetPlan plan);
}
