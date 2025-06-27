import httpx
import random
import datetime
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, create_engine, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from faker import Faker
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import scoped_session
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = "sqlite:///./SMARTHOME.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30})
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

fake = Faker()
Base = declarative_base()

def random_datetime(start: datetime = datetime(2025, 6, 17, 0, 0),
                    end: datetime = datetime(2025, 6, 22, 0, 0)):
    """在指定时间段内生成随机时间"""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    house_size = Column(Float)
    created_at = Column(DateTime, default=random_datetime)
    updated_at = Column(DateTime, default=random_datetime)

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    type = Column(String)
    room = Column(String)
    created_at = Column(DateTime, default=random_datetime)
    updated_at = Column(DateTime, default=random_datetime)

class DeviceUsage(Base):
    __tablename__ = "device_usages"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id', ondelete="CASCADE"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration = Column(Integer)  # 单位秒
    energy_consumption = Column(Float)  # 单位kWh

class SecurityEvent(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'))
    event_type = Column(String)
    severity = Column(Integer)
    details = Column(String)
    timestamp = Column(DateTime, default=random_datetime)

class UserFeedback(Base):
    __tablename__ = "user_feedbacks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    device_id = Column(Integer, ForeignKey('devices.id'))
    feedback_text = Column(String)
    rating = Column(Integer)
    created_at = Column(DateTime, default=random_datetime)

class DeviceCoOccurrence(Base):
    __tablename__ = "device_co_occurrence"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))
    device1_id = Column(Integer, ForeignKey('devices.id', ondelete="CASCADE"))
    device2_id = Column(Integer, ForeignKey('devices.id', ondelete="CASCADE"))
    occurrence_count = Column(Integer)
    last_occurred = Column(DateTime, default=random_datetime)
    __table_args__ = (UniqueConstraint('user_id', 'device1_id', 'device2_id', name='uix_user_device_pair'),)

Base.metadata.create_all(engine)

# 重新生成用户与设备的随机时间（完全打散年月日）
def regenerate_user_device_timestamps():
    users = db.query(User).all()
    for user in users:
        created = random_datetime()
        updated = created + timedelta(minutes=random.randint(1, 180))
        user.created_at = created
        user.updated_at = updated

    devices = db.query(Device).all()
    for device in devices:
        created = random_datetime()
        updated = created + timedelta(minutes=random.randint(1, 180))
        device.created_at = created
        device.updated_at = updated

    db.commit()

regenerate_user_device_timestamps()

# 强制覆盖随机时间，确保每条记录都不相同

session = scoped_session(SessionLocal)

for user in session.query(User):
    created = random_datetime()
    updated = created + timedelta(minutes=random.randint(1, 120))
    user.created_at = created
    user.updated_at = updated

for device in session.query(Device):
    created = random_datetime()
    updated = created + timedelta(minutes=random.randint(1, 120))
    device.created_at = created
    device.updated_at = updated

session.commit()

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    house_size: float
    created_at: Optional[str]
    updated_at: Optional[str]
    @classmethod
    def from_orm(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            house_size=round(user.house_size, 1),
            created_at=user.created_at.strftime("%Y.%m.%d %H:%M") if user.created_at else None,
            updated_at=user.updated_at.strftime("%Y.%m.%d %H:%M") if user.updated_at else None
        )

class DeviceOut(BaseModel):
    id: int
    user_id: int
    name: str
    type: str
    room: str
    created_at: Optional[str]
    updated_at: Optional[str]
    @classmethod
    def from_orm(cls, device):
        return cls(
            id=device.id,
            user_id=device.user_id,
            name=device.name,
            type=device.type,
            room=device.room,
            created_at=device.created_at.strftime("%Y.%m.%d %H:%M") if device.created_at else None,
            updated_at=device.updated_at.strftime("%Y.%m.%d %H:%M") if device.updated_at else None
        )

class SecurityEventOut(BaseModel):
    id: int
    device_id: int
    event_type: str
    severity: int
    details: str
    timestamp: Optional[str]
    @classmethod
    def from_orm(cls, event):
        return cls(
            id=event.id,
            device_id=event.device_id,
            event_type=event.event_type,
            severity=event.severity,
            details=event.details,
            timestamp=event.timestamp.strftime("%Y.%m.%d %H:%M") if event.timestamp else None
        )

class UserFeedbackOut(BaseModel):
    id: int
    user_id: int
    device_id: int
    feedback_text: str
    rating: int
    created_at: Optional[str]
    @classmethod
    def from_orm(cls, fb):
        return cls(
            id=fb.id,
            user_id=fb.user_id,
            device_id=fb.device_id,
            feedback_text=fb.feedback_text,
            rating=fb.rating,
            created_at=fb.created_at.strftime("%Y.%m.%d %H:%M") if fb.created_at else None
        )

