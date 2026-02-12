from schemas import LanInterface
from pydantic import ValidationError

try:
    print("Testing with valid IP...")
    LanInterface(
        interface_name="lan1",
        ip_address="192.168.1.1",
        subnet_mask="255.255.255.0",
        dhcp_enabled=True,
        dhcp_range_start="192.168.1.10",
        dhcp_range_end="192.168.1.20"
    )
    print("Success")

    print("\nTesting with None...")
    LanInterface(
        interface_name="lan1",
        ip_address="192.168.1.1",
        subnet_mask="255.255.255.0",
        dhcp_enabled=False,
        dhcp_range_start=None
    )
    print("Success")

    print("\nTesting with empty string (Should now work due to BeforeValidator)...")
    LanInterface(
        interface_name="lan1",
        ip_address="192.168.1.1",
        subnet_mask="255.255.255.0",
        dhcp_enabled=False,
        dhcp_range_start="",
        dhcp_range_end=""
    )
    print("Success")
except ValidationError as e:
    print(f"Caught error: {e}")
except Exception as e:
    print(f"Caught unexpected error: {type(e).__name__}: {e}")
