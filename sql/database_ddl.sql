USE ChatBot;

-- 用户表：记录每个 Telegram 用户
CREATE TABLE telegram_users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    telegram_chat_id BIGINT NOT NULL,            -- 私聊 chat_id，一般等于 telegram_user_id
    telegram_user_id BIGINT NULL,                -- Telegram 用户 id（备用）
    username VARCHAR(255) NULL,                  -- @username
    first_name VARCHAR(255) NULL,
    last_name VARCHAR(255) NULL,
    language_code VARCHAR(16) NULL,              -- Telegram 自带语言码，如 "en", "zh-hans"

    allow_contact TINYINT(1) NOT NULL DEFAULT 1, -- 用户是否允许我们再主动联系

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uk_telegram_chat_id (telegram_chat_id),
    KEY idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 会话表：一轮对话（多条消息）对应一条记录
CREATE TABLE conversations (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    telegram_user_id BIGINT UNSIGNED NOT NULL,   -- 对应 telegram_users.id

    status ENUM('open','in_progress','closed') NOT NULL DEFAULT 'open',
    subject VARCHAR(255) NULL,                   -- 可选：简短主题，比如“计费问题”

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    closed_at DATETIME NULL,
    last_message_at DATETIME NULL,

    PRIMARY KEY (id),
    KEY idx_telegram_user_id (telegram_user_id),
    KEY idx_status_last_message (status, last_message_at),

    CONSTRAINT fk_conversations_user
        FOREIGN KEY (telegram_user_id)
        REFERENCES telegram_users (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 消息表：记录每一条消息（用户的 & 内部同事的）
CREATE TABLE messages (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    conversation_id BIGINT UNSIGNED NOT NULL,      -- 对应 conversations.id

    direction ENUM('from_user','from_staff') NOT NULL,    -- 消息方向
    content_type ENUM('text','photo','document','audio','video','sticker','other')
        NOT NULL DEFAULT 'text',

    text TEXT NULL,                                -- 文本内容（如果是文本类型）

    telegram_user_message_id BIGINT NULL,          -- 用户私聊里的 message_id（可选，debug 用）
    telegram_group_message_id BIGINT NULL,         -- 内部群里那条“卡片/消息”的 message_id

    internal_staff_username VARCHAR(255) NULL,     -- 可选：记录是哪个同事发的（从群里取 username）
    raw_payload LONGTEXT NULL,                     -- 可选：保存原始 Telegram JSON（调试用）

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_conversation_created (conversation_id, created_at),
    KEY idx_telegram_group_message_id (telegram_group_message_id),

    CONSTRAINT fk_messages_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 记录简单版独服产品信息（MySQL 版本）
CREATE TABLE server_info (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    -- 机房所在城市 / 国家
    city    VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL,

    -- 产品编码：全局唯一
    product_code VARCHAR(50) NOT NULL,

    cpu     VARCHAR(200) NOT NULL,   -- 例如：Intel Xeon E5-2690 v4 x2
    ram     VARCHAR(200) NOT NULL,   -- 例如：64GB DDR4
    storage VARCHAR(200) NOT NULL,   -- 例如：2x1TB NVMe + 2x4TB HDD
    nic     VARCHAR(200) DEFAULT NULL,  -- 例如：1Gbps / 10Gbps
    included_bandwidth VARCHAR(200) DEFAULT NULL, -- 机器自带的带宽信息（如“10Gbps included”）

    -- 每月价格（美元）
    price_monthly_usd DECIMAL(10,2) NOT NULL,

    -- 当前是否空闲 / 可售，TRUE=空闲
    available TINYINT(1) NOT NULL DEFAULT 1,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    UNIQUE KEY uk_product_code (product_code),

    -- 常用查询：按城市 / 国家过滤
    KEY idx_server_products_location (city, country),
    KEY idx_server_products_available (available),

    -- 可选位置约束（MySQL 8.0 以后才真正生效；8.0 以下版本会忽略 CHECK）
    CONSTRAINT chk_server_location_pair
        CHECK (
            (city = 'San Jose' AND country = 'United States')
         OR (city = 'Hong Kong' AND country = 'China')
        )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bandwidth_pricing (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    -- 机房位置，例如：SJC / HKG
    location_code  VARCHAR(10)  NOT NULL,      -- SJC, HKG ...
    location_name  VARCHAR(50)  DEFAULT NULL,  -- 可选：San Jose, Hong Kong 等

    -- 带宽档位说明
    tier_label     VARCHAR(50)  NOT NULL,      -- 例如：'Bandwidth < 5 Gbps'

    -- 范围（单位：Gbps；NULL 表示“无下限 / 无上限”）
    min_bandwidth_gbps DECIMAL(6,2) DEFAULT NULL,
    max_bandwidth_gbps DECIMAL(6,2) DEFAULT NULL,

    -- 单价：USD / Mbps
    flat_price_usd_per_mbps    DECIMAL(6,3) NOT NULL,
    commit_price_usd_per_mbps  DECIMAL(6,3) NOT NULL,
    overage_price_usd_per_mbps DECIMAL(6,3) NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (id),

    -- 常用查询：按机房 + 带宽范围
    KEY idx_bandwidth_location_range (location_code, min_bandwidth_gbps, max_bandwidth_gbps),

    -- 限制：同一机房中，同一范围只能出现一次
    UNIQUE KEY uk_bw_location_range (location_code, min_bandwidth_gbps, max_bandwidth_gbps)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
