from django.db import models


class SourceType(models.TextChoices):
    """Emission source categories shared across ERP and ESG apps."""

    DIESEL = "DIESEL", "Diesel"
    PETROL = "PETROL", "Petrol"
    CNG = "CNG", "CNG"
    NATURAL_GAS = "NATURAL_GAS", "Natural Gas"
    ELECTRICITY = "ELECTRICITY", "Electricity"
    WATER = "WATER", "Water"
    WASTE = "WASTE", "Waste"
    RAW_MATERIAL = "RAW_MATERIAL", "Raw Material"


class MeasurementUnit(models.TextChoices):
    LITER = "LITER", "Liter"
    KWH = "KWH", "kWh"
    KG = "KG", "Kilogram"
    CUBIC_METER = "CUBIC_METER", "Cubic Meter"
    UNIT = "UNIT", "Unit"


class Severity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class ApprovalStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class ESGPillar(models.TextChoices):
    ENVIRONMENTAL = "E", "Environmental"
    SOCIAL = "S", "Social"
    GOVERNANCE = "G", "Governance"
