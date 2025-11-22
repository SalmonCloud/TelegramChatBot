INSERT INTO server_info
    (city, country, product_code, cpu, ram, storage, nic, price_monthly_usd)
VALUES
    -- E7C13-64-128-HKG
    ('Hong Kong', 'China',
     'E7C13-64-128-HKG',
     'EPYC 7C13 x1',
     'SK Hynix 32GB 2933MHz DDR4 ECC x4',
     'Intel P4510 NVMe 1TB x2',
     'Mellanox CX4 25G OCP x1',
     229.00),

    -- E7V13-64-128-HKG
    ('Hong Kong', 'China',
     'E7V13-64-128-HKG',
     'EPYC 7V13 x1',
     '32GB 2933MHz DDR4 ECC x4',
     'Intel P4510 NVMe 1TB x2',
     'Mellanox CX4 25G OCP x1',
     229.00),

    -- E7413-24-128-HKG
    ('Hong Kong', 'China',
     'E7413-24-128-HKG',
     'EPYC 7413 x1',
     '32GB 2933MHz DDR4 ECC x4',
     'Intel P4510 NVMe 1TB x2',
     'Mellanox CX4 25G OCP x1',
     209.00),

    -- R9900X-12-128-HKG (记录 1)
    ('Hong Kong', 'China',
     'R9900X-12-128-HKG',
     'Ryzen 9900X',
     '128GB DDR5 ECC',
     'M.2 NVMe 1TB x2',
     'Mellanox CX4 25G OCP x1',
     269.00),

    -- R9900X-12-128-HKG (记录 2，与上面相同)
    ('Hong Kong', 'China',
     'R9900X-12-128-HKG',
     'Ryzen 9900X',
     '128GB DDR5 ECC',
     'M.2 NVMe 1TB x2',
     'Mellanox CX4 25G OCP x1',
     269.00);
