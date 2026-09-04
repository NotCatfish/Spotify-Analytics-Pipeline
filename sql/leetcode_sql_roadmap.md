```pgsql
-- Write your PostgreSQL query statement below
SELECT
    d.name AS Department,
    e.name AS Employee,
    e.salary as Salary
FROM Employee e
INNER JOIN Department d
ON e.departmentId=d.id
GROUP BY e.Salary
ORDER BY e.Salary DESC;
```

```pgsql
-- Write your PostgreSQL query statement below
SELECT
    TO_CHAR(trans_date,'YYYY-MM') AS month,
    country,
    COUNT(id) AS trans_count ,
    COUNT(CASE WHEN state='approved' THEN 1 END) AS approved_count ,
    SUM(amount) AS trans_total_amount  ,
    SUM(CASE WHEN state='approved' THEN amount ELSE 0 END) AS approved_total_amount 
FROM Transactions
GROUP BY country,month
ORDER BY month ASC;
```

```pgsql
SELECT
    actor_id,
    director_id
FROM ActorDirector
GROUP BY actor_id,director_id
HAVING COUNT(actor_id,Director_id) >2
```

```pgsql
-- Write your PostgreSQL query statement below
SELECT
    player_id,
    MIN(event_date) AS first_login
FROM Activity
GROUP BY player_id
```

```pgsql
-- Write your PostgreSQL query statement below
SELECT
    uniq.unique_id,
    emp.name
FROM EmployeeUNI uniq
RIGHT JOIN Employees emp
ON emp.id=uniq.id;
```

# 🚀 LeetCode SQL Mastery Roadmap

This roadmap contains the most highly-rated, frequently asked LeetCode SQL problems. If you complete this list, you will have mastered 90% of the SQL concepts required for Data Analyst and Data Engineering interviews.

**Instructions:**

1. Search the problem number on LeetCode (or filter by "Database").
2. Check the box `[x]` when you pass all test cases.
3. Paste your successful code in the empty code blocks below each question to build your personal cheat sheet!

---

## LEVEL 1: The Bare Basics (Filtering & Joins)

*Concepts: `SELECT`, `WHERE`, `INNER JOIN`, `LEFT JOIN`, `IS NULL`*

- [X] **175. Combine Two Tables** (Easy)

```sql
-- Paste your passing code he-- Write your PostgreSQL query statement below
SELECT 
    p.firstName,
    p.lastName,
    a.city,
    a.state
FROM Person p
LEFT JOIN Address a
ON p.personId=a.personIdre:
```

- [X] **183. Customers Who Never Order** (Easy)

```sql
-- Paste your pas-- Write your PostgreSQL query statement below
SELECT 
    c.name AS Customers 
FROM Customers c
LEFT JOIN Orders o
ON c.id=o.customerId 
WHERE o.id IS NULL;sing code here:
```

- [X] **1148. Article Views I** (Easy)

```sql
-- Write your PostgreSQL query statement below
SELECT DISTINCT
    author_id AS id
FROM Views
WHERE author_id=viewer_id
ORDER BY id ASC;
```

- [X] **1378. Replace Employee ID With The Unique Identifier** (Easy)

```sql
-- Paste your -- Write your PostgreSQL query statement below
SELECT
    uniq.unique_id,
    emp.name
FROM EmployeeUNI uniq
RIGHT JOIN Employees emp
ON emp.id=uniq.id;passing code here:
```

---

## LEVEL 2: Aggregation & Grouping

*Concepts: `GROUP BY`, `HAVING`, `MIN()`, `MAX()`, `COUNT(DISTINCT)`*

- [X] **511. Game Play Analysis I** (Easy)

```sql
-- Paste your-- Write your PostgreSQL query statement below
SELECT
    player_id,
    MIN(event_date) AS first_login
FROM Activity
GROUP BY player_id passing code here:
```

- [X] **1050. Actors and Directors Who Cooperated At Least Three Times** (Easy)

```sql
-- Paste your passing -- Write your PostgreSQL query statement below
SELECT
    actor_id,
    director_id
FROM ActorDirector
GROUP BY actor_id,director_id
HAVING COUNT(*) >2 here:
```

- [X] **1693. Daily Leads and Partners** (Easy)

```pgsql
-- Write your PostgreSQL query statement below
SELECT
    e1.name AS Employee
FROM Employee e1
JOIN Employee e2 ON e1.managerId = e2.id
WHERE e1.salary > e2.salary
```

```sql
-- Paste your passing -- Write your PostgreSQL query statement below
SELECT 
    date_id,
    make_name,
    COUNT(DISTINCT lead_id) AS unique_leads,
    COUNT(DISTINCT partner_id) AS unique_Partners
FROM DailySales
GROUP BY make_name,date_id;code here:
```

---

## LEVEL 3: Relational Logic & Self Joins

*Concepts: Joining a table to itself using aliases, Date manipulation*

- [X] **181. Employees Earning More Than Their Managers** (Easy)

```sql
-- Paste your passing code here:-- Write your PostgreSQL query statement below
SELECT
    e1.name AS Employee
FROM Employee e1
JOIN Employee e2 ON e1.managerId = e2.id
WHERE e1.salary > e2.salary
```

- [X] **196. Delete Duplicate Emails** (Easy)

```sql
-- Paste your paDELETE FROM Person
WHERE id NOT IN(
    SELECT MIN(id)
    FROM Person
    GROUP BY email
)ssing code here:
```

- [X] **197. Rising Temperature** (Easy)

```sql
-- Paste your -- Write your PostgreSQL query statement below
SELECT 
    id
FROM(
    SELECT
        id,
        recordDate,
        temperature,
        LAG(temperature) OVER( ORDER BY recordDate ASC) AS prev_temp,
        LAG(recordDate) OVER( ORDER BY recordDate ASC) AS prev_date
    FROM Weather
) AS Temp_table
WHERE temperature>prev_temp AND recordDate-prev_date=1;passing code here:
```

---

## LEVEL 4: Advanced Aggregation & Math

*Concepts: `CASE WHEN` inside `SUM()`, Subqueries, Advanced Filtering*

- [X] **1193. Monthly Transactions I** (Medium)

```PostgreSQL
-- Write your PostgreSQL query statement below
SELECT 
    ROUND(SUM(CASE WHEN order_date=customer_pref_delivery_date THEN 1 ELSE 0 END)*100.0/COUNT( DISTINCT customer_id),2) AS immediate_percentage 
FROM(
    SELECT DISTINCT ON(customer_id)
        order_date,
        customer_pref_delivery_date,
        customer_id
    FROM Delivery
    ORDER BY customer_id,order_date ASC
) AS First_order_table;
```

- [X] **1174. Immediate Food Delivery II** (Medium)

```PostgreSQL
-- Paste your pas-- Write your PostgreSQL query statement below
SELECT 
    ROUND(SUM(CASE WHEN order_date=customer_pref_delivery_date THEN 1 ELSE 0 END)*100.0/COUNT( DISTINCT customer_id),2) AS immediate_percentage 
FROM(
    SELECT DISTINCT ON(customer_id)
        order_date,
        customer_pref_delivery_date,
        customer_id
    FROM Delivery
    ORDER BY customer_id,order_date ASC
) AS First_order_table;
sing code here:
```

- [X] **1045. Customers Who Bought All Products** (Medium)

```sql
-- Paste your passi-- Write your PostgreSQL query statement below
SELECT
    customer_id
FROM Customer 
GROUP BY customer_id
HAVING COUNT(DISTINCT product_key)=(SELECT COUNT(product_key) FROM Product);ng code here:
```

---

## LEVEL 5: Window Functions & CTEs (The Boss Level)

*Concepts: `WITH ... AS ()`, `RANK()`, `DENSE_RANK()`, `PARTITION BY`*

- [X] **176. Second Highest Salary** (Medium)

```sql
-- Paste your pa-- Write your PostgreSQL query statement below
SELECT DISTINCT ON(salary)
    salary AS SecondHighestSalary  
FROM Employee
ORDER BY salary DESc
LIMIT 1 OFFSET 1; ssing code here:
```

- [X] **184. Department Highest Salary** (Medium)

```sql
-- Paste your passing code here:SELECT
    dept.name AS Department,
    emp.name AS Employee,
    salary AS Salary
FROM Employee emp
INNER JOIN Department dept
ON dept.id=emp.departmentId
WHERE (emp.departmentID,emp.salary) IN (
    SELECT 
        departmentId,
        MAX(salary)
    FROM Employee
    GROUP BY departmentID
);
```

- [X] **185. Department Top Three Salaries** (Hard)

```sql
-- Paste your pass-- Write your PostgreSQL query statement below
WITH top_three_employee AS(
    SELECT
        DENSE_RANK() OVER(PARTITION BY departmentID ORDER BY salary DESC) AS Rank,
        name,
        salary,
        departmentId
    FROM Employee
)
SELECT
    dept.name AS Department,
    emp.name AS Employee,
    emp.salary AS Salary
FROM top_three_employee emp 
INNER JOIN Department dept
ON emp.departmentId=dept.id
WHERE emp.Rank BETWEEN 1 AND 3;
ing code here:
```

- [X] **601. Human Traffic of Stadium** (Hard)

```sql
-- Paste your pass-- Write your PostgreSQL query statement below
WITH dates_with_over_hund AS(
    SELECT
        *,
        (id-ROW_NUMBER() OVER(ORDER BY id)) AS group_id
    FROM Stadium
    WHERE people>=100
)
SELECT
    id,
    visit_date,
    people
FROM dates_with_over_hund
WHERE group_id IN(
    SELECT group_id 
    FROM dates_with_over_hund 
    GROUP BY group_id 
    HAVING COUNT(*) >= 3
)
ORDER BY visit_date ASC;ing code here:
```

- [ ] **262. Trips and Users** (Hard)

```sql
-- Paste your passing code here:
```
