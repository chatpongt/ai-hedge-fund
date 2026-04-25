using FruitGardenApi.Data;
using FruitGardenApi.Models.Finance;
using Microsoft.EntityFrameworkCore;

namespace FruitGardenApi.Repositories;

public class FinanceRepository(AppDbContext db) : IFinanceRepository
{
    public Task<List<IncomeRecord>> GetIncomeAsync(DateOnly? from = null, DateOnly? to = null)
    {
        var q = db.IncomeRecords.AsQueryable();
        if (from.HasValue) q = q.Where(r => r.Date >= from.Value);
        if (to.HasValue) q = q.Where(r => r.Date <= to.Value);
        return q.OrderByDescending(r => r.Date).ToListAsync();
    }

    public async Task<IncomeRecord> CreateIncomeAsync(IncomeRecord record)
    {
        db.IncomeRecords.Add(record);
        await db.SaveChangesAsync();
        return record;
    }

    public Task<List<ExpenseRecord>> GetExpensesAsync(DateOnly? from = null, DateOnly? to = null, string? category = null)
    {
        var q = db.ExpenseRecords.AsQueryable();
        if (from.HasValue) q = q.Where(r => r.Date >= from.Value);
        if (to.HasValue) q = q.Where(r => r.Date <= to.Value);
        if (category != null) q = q.Where(r => r.Category == category);
        return q.OrderByDescending(r => r.Date).ToListAsync();
    }

    public async Task<ExpenseRecord> CreateExpenseAsync(ExpenseRecord record)
    {
        db.ExpenseRecords.Add(record);
        await db.SaveChangesAsync();
        return record;
    }

    public Task<BudgetPlan?> GetBudgetAsync(string period) =>
        db.BudgetPlans.FirstOrDefaultAsync(b => b.Period == period);

    public async Task<BudgetPlan> UpsertBudgetAsync(BudgetPlan plan)
    {
        var existing = await db.BudgetPlans.FirstOrDefaultAsync(b => b.Period == plan.Period);
        if (existing != null)
        {
            existing.TotalBudget = plan.TotalBudget;
            existing.CategoriesJson = plan.CategoriesJson;
            existing.UpdatedAt = DateTime.UtcNow;
            db.BudgetPlans.Update(existing);
            await db.SaveChangesAsync();
            return existing;
        }
        db.BudgetPlans.Add(plan);
        await db.SaveChangesAsync();
        return plan;
    }
}
