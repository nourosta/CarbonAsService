from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from database import Base

class CPUImpact(Base):
    __tablename__ = "cpu_impacts"
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String)
    gwp = Column(Float)  # Global Warming Potential
    adp = Column(Float)  # Abiotic Depletion Potential
    pe = Column(Float)   # Primary Energy
    timestamp = Column(DateTime, default=datetime.utcnow)


class GPUImpact(Base):
    __tablename__ = "gpu_impacts"
    id = Column(Integer, primary_key=True, index=True)
    model = Column(String)
    die_size = Column(Float)
    ram_size = Column(Float)
    gwp = Column(Float)
    adp = Column(Float)
    pe = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class RAMImpact(Base):
    __tablename__ = "ram_impacts"
    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String)
    capacity = Column(Float)
    process = Column(Integer)
    gwp = Column(Float)
    adp = Column(Float)
    pe = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class SSDImpact(Base):
    __tablename__ = "ssd_impacts"
    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String)
    capacity = Column(Float)
    gwp = Column(Float)
    adp = Column(Float)
    pe = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

class HDDImpact(Base):
    __tablename__ = "hdd_impacts"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    capacity = Column(Float)
    units = Column(Integer)
    gwp = Column(Float)
    adp = Column(Float)
    pe = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)


class PowerBreakdown(Base):
    __tablename__ = "power_breakdown"
    id = Column(Integer, primary_key=True, index=True)
    zone = Column(String, index=True)
    data = Column(Text)

class CarbonIntensity(Base):
    __tablename__ = "carbon_intensity"
    id = Column(Integer, primary_key=True, index=True)
    zone = Column(String, index=True)
    data = Column(Text)


class EcoflocResult(Base):
    __tablename__ = "ecofloc_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    pid = Column(Integer)
    process_name = Column(String)
    resource_type = Column(String)  # e.g., 'cpu' or 'ram'
    metric_name = Column(String)    # e.g., 'energy' or 'power'
    metric_value = Column(Float)
    unit = Column(String)
    cpu_usage = Column(Float)
    ram_usage = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    