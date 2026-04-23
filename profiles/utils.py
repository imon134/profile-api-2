import time
import uuid


def uuid7():
    """Generate a UUID7 (timestamp-based UUID)."""
    ts = int(time.time() * 1000)  # 48-bit timestamp in ms
    rand = int(uuid.uuid4().int & 0xFFFFFFFFFFFFFFFF)  # 64-bit random
    # Combine timestamp and random: 48 bits timestamp + 80 bits random
    uuid_int = (ts << 80) | rand
    return uuid.UUID(int=uuid_int)
