# dbas

### Accessing the Database
psql -h psql-dd1368-ht23.sys.kth.se

## Labb 1

### Queer

1. SELECT FullName FROM lib_user;
2. SELECT * FROM borrowing; SELECT * FROM borrowing WHERE dateofreturn IS NULL;
3. SELECT Title FROM book;  SELECT * FROM book WHERE title = 'Harry Potter and the Philosopher''s Stone';
4. SELECT * FROM fines; 

## Labb 2

### Assignment 1

```
SELECT
  b.title,
  STRING_AGG(g.genre, ', ') AS genre
FROM
  books b
JOIN
  genre g ON b.bookid = g.bookid
GROUP BY
  b.title
ORDER BY
  CAST(b.title AS BYTEA);
```

### Assignment 2

```
WITH BorrowCount AS (
    SELECT 
      b.bookid, 
      b.title, 
      COUNT(bor.physicalid) AS borrowCount
    FROM 
      books b
    JOIN 
      resources r ON b.bookid = r.bookid
    JOIN 
      borrowing bor ON r.physicalid = bor.physicalid
      WHERE b.bookid IN (SELECT bookid FROM genre WHERE genre = 'RomCom')
    GROUP BY 
      b.bookid, b.title
)
SELECT 
  title,
  rank
FROM (
  SELECT 
    title, 
    RANK() OVER (ORDER BY borrowCount DESC) AS rank
  FROM 
    BorrowCount
) AS ranked_data
WHERE rank <= 5;
```

### Assignment 3

```
WITH weekly_data AS (
    SELECT
        EXTRACT(WEEK FROM dob) AS week,
        COUNT(borrowingid) AS borrowed,
        0 AS returned,
        0 AS late
    FROM
        borrowing
    GROUP BY
        week

    UNION

    SELECT
        EXTRACT(WEEK FROM dor) AS week,
        0 AS borrowed,
        COUNT(borrowingid) AS returned,
        COUNT(CASE WHEN dor > doe THEN borrowingid END) AS late
    FROM
        borrowing
    GROUP BY
        week
)
SELECT
    week,
    SUM(borrowed) AS borrowed,
    SUM(returned) AS returned,
    SUM(late) AS late
FROM
    weekly_data
WHERE
    week <= 30
GROUP BY
    week
ORDER BY
    week;
```

### Assignment 4

```
SELECT
    b.title,
    EVERY(p.prequelid IS NOT NULL) AS every,
    bor.dob
FROM
    books b
JOIN
    resources r ON b.bookid = r.bookid
LEFT JOIN
    prequels p ON b.bookid = p.bookid
JOIN
    borrowing bor ON r.physicalid = bor.physicalid
WHERE
    EXTRACT(MONTH FROM bor.dob) = 2
GROUP BY
    b.title, bor.dob
ORDER BY
  CAST(b.title AS BYTEA);
  ```
  
  ### Assignment 5

```
WITH RECURSIVE BookHierarchy AS (

  SELECT
    b.title,
    b.bookid,
    p.prequelid
  FROM
    books b
  LEFT JOIN
    prequels p ON b.bookid = p.bookid
  WHERE
    b.bookid = 8713
  
  UNION
  
  SELECT
    b.title,
    b.bookid,
    p.prequelid
  FROM
    books b
  LEFT JOIN
    prequels p ON b.bookid = p.bookid
  JOIN
    BookHierarchy bh ON (b.bookid = bh.prequelid OR p.prequelid = bh.bookid)
)
SELECT * FROM BookHierarchy;
```

### P+

```
WITH BookBorrowing AS (
    SELECT
        a.author,
        MAX(CASE WHEN EXISTS (
                SELECT 
                  r.physicalid
                FROM 
                  resources r
                JOIN 
                  borrowing b ON r.physicalid = b.physicalid
                WHERE 
                  r.bookid = a.bookid
                AND EXTRACT(MONTH FROM b.dor) = 5
            ) THEN 1
            ELSE 0
        END)::BOOLEAN AS "true/false"
    FROM
        author a
    GROUP BY
        a.author
)
SELECT
    author,
    "true/false"
FROM
    BookBorrowing
ORDER BY
    "true/false" DESC, author;
```

## Labb 3

### P Assignments

#### Querie 1

```
SELECT
    c.Name AS name,
    COUNT(*) AS num
FROM
    Country c
JOIN
    borders b ON c.Code = b.Country1 OR c.Code = b.Country2
GROUP BY
    c.Name
HAVING
    COUNT(*) = (
        SELECT 
            MIN(numBorder)
        FROM (
            SELECT
                COUNT(*) AS numBorder
            FROM
                Country c
            JOIN
                borders b ON c.Code = b.Country1 OR c.Code = b.Country2
            GROUP BY
                c.Name
        ) AS countBorder
    )
ORDER BY
    num;
```