class DeviceCoOccurrenceOut(BaseModel):
    id: int
    user_id: int
    device1_id: int
    device2_id: int
    occurrence_count: int
    last_occurred: Optional[str]
    @classmethod
    def from_orm(cls, co):
        return cls(
            id=co.id,
            user_id=co.user_id,
            device1_id=co.device1_id,
            device2_id=co.device2_id,
            occurrence_count=co.occurrence_count,
            last_occurred=co.last_occurred.strftime("%Y.%m.%d %H:%M") if co.last_occurred else None
        )

def generate_device_usages_and_cooccurrence(device_objects, users):
    # Step 1: 使用记录
    usage_records = []
    for device in device_objects:
        for _ in range(random.randint(2, 5)):
            start = random_datetime()
            end = start + timedelta(minutes=random.randint(5, 90))
            duration = int((end - start).total_seconds())
            usage = DeviceUsage(
                device_id=device.id,
                start_time=start,
                end_time=end,
                duration=duration,
                energy_consumption=round(random.uniform(0.1, 3.0), 2)
            )
            usage_records.append(usage)
    db.add_all(usage_records)
    db.commit()

    # Step 2: 共现记录
    usage_map = {}
    for usage in db.query(DeviceUsage).all():
        usage_map.setdefault(usage.device_id, []).append(usage)

    co_records = []
    for user in users:
        user_devices = [d for d in device_objects if d.user_id == user.id]
        for i in range(len(user_devices)):
            for j in range(i + 1, len(user_devices)):
                d1, d2 = user_devices[i], user_devices[j]
                u1_list = usage_map.get(d1.id, [])
                u2_list = usage_map.get(d2.id, [])
                overlap_count = 0
                last_overlap = None
                for u1 in u1_list:
                    for u2 in u2_list:
                        latest_start = max(u1.start_time, u2.start_time)
                        earliest_end = min(u1.end_time, u2.end_time)
                        if latest_start < earliest_end:
                            overlap_count += 1
                            last_overlap = max(last_overlap or latest_start, latest_start)
                if overlap_count > 0:
                    co = DeviceCoOccurrence(
                        user_id=user.id,
                        device1_id=min(d1.id, d2.id),
                        device2_id=max(d1.id, d2.id),
                        occurrence_count=overlap_count,
                        last_occurred=last_overlap
                    )
                    co_records.append(co)

    db.add_all(co_records)
    db.commit()


# Kimi API 配置
KIMI_API_KEY = "sk-T0nBPk76SABreNynijPaLcw7H4fZI4EyRzxfZgrDvSDYNp2R"  # 使用你提供的 Kimi API 密钥
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"  # Kimi API URL


