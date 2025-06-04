from sqlalchemy import text


def query_ploss_por_obra_cuentacontable_year(fecha_inicio, fecha_fin):
    query = text(f"""
    SELECT year, mes, name as cuenta, coalesce(obra, "Empty") AS obra, coalesce(saldo, 0) AS saldo from `tabAccount` as t1
    LEFT JOIN (
    SELECT LEFT(posting_date,4) AS year, LEFT(posting_date,7) AS mes, account, LEFT(cost_center, 4) AS obra, voucher_no, SUM(credit-debit)/1000000 AS saldo from `tabGL Entry`
    WHERE (account LIKE '05%' or account LIKE '04%') 
        AND posting_date >= '{fecha_inicio}'
        AND posting_date <= '{fecha_fin}'
        AND ((finance_book IS NULL) OR (finance_book = ""))
        GROUP by account, obra, voucher_no, year
    ) AS t2
    ON t2.account = t1.name
    WHERE is_group = 0
    AND (t1.name LIKE '05%' or t1.name LIKE '04%')
    AND voucher_no NOT LIKE '%PCE%'
    """)
    return query


def query_ploss_por_obra_cuentacontable_centrocoste_year(fecha_inicio, fecha_fin):
    query = text(f"""
    SELECT year, mes, name as cuenta, coalesce(obra, "Empty") AS obra, cost_center, coalesce(saldo, 0) AS saldo from `tabAccount` as t1
    LEFT JOIN (
    SELECT LEFT(posting_date,4) AS year, LEFT(posting_date,7) AS mes, account, LEFT(cost_center, 4) AS obra, cost_center, voucher_no, SUM(credit-debit)/1000000 AS saldo from `tabGL Entry`
    WHERE (account LIKE '05%' or account LIKE '04%') 
        AND posting_date >= '{fecha_inicio}'
        AND posting_date <= '{fecha_fin}'
        AND ((finance_book IS NULL) OR (finance_book = ""))
        GROUP by account, obra, cost_center, voucher_no, year
    ) AS t2
    ON t2.account = t1.name
    WHERE is_group = 0
    AND (t1.name LIKE '05%' or t1.name LIKE '04%')
    AND voucher_no NOT LIKE '%PCE%'
    """)
    return query


def query_ploss_por_obra_centrocoste_year(fecha_inicio, fecha_fin):
    query = text(f"""
    SELECT LEFT(posting_date,4) AS year, LEFT(posting_date,7) AS mes, LEFT(cost_center, 4) AS obra, cost_center, SUM(credit-debit)/1000000 AS saldo from `tabGL Entry`
    WHERE (account LIKE '05%' or account LIKE '04%') 
        AND posting_date >= '{fecha_inicio}'
        AND posting_date <= '{fecha_fin}'
        AND ((finance_book IS NULL) OR (finance_book = ""))
        AND voucher_no NOT LIKE '%PCE%'
        GROUP by obra, cost_center, year, mes
    """)
    return query


def query_balance_8_columnas(fecha_inicio, fecha_fin):
    query = text(f"""
    SELECT g.account, a.root_type, 
           SUM(g.debit) AS debitos,
           SUM(g.credit) AS creditos, 
           (SUM(g.debit) - SUM(g.credit)) AS saldo
    FROM `tabGL Entry` g
    JOIN tabAccount a ON a.name = g.account
    WHERE g.posting_date BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND g.is_cancelled = 0
      AND (g.finance_book IS NULL OR g.finance_book = "")
      AND (g.voucher_type <> 
           CASE 
               WHEN g.posting_date >= CONCAT(YEAR('{fecha_fin}'), '-01-01') THEN 'Period Closing Voucher'
               ELSE '%'
           END)
    GROUP BY g.account
    ORDER BY g.account, a.root_type;
    """)
    return query
