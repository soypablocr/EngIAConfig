from pydantic import BaseModel, Field, IPvAnyAddress, field_validator, model_validator
from typing import List, Optional, Literal, Union
import ipaddress
import re

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
        try:
            parts = [int(x) for x in v.split('.')]
            if len(parts) != 4:
                raise ValueError("Invalidad mask format")
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
    interface_name: str
    ip_address: IPvAnyAddress
    subnet_mask: str
    vlan_id: Optional[int] = Field(None, ge=1, le=4094)
    dhcp_enabled: bool = False
    dhcp_range_start: Optional[IPvAnyAddress] = None
    dhcp_range_end: Optional[IPvAnyAddress] = None

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
            if ipaddress.IPv4Address(str(self.dhcp_range_start)) not in network:
                 raise ValueError(f"DHCP start {self.dhcp_range_start} is not in the same subnet")
            if ipaddress.IPv4Address(str(self.dhcp_range_end)) not in network:
                 raise ValueError(f"DHCP end {self.dhcp_range_end} is not in the same subnet")
        return self

class Services(BaseModel):
    dns_servers: List[Union[IPvAnyAddress, str]] = []
    ntp_servers: List[Union[IPvAnyAddress, str]] = []

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