#### Querie 2

```
SELECT
    s.Language,
    COALESCE(CAST(SUM(c.Population * s.Percentage / 100) AS INTEGER), 0) AS numberspeaker
FROM
    Spoken s
JOIN
    Country c ON s.Country = c.Code
GROUP BY
    s.Language
ORDER BY
    numberspeaker DESC;
```

#### Querie 3

```
SELECT 
    b.Country1, 
    e1.GDP as GDP1, 
    b.Country2, 
    e2.GDP as GDP2, 
      CASE
          WHEN e1.GDP > e2.GDP THEN ROUND(e1.GDP / NULLIF(e2.GDP, 0), 0)
          ELSE ROUND(e2.GDP / NULLIF(e1.GDP, 0), 0) 
      END AS ratio
FROM 
      borders b
JOIN 
      Economy e1 ON b.Country1 = e1.Country
JOIN 
      Economy e2 ON b.Country2 = e2.Country
Where
      e1.GDP IS NOT NULL
   AND
      e2.GDP IS NOT NULL
ORDER BY 
    ratio DESC;
```

### P+ Assignments

#### Querie 1

```
WITH RECURSIVE BorderCrossing AS (
  SELECT CASE 
      WHEN 
          b.Country1 = 'S' THEN b.Country2
      ELSE 
          b.Country1
      END AS 
          code,
          1 AS depth,
          ARRAY['S']::text[] AS path
  FROM 
      borders b
  WHERE 
      'S' IN (b.Country1, b.Country2)
  
  UNION ALL
  
  SELECT CASE
      WHEN 
          b.Country1 = bc.code THEN b.Country2
      ELSE 
          b.Country1
      END AS 
          next_country,
          bc.depth + 1,
          bc.path || ARRAY[
              CASE
              WHEN 
                  b.Country1 = bc.code THEN b.Country2
              ELSE 
                  b.Country1
              END
                  ]::text[]
  FROM 
      borders b
  JOIN 
      BorderCrossing bc ON (
          bc.code = b.Country1
          OR bc.code = b.Country2
    )
      AND bc.depth < 5
)

SELECT 
    bc.code,
    c.Name AS name,
    MIN(bc.depth) AS min
FROM 
    BorderCrossing bc
JOIN 
    Country c ON bc.code = c.Code
WHERE 
    bc.code <> 'S'
GROUP BY 
    bc.code,
    c.Name
ORDER BY 
    min,
    name;
```

#### Querie 2

```
WITH RECURSIVE RiverHierarchy AS (
  SELECT 
      r.Name AS MainRiver,
      '' as path,
      r.Name AS lastRiver,
      1 AS NumRivers,
      r.Length AS TotLength
  FROM 
      River r
  WHERE 
      r.Name IN (
          'Nile',
          'Amazonas',
          'Yangtze',
         'Rhein',
         'Donau',
         'Mississippi'
      )
      
  UNION ALL
  
  SELECT 
    rh.MainRiver AS MainRiver,
    CASE
      WHEN 
        rh.path = '' THEN r.River
      ELSE 
        rh.path || '-' || r.River
    END AS 
      path,
      r.Name AS lastRiver,
      rh.NumRivers + 1 AS NumRivers,
      rh.TotLength + r.Length AS TotLength
  FROM 
    River r
    JOIN RiverHierarchy rh ON r.River = rh.lastRiver
),
MaxNumRivers AS (
  SELECT 
    MainRiver,
    MAX(NumRivers) AS MaxRivers
  FROM RiverHierarchy
  GROUP BY MainRiver
)

SELECT 
    RANK() OVER (ORDER BY rh.NumRivers) AS Rank,
    rh.path || '-' || rh.lastRiver AS lastRiver,
    rh.NumRivers AS NumRivers,
    rh.TotLength AS TotLength
FROM 
    RiverHierarchy rh
JOIN 
    MaxNumRivers mnr ON rh.MainRiver = mnr.MainRiver
    AND rh.NumRivers = mnr.MaxRivers
ORDER BY 
    Rank,
    TotLength DESC;
```
## Labb 4

```python
query = "SELECT * FROM books WHERE title LIKE '%" + usersearch + "%';"
```

```python
usersearch = "hello%'; DROP TABLE fines; SELECT * FROM books WHERE title LIKE '%hello"
```

```python
>>> usersearch = "hello%'; DROP TABLE fines; SELECT * FROM books WHERE title LIKE '%hello"
>>> query = "SELECT * FROM books WHERE title LIKE '%" + usersearch + "%';"
>>> print(query)
SELECT * FROM books WHERE title LIKE '%hello%'; DROP TABLE fines; SELECT * FROM books WHERE title LIKE '%hello%';
>>>
```
