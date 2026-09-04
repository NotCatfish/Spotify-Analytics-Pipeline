# The Ultimate SQL Masterclass: 0 to Expert Guide

This document is structured to mirror a comprehensive 20-30 hour premium SQL Bootcamp. It moves sequentially from the absolute basics of retrieving data to advanced data engineering concepts like Window Functions, Database Design, and Triggers.

---

## MODULE 1: The Basics (Retrieving & Filtering)

Before you can manipulate data, you must know how to pull exactly what you want from a single table.

### 1. The `SELECT` Statement

The foundation of all queries.

```sql
-- Select everything
SELECT * FROM employees;

-- Select specific columns and do basic math
SELECT 
    first_name, 
    last_name, 
    salary,
    salary * 1.10 AS projected_salary -- The AS keyword creates an 'alias'
FROM employees;
```

### 2. The `WHERE` Clause (Filtering)

```sql
-- Standard Operators: =, >, <, >=, <=, != or <>
SELECT * FROM orders WHERE total_amount > 100;

-- IN: Check against a list of values
SELECT * FROM customers WHERE state IN ('CA', 'NY', 'TX');

-- BETWEEN: Inclusive range
SELECT * FROM employees WHERE hire_date BETWEEN '2023-01-01' AND '2023-12-31';

-- LIKE: Pattern matching ( % = any number of chars, _ = exactly one char )
SELECT * FROM users WHERE email LIKE '%@gmail.com';
SELECT * FROM employees WHERE phone LIKE '555-____';

-- IS NULL: Check for missing data
SELECT * FROM shipments WHERE delivery_date IS NULL;
```

### 3. Sorting and Limiting

```sql
SELECT first_name, salary 
FROM employees
ORDER BY salary DESC, first_name ASC -- Sorts by salary highest to lowest. If tied, alphabetical.
LIMIT 5; -- Only show the top 5
```

---

## MODULE 2: Summarizing Data (Aggregations)

### 1. Aggregate Functions

Math operations that compress multiple rows into a single value.

* `COUNT()`: Number of rows
* `SUM()`: Total sum
* `AVG()`: Average
* `MAX()` / `MIN()`: Highest / Lowest

```sql
SELECT 
    COUNT(*) AS total_employees,
    AVG(salary) AS avg_salary,
    MAX(salary) AS highest_salary
FROM employees;
```

### 2. `GROUP BY` & `HAVING`

When you want to aggregate by a category (e.g., average salary *per department*).

```sql
SELECT 
    department_id,
    COUNT(*) AS employee_count,
    AVG(salary) AS avg_dept_salary
FROM employees
GROUP BY department_id
HAVING AVG(salary) > 60000; -- HAVING filters the aggregated buckets!
```

*(Mental Rule: `WHERE` filters before grouping. `HAVING` filters after grouping.)*

---

## MODULE 3: Relational Data (The Joins)

