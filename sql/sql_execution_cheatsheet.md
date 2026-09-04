# The SQL Mental Model & Execution Cheatsheet

One of the biggest hurdles in SQL is that **we write the code in a completely different order than the database engine actually executes it.** 

To become a master at SQL, you must stop thinking about what you want to `SELECT`, and start thinking about where the data comes from and how it gets filtered step-by-step.

---

## 1. The Order of Execution (Lexical vs. Logical)

### How you TYPE it (Lexical Order):
1. `SELECT` (What columns do I want to see?)
2. `FROM` (What table is this in?)
3. `JOIN` (Are there other tables?)
4. `WHERE` (Filter the raw data)
5. `GROUP BY` (Aggregate the data)
6. `HAVING` (Filter the aggregated data)
7. `ORDER BY` (Sort the final output)
8. `LIMIT` (Show me top N rows)

### How the Database ENGINE executes it (Logical Order):
1. **`FROM` & `JOIN`**: First, the engine goes to the hard drive and loads the tables into memory. It joins them together into one massive virtual table.
2. **`WHERE`**: It immediately throws away any raw rows that don't match the condition. *(Note: You cannot use aliases created in the `SELECT` clause here, because `SELECT` hasn't happened yet!)*
3. **`GROUP BY`**: It squashes the remaining rows into buckets (e.g., grouping by department or artist).
4. **`HAVING`**: It filters the *buckets* (e.g., throwing away buckets that have a `SUM() < 100`).
5. **`SELECT`**: **Finally!** It picks the specific columns you asked for, applies math/functions, and assigns your `AS alias` names.
6. **`ORDER BY`**: It takes the final selected columns and sorts them. *(Because this happens after `SELECT`, you CAN use your aliases here!)*
7. **`LIMIT`**: It chops off the bottom rows and returns the result to your screen.

---

## 2. The Mental Pattern for Writing Code

When you face a complex SQL problem, **DO NOT start by writing `SELECT`**. 
Write your query in the order the engine thinks:

1. **"Where is the raw data coming from?"** -> Write your `FROM` and `JOIN`s first.
2. **"What raw rows do I not care about?"** -> Write your `WHERE` clause.
3. **"Do I need to summarize this data into categories?"** -> Write your `GROUP BY`.
4. **"Are there any summaries I want to throw away?"** -> Write your `HAVING`.
5. **"Okay, what exactly do I want to print on the screen?"** -> Now jump back to the top and write your `SELECT`.
6. **"How should it look?"** -> Write your `ORDER BY`.

---

## 3. CTEs (Common Table Expressions)

A CTE (using the `WITH` clause) is essentially a temporary named result set. Think of it as creating a mini-table on the fly that only exists for the duration of your query.

**Why use them?** 
They make complex queries readable. Instead of writing massive, deeply nested subqueries, you write a CTE at the top, and then query it at the bottom.

### Bootcamp Example: The Salary vs. Average Problem
**Scenario:** You have an `employees` table (columns: `emp_id`, `name`, `department`, `salary`). You want to find all employees who make MORE than the average salary of their specific department.

**The Solution using a CTE:**
```sql
-- Step 1: Create the CTE (The "Temporary Table")
WITH DepartmentAverages AS (
    SELECT 
        department,
        AVG(salary) AS avg_dept_salary
    FROM employees
    GROUP BY department
)

-- Step 2: Write your main query using the CTE you just made!
SELECT 
    e.name,
    e.department,
    e.salary,
    da.avg_dept_salary
FROM employees e
INNER JOIN DepartmentAverages da
    ON e.department = da.department
WHERE e.salary > da.avg_dept_salary;
```

### Bootcamp Example: Multi-Step CTE (The Pipeline)
You can chain multiple CTEs together. They execute sequentially.

**Scenario:** Find the top 3 customers who spent the most money in 2023, but only include customers who made more than 5 purchases.

```sql
WITH CustomerPurchases AS (
    -- CTE 1: Filter to 2023 and count purchases
    SELECT 
        customer_id,
        COUNT(order_id) as total_orders,
        SUM(total_amount) as total_spent
    FROM orders
    WHERE EXTRACT(YEAR FROM order_date) = 2023
    GROUP BY customer_id
),
LoyalCustomers AS (
    -- CTE 2: Filter CTE 1 to only keep people with > 5 orders
    SELECT *
    FROM CustomerPurchases
    WHERE total_orders > 5
)

-- Main Query: Get the top 3 spenders from CTE 2
SELECT 
    c.customer_name,
    lc.total_orders,
    lc.total_spent
FROM LoyalCustomers lc
INNER JOIN customers c 
    ON lc.customer_id = c.customer_id
ORDER BY lc.total_spent DESC
LIMIT 3;
```

---

## 4. Key Rules to Memorize
1. **`WHERE` vs `HAVING`**: 
   - `WHERE` filters *raw rows* before grouping.
   - `HAVING` filters *aggregated buckets* after grouping.
2. **Aliases in `WHERE`**: 
   - You **cannot** use `SELECT` aliases in the `WHERE` or `GROUP BY` clauses because they haven't been processed yet.
   - You **can** use aliases in `ORDER BY`.
3. **Window Functions (`OVER()`)**:
   - Window functions (like `RANK() OVER(PARTITION BY...)`) happen at the very end of the `SELECT` phase, just before `ORDER BY`. You cannot put them in a `WHERE` clause! (If you need to filter by a rank, you must put the ranking in a CTE first, and then filter it in the main query).
