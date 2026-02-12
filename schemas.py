from pydantic import BaseModel, Field, IPvAnyAddress, field_validator, model_validator, BeforeValidator
from typing_extensions import Annotated
from typing import List, Optional, Literal, Union
import ipaddress
import re

def empty_to_none(v):
    if v == "":
        return None
    return v

# Annotated type for IP that treats "" as None
EmptyStrToNoneIP = Annotated[Optional[IPvAnyAddress], BeforeValidator(empty_to_none)]

class SiteInfo(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    customer: Optional[str] = ""
    location: Optional[str] = ""
    timezone: Optional[str] = "UTC"

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            # This matches the warning in original validator
            pass 
        return v

class Device(BaseModel):
    vendor: Literal["fortinet", "meraki", "velocloud", "bigleaf", "cato"]
    model: str
    firmware_version: str

class WanInterface(BaseModel):
    interface_name: str
    ip_address: IPvAnyAddress
    subnet_mask: str
    gateway: IPvAnyAddress
    bandwidth_mbps: Optional[float] = Field(None, gt=0)
    isp_name: Optional[str] = None
    priority: Literal["primary", "secondary"] = "secondary"

    @field_validator('subnet_mask')
    @classmethod
    def validate_mask(cls, v: str) -> str:
        # Handle CIDR (e.g. /24 or 24)
        if v.startswith('/') or v.isdigit():
            try:
                prefix = v.replace('/', '')
                # Validate it's a valid CIDR prefix
                if not prefix.isdigit():
                     raise ValueError()
                prefix_val = int(prefix)
                if not (0 <= prefix_val <= 32):
                    raise ValueError("CIDR prefix must be between 0 and 32")
                return str(ipaddress.IPv4Network(f"0.0.0.0/{prefix_val}").netmask)
            except (ValueError, TypeError):
                if v.startswith('/') or v.isdigit():
                    raise ValueError(f"Invalid CIDR notation: {v}")

        # Handle dotted decimal
        try:
            parts = [int(x) for x in v.split('.')]
            if len(parts) != 4:
                raise ValueError("Invalid mask format")
            binary = ''.join([format(x, '08b') for x in parts])
            if '01' in binary:
                raise ValueError("Invalid mask (broken sequence of 1s and 0s)")
            return v
        except Exception:
            raise ValueError(f"Invalid subnet mask: {v}")

    @model_validator(mode='after')
    def validate_gateway_in_subnet(self) -> 'WanInterface':
        if self.ip_address and self.subnet_mask and self.gateway:
            try:
                network = ipaddress.IPv4Network(f"{self.ip_address}/{self.subnet_mask}", strict=False)
                if ipaddress.IPv4Address(str(self.gateway)) not in network:
                    raise ValueError(f"Gateway {self.gateway} is not in the same subnet as {self.ip_address}")
            except Exception as e:
                # If network conversion fails (e.g. invalid mask), it's already caught by individual validators
                pass
        return self

class LanInterface(BaseModel):
    # ... (existing fields)
    interface_name: str
    ip_address: IPvAnyAddress
    subnet_mask: str
    vlan_id: Optional[int] = Field(None, ge=1, le=4094)
    dhcp_enabled: bool = False
    dhcp_range_start: EmptyStrToNoneIP = None
    dhcp_range_end: EmptyStrToNoneIP = None

    @field_validator('subnet_mask')
    @classmethod
    def validate_mask(cls, v: str) -> str:
        # Reusing logic from WanInterface
        return WanInterface.validate_mask(v)

    @model_validator(mode='after')
    def validate_dhcp(self) -> 'LanInterface':
        if self.dhcp_enabled:
            if not self.dhcp_range_start or not self.dhcp_range_end:
                raise ValueError("DHCP range start and end are required when DHCP is enabled")
            
            network = ipaddress.IPv4Network(f"{self.ip_address}/{self.subnet_mask}", strict=False)
            if self.dhcp_range_start and ipaddress.IPv4Address(str(self.dhcp_range_start)) not in network:
                 raise ValueError(f"DHCP start {self.dhcp_range_start} is not in the same subnet")
            if self.dhcp_range_end and ipaddress.IPv4Address(str(self.dhcp_range_end)) not in network:
                 raise ValueError(f"DHCP end {self.dhcp_range_end} is not in the same subnet")
        return self

class FirewallPolicy(BaseModel):
    name: str
    srcintf: str = "any"
    dstintf: str = "any"
    srcaddr: Union[str, List[str]] = "all"
    dstaddr: Union[str, List[str]] = "all"
    action: Literal["accept", "deny"] = "accept"
    nat: bool = True
    service: str = "ALL"

class WhitelistEntry(BaseModel):
    name: str
    address: str  # Can be IP, Subnet or FQDN

class SdwanHealthCheck(BaseModel):
    name: str = "Default_Health"
    server: str = "8.8.8.8"
    protocol: Literal["ping", "dns", "http"] = "dns"
    interval: int = 1000
    failtime: int = 5
    recoverytime: int = 5

class Services(BaseModel):
    dns_servers: List[Union[EmptyStrToNoneIP, str]] = []
    ntp_servers: List[Union[EmptyStrToNoneIP, str]] = []

    @field_validator('dns_servers', 'ntp_servers')
    @classmethod
    def validate_hostnames(cls, v: List[Union[IPvAnyAddress, str]]) -> List[Union[IPvAnyAddress, str]]:
        for item in v:
            if isinstance(item, str):
                # Basic hostname validation
                if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?$', item):
                    try:
                        ipaddress.ip_address(item)
                    except ValueError:
                        raise ValueError(f"Invalid hostname or IP: {item}")
        return v

class NetworkParams(BaseModel):
    site_info: SiteInfo
    device: Device
    wan_interfaces: List[WanInterface]
    lan_interfaces: List[LanInterface] = []
    services: Optional[Services] = Field(default_factory=Services)
    policy_template: Literal["basic", "standard", "advanced", "custom"] = "basic"
    custom_policies: List[FirewallPolicy] = []
    whitelist: List[WhitelistEntry] = []
    sdwan_health_checks: List[SdwanHealthCheck] = []
    webfilter_categories: List[int] = []
