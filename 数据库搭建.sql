-- 创建枚举类型
CREATE TYPE device_type AS ENUM (
    'light',            -- 灯光设备
    'thermostat',       -- 恒温器
    'security_camera',  -- 安防摄像头
    'door_lock',        -- 智能门锁
    'smart_plug',       -- 智能插座
    'air_conditioner',  -- 空调
    'window_sensor',    -- 窗户传感器
    'motion_sensor'     -- 运动传感器
);
--定义系统中所有可能的智能设备类型，确保设备类型的一致性。

CREATE TYPE event_severity AS ENUM ('low', 'medium', 'high', 'critical');--安防事件严重程度


--核心数据表
-- 创建用户表（存储系统用户的基本信息。house_size：用于分析房屋面积对设备使用行为的影响。 username和email都有唯一约束，防止重复注册）
CREATE TABLE users (
    id SERIAL PRIMARY KEY,               -- 自增主键
    username VARCHAR(50) NOT NULL UNIQUE,-- 用户名(唯一)
    email VARCHAR(100) NOT NULL UNIQUE,  -- 电子邮箱(唯一)
    house_size DECIMAL(10, 2) NOT NULL,  -- 房屋面积(平方米)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP  -- 更新时间
);

-- 创建设备表
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,               -- 自增主键
    user_id INTEGER NOT NULL,            -- 所属用户ID
    name VARCHAR(100) NOT NULL,         -- 设备名称(如"客厅主灯")
    type device_type NOT NULL,           -- 设备类型(使用枚举)
    room VARCHAR(50) NOT NULL,           -- 设备所在房间(如"客厅")
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- 更新时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
--type：使用预定义的设备类型枚举
--room：记录设备位置，便于按房间分析使用模式
--外键user_id关联到users表，当用户被删除时，其设备也会级联删除


-- 创建设备使用记录表(详细记录每个设备使用情况）
CREATE TABLE device_usages (
    id SERIAL PRIMARY KEY,               -- 自增主键
    device_id INTEGER NOT NULL,          -- 设备ID
    start_time TIMESTAMP WITH TIME ZONE NOT NULL, -- 开始使用时间
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,   -- 结束使用时间
    duration DECIMAL(10, 2) GENERATED ALWAYS AS ( -- 自动计算的持续时间(秒)
        EXTRACT(EPOCH FROM (end_time - start_time)))
    STORED,
    energy_consumption DECIMAL(10, 2),   -- 能耗(千瓦时)
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);
--duration是生成列，自动计算使用时长(秒)
--记录能量消耗，可用于能源使用分析
--外键关联到devices表，设备删除时使用记录也会删除


-- 创建安防事件表（安防相关事件）
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,               -- 自增主键
    device_id INTEGER NOT NULL,          -- 触发事件的设备ID
    event_type VARCHAR(50) NOT NULL,     -- 事件类型(如"motion_detected")
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 发生时间
    severity event_severity NOT NULL,    -- 严重程度(使用枚举)
    details TEXT,                        -- 事件详细信息
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);
--severity：使用预定义的严重程度枚举
--details：存储事件详情JSON或文本描述
--用于分析安全事件的时间模式和设备可靠性


-- 创建用户反馈表（手机用户对系统或特定设备的反馈）
CREATE TABLE user_feedbacks (
    id SERIAL PRIMARY KEY,               -- 自增主键
    user_id INTEGER NOT NULL,            -- 反馈用户ID
    device_id INTEGER,                   -- 相关设备ID(可选)
    feedback_text TEXT NOT NULL,         -- 反馈内容
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5), -- 评分(1-5)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 创建时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
);
--device_id可为空，允许提交系统整体反馈
--rating有检查约束，确保评分在1-5范围内
--设备删除时，反馈保留但device_id设为NULL



--分析辅助表
-- 创建设备共现表(用于分析：记录哪些设备经常一起使用，用于分析用户习惯）
CREATE TABLE device_co_occurrence (
    id SERIAL PRIMARY KEY,               -- 自增主键
    user_id INTEGER NOT NULL,            -- 用户ID
    device1_id INTEGER NOT NULL,         -- 设备1ID
    device2_id INTEGER NOT NULL,         -- 设备2ID
    occurrence_count INTEGER DEFAULT 1,  -- 共现次数
    last_occurred TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 最后共现时间
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (device1_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (device2_id) REFERENCES devices(id) ON DELETE CASCADE,
    UNIQUE (user_id, device1_id, device2_id)  -- 确保唯一性
);
--存储设备对的共现次数，用于识别常用组合
--唯一约束确保每个设备对只有一条记录
--用于实现"哪些设备经常同时使用"的分析需求



-- 创建索引以提高查询性能
-- 设备使用记录的设备ID索引
CREATE INDEX idx_device_usages_device_id ON device_usages(device_id);

-- 设备使用记录的时间范围索引
CREATE INDEX idx_device_usages_time_range ON device_usages(start_time, end_time);

-- 安防事件的设备ID索引
CREATE INDEX idx_security_events_device_id ON security_events(device_id);

-- 安防事件的时间戳索引
CREATE INDEX idx_security_events_timestamp ON security_events(timestamp);

-- 用户反馈的用户ID索引
CREATE INDEX idx_user_feedbacks_user_id ON user_feedbacks(user_id);

-- 用户反馈的设备ID索引
CREATE INDEX idx_user_feedbacks_device_id ON user_feedbacks(device_id);

--索引作用：加速按设备查询使用记录，优化时间范围查询，提高安防事件分析的查询速度，加速用户反馈的检索

