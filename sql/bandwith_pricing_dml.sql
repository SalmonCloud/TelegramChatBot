INSERT INTO bandwidth_pricing (
    country,
    city,
    datacenter_code,
    datacenter_name,
    tier_label,
    min_bandwidth_gbps,
    max_bandwidth_gbps,
    flat_price_usd_per_mbps,
    commit_price_usd_per_mbps,
    overage_price_usd_per_mbps
)
VALUES
    -- SJC: Bandwidth < 10 Gbps
    ('United States', 'San Jose',
     'SJC1', 'San Jose DC1',
     'Bandwidth < 10 Gbps',
     NULL, 10.00,
     0.130, 0.140, 0.180),

    -- HKG: Bandwidth < 5 Gbps
    ('China', 'Hong Kong',
     'HKG1', 'Hong Kong DC1',
     'Bandwidth < 5 Gbps',
     NULL, 5.00,
     0.300, 0.320, 0.400),

    -- HKG: 5 Gbps <= Bandwidth < 10 Gbps
    ('China', 'Hong Kong',
     'HKG1', 'Hong Kong DC1',
     '5 Gbps <= Bandwidth < 10 Gbps',
     5.00, 10.00,
     0.250, 0.270, 0.340),

    -- HKG: Bandwidth >= 10 Gbps
    ('China', 'Hong Kong',
     'HKG1', 'Hong Kong DC1',
     'Bandwidth >= 10 Gbps',
     10.00, NULL,
     0.240, 0.260, 0.325);
