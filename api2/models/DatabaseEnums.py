import enum


class OrderStatus(str, enum.Enum):
    shipped = 'Shipped'
    pending = 'Pending'


class TransferStatus(str, enum.Enum):
    scheduled = 'Scheduled'
    processed = 'Processed'


class ShipmentType(str, enum.Enum):
    incoming = 'Incoming'
    outgoing = 'Outgoing'


class ShipmentStatus(str, enum.Enum):
    scheduled = 'Scheduled'
    transit = 'Transit'
    delivered = 'Delivered'