Relational databases store data across multiple tables using **Primary Keys** (the unique ID of a row) and **Foreign Keys** (a reference to another table's Primary Key).

### 1. INNER JOIN (The Default)

Returns only rows where there is a match in BOTH tables.

```sql
SELECT 
    o.order_id,
    c.customer_name,
    o.total_amount
FROM orders o
INNER JOIN customers c 
    ON o.customer_id = c.customer_id;
```

### 2. LEFT JOIN (Outer Join)

Returns ALL rows from the Left table, and matches from the Right table. If there's no match, the Right table columns will be `NULL`.

```sql
-- Find all customers, and their orders IF they have any (shows NULL for customers with 0 orders)
SELECT 
    c.customer_name,
    o.order_id
FROM customers c
LEFT JOIN orders o 
    ON c.customer_id = o.customer_id;
```

### 3. Other Joins (Rarely Used but important to know)

* **RIGHT JOIN**: The reverse of a LEFT JOIN.
* **FULL OUTER JOIN**: Returns everything from both tables. Missing matches become `NULL`.
* **CROSS JOIN**: Pairs every row in Table A with every row in Table B (Cartesian Product).
* **SELF JOIN**: Joining a table to itself (e.g., finding an employee's manager within the same `employees` table).

---

## MODULE 4: Subqueries & CTEs

### 1. Subqueries

A query nested inside another query.

**In the WHERE clause:**

```sql
-- Find employees who make more than the company average
SELECT name, salary 
FROM employees 
WHERE salary > (SELECT AVG(salary) FROM employees);
```

**In the SELECT clause:**

```sql
-- Compare each salary to the max salary
SELECT 
    name, 
    salary,
    (SELECT MAX(salary) FROM employees) AS company_max
FROM employees;
```

### 2. CTEs (Common Table Expressions)

The modern, readable replacement for complex subqueries. (See the previous cheatsheet for the full mental model!)

```sql
WITH HighEarners AS (
    SELECT emp_id, name FROM employees WHERE salary > 100000
)
SELECT * FROM HighEarners;
```

---

## MODULE 5: Advanced Built-In Functions

### 1. `CASE WHEN` (SQL's IF/ELSE)

```sql
SELECT 
    order_id,
    total_amount,
    CASE 
        WHEN total_amount > 1000 THEN 'High Value'
        WHEN total_amount BETWEEN 500 AND 1000 THEN 'Medium Value'
        ELSE 'Low Value'
    END AS order_tier
FROM orders;
```

### 2. String Manipulation

```sql
SELECT 
    CONCAT(first_name, ' ', last_name) AS full_name,
    UPPER(email) AS upper_email,
    SUBSTRING(phone, 1, 3) AS area_code, -- Extracts first 3 characters
    REPLACE(department, 'Dept', 'Department') AS clean_dept
FROM employees;
```

### 3. Date Manipulation

*(Syntax varies heavily between PostgreSQL, MySQL, and SQL Server. This is standard PostgreSQL)*

```PostgreSQL
SELECT 
    order_date,
    EXTRACT(YEAR FROM order_date) AS order_year,
    EXTRACT(MONTH FROM order_date) AS order_month,
    order_date + INTERVAL '30 days' AS payment_due_date
FROM orders;
```

---

## MODULE 6: Window Functions (The Heavy Lifters)

Window functions perform calculations across a set of rows related to the current row. **Unlike `GROUP BY`, they do NOT squash the rows together.**

### 1. `OVER(PARTITION BY ...)`

Compare an individual row to the aggregate of its group, without losing the individual row data.

```sql
SELECT 
    name,
    department,
    salary,
    AVG(salary) OVER(PARTITION BY department) AS avg_dept_salary,
    salary - AVG(salary) OVER(PARTITION BY department) AS difference_from_avg
FROM employees;
```

### 2. Ranking Functions

```sql
SELECT 
    name,
    department,
    salary,
    -- Ranks salaries 1, 2, 3 within EACH department
    RANK() OVER(PARTITION BY department ORDER BY salary DESC) AS dept_rank
FROM employees;
```

### 3. `LEAD()` and `LAG()`

Fetch data from the next or previous row. Crucial for calculating month-over-month growth.

```sql
SELECT 
    month,
    revenue,
    LAG(revenue) OVER(ORDER BY month ASC) AS previous_month_revenue,
    revenue - LAG(revenue) OVER(ORDER BY month ASC) AS month_over_month_growth
FROM monthly_sales;
```

---

## MODULE 7: Creating & Modifying Data (DML)

Up to now, we only read data. Now we change it.

### 1. INSERT

```sql
INSERT INTO customers (customer_name, email, city)
VALUES 
    ('John Doe', 'john@test.com', 'New York'),
    ('Jane Smith', 'jane@test.com', 'Chicago');
```

### 2. UPDATE

**CRITICAL:** Always include a `WHERE` clause, or you will overwrite the entire table!

```sql
UPDATE employees
SET salary = salary * 1.05, department = 'Sales'
WHERE emp_id = 45;
```

### 3. DELETE

**CRITICAL:** Always include a `WHERE` clause!

```sql
DELETE FROM orders
WHERE order_status = 'Cancelled';
```

---

## MODULE 8: Database Design (DDL)

### 1. Creating Tables & Constraints

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY, -- Auto-incrementing unique ID
    username VARCHAR(50) NOT NULL UNIQUE, -- Cannot be empty, must be unique
    email VARCHAR(255) NOT NULL,
    age INT CHECK (age >= 18), -- Must be 18 or older
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Foreign Keys

Enforcing referential integrity (You can't create an order for a customer_id that doesn't exist).

```sql
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT,
    total DECIMAL(10, 2),
    FOREIGN KEY (customer_id) REFERENCES users(user_id) ON DELETE CASCADE
    -- ON DELETE CASCADE means if the user is deleted, all their orders are auto-deleted.
);
```

---

## MODULE 9: Advanced Database Objects

### 1. Views

A saved query that acts like a virtual table. Great for security (hiding sensitive columns) or convenience.

```sql
-- Create it once
CREATE VIEW active_customers AS
SELECT * FROM customers WHERE status = 'Active';

-- Query it forever like a normal table
SELECT * FROM active_customers;
```

### 2. Stored Procedures

Saved blocks of SQL code that can take parameters. Used for automating tasks (like an ETL job).

```sql
-- PostgreSQL Syntax
CREATE OR REPLACE PROCEDURE give_department_raise(dept_name VARCHAR, raise_percent DECIMAL)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE employees 
    SET salary = salary * (1 + raise_percent)
    WHERE department = dept_name;
END;
$$;

-- Run it
CALL give_department_raise('Engineering', 0.10);
```

### 3. Indexes

Indexes are like the index at the back of a textbook. They make reading (`SELECT`) incredibly fast, but slow down writing (`INSERT`/`UPDATE`) because the index must be updated.

```sql
-- Create an index on the email column so login queries are blazing fast
CREATE INDEX idx_user_email ON users(email);
```

---

*End of Masterclass. Reference this document whenever you need to recall syntax for advanced analytical queries or database design!*