# 调用 Kimi API 生成用户反馈的函数
def generate_feedback_with_kimi(device_name: str) -> str:
    prompt = f"你是一个使用智能家居的普通用户，请围绕以下设备，写一条真实、自然、简洁的中文反馈（30~50字），内容应包含1个实际问题和1个建议：设备：{device_name}"

    data = {
        "model": "moonshot-v1-8k",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "top_p": 0.9,
        "max_tokens": 100
    }

    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(KIMI_API_URL, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                return f"【Kimi错误】状态码：{response.status_code}"
    except Exception as e:
        return f"【调用失败】{str(e)}"

# 调用 Kimi API 生成用户反馈的函数
def generate_fake_data(num_users=30, num_devices=30, num_events=30, num_feedbacks=1):
    # 删除所有表格数据并重新创建表格
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    # 生成用户数据
    users = []
    for _ in range(num_users):
        created_at = random_datetime()
        updated_at = created_at + timedelta(minutes=random.randint(5, 180))
        user = User(
            username=fake.name(),
            email=fake.email(),
            house_size=round(random.uniform(60, 160), 1),
            created_at=created_at,
            updated_at=updated_at
        )
        users.append(user)
    db.add_all(users)
    db.commit()

    # 设备类型及其设备名称列表
    device_types = {
        "Smart_plug": ["Smart Plug", "Smart Outlet", "Wi-Fi Plug", "USB Smart Plug", "Bluetooth Smart Plug"],
        "Thermostat": ["Smart Thermostat", "Wi-Fi Thermostat", "Programmable Thermostat", "Digital Thermostat",
                       "Learning Thermostat"],
        "Air_conditioner": ["Smart Air Conditioner", "Window Air Conditioner", "Portable Air Conditioner",
                            "Split Air Conditioner", "Inverter Air Conditioner"],
        "Security_camera": ["Indoor Security Camera", "Outdoor Security Camera", "Wireless Security Camera",
                            "Smart CCTV Camera", "IP Security Camera"],
        "Motion_sensor": ["PIR Motion Sensor", "Smart Motion Sensor", "Wireless Motion Sensor",
                          "Motion-Activated Light Sensor", "Ceiling Mount Motion Sensor"],
        "Window_sensor": ["Window Contact Sensor", "Magnetic Window Sensor", "Smart Window Sensor",
                          "Wireless Window Sensor", "Glass Break Window Sensor"],
        "Door_lock": ["Smart Door Lock", "Electronic Door Lock", "Keyless Door Lock", "Bluetooth Door Lock",
                      "Wi-Fi Door Lock"],
        "Smart_light": ["Smart LED Light", "Smart Bulb", "RGB Smart Light", "Smart Flood Light", "Wi-Fi Light Bulb"]
    }

    # 生成设备数据
    device_objects = []
    for _ in range(num_devices):
        user_id = random.randint(1, num_users)
        created_at = random_datetime()
        updated_at = created_at + timedelta(minutes=random.randint(5, 180))
        device_type = random.choice(list(device_types.keys()))
        device_name = random.choice(device_types[device_type])

        device = Device(
            user_id=user_id,
            name=device_name,
            type=device_type,
            room=random.choice(["Living Room", "Bedroom", "Kitchen", "Entrance", "Bathroom"]),
            created_at=created_at,
            updated_at=updated_at
        )
        device_objects.append(device)

    db.add_all(device_objects)
    db.commit()



    # 生成安防事件
    for _ in range(num_events):
        device = random.choice(device_objects)  # 随机选择一个设备
        severity = random.randint(1, 5)  # 随机选择事件的严重程度
        details = f"事件发生在 {device.room}，设备 {device.name} 检测到异常。具体事件：未知"  # 使用设备的名称
        db.add(SecurityEvent(
            device_id=device.id,  # 使用设备的 ID
            event_type="Motion Detected",  # 事件类型
            severity=severity,  # 严重程度
            details=details  # 事件详情
        ))
    db.commit()  # 提交数据库事务

    # 生成用户反馈
    for i in range(num_feedbacks):
        user = random.choice(users)
        device = random.choice(device_objects)
        print(f"[Kimi] 正在生成第 {i + 1} 条反馈...")
        feedback = generate_feedback_with_kimi(device.name)  # 使用 Kimi API 生成反馈

        # 如果反馈错误，则重新尝试（加延时）
        if "【Kimi错误】" in feedback:
            print(f"【Kimi错误】状态码：429，正在等待 20 秒后重试...")
            time.sleep(20)  # 延时 5 秒再试
            feedback = generate_feedback_with_kimi(device.name)

        db.add(UserFeedback(user_id=user.id, device_id=device.id, feedback_text=feedback, rating=random.randint(1, 5)))
        time.sleep(20)  # 每个反馈之间加入 10 秒的延时，防止过快请求

    db.commit()
    # 最后生成使用记录和共现表
    generate_device_usages_and_cooccurrence(device_objects, users)
    db.commit()

generate_fake_data()


@app.get("/users/", response_model=List[UserOut])
def get_users():
    return [UserOut.from_orm(u) for u in db.query(User).all()]

@app.get("/devices/", response_model=List[DeviceOut])
def get_devices():
    return [DeviceOut.from_orm(d) for d in db.query(Device).all()]

class DeviceUsageOut(BaseModel):
    id: int
    device_id: int
    start_time: Optional[str]
    end_time: Optional[str]
    duration: int
    energy_consumption: float
    @classmethod
    def from_orm(cls, u):
        return cls(
            id=u.id,
            device_id=u.device_id,
            start_time=u.start_time.strftime("%Y.%m.%d %H:%M") if u.start_time else None,
            end_time=u.end_time.strftime("%Y.%m.%d %H:%M") if u.end_time else None,
            duration=u.duration,
            energy_consumption=u.energy_consumption
        )

@app.get("/device_usages/", response_model=List[DeviceUsageOut])
def get_device_usages():
    return [DeviceUsageOut.from_orm(u) for u in db.query(DeviceUsage).all()]

@app.get("/security_events/", response_model=List[SecurityEventOut])
def get_security_events():
    return [SecurityEventOut.from_orm(e) for e in db.query(SecurityEvent).all()]

@app.get("/user_feedbacks/", response_model=List[UserFeedbackOut])
def get_user_feedbacks():
    return [UserFeedbackOut.from_orm(f) for f in db.query(UserFeedback).all()]

@app.get("/device_co_occurrence/", response_model=List[DeviceCoOccurrenceOut])
def get_device_co_occurrence():
    return [DeviceCoOccurrenceOut.from_orm(r) for r in db.query(DeviceCoOccurrence).all()]
