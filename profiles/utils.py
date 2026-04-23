import time
import uuid


def uuid7():
    ts = int(time.time() * 1000)
    rand = uuid.uuid4().hex[:16]
    return uuid.UUID(f"{ts:012x}{rand[:20]}")