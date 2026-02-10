from dataclasses import dataclass
from typing import Any, Literal, Optional
import json

Format = Literal["cli", "json", "graphql"]

@dataclass
class ConfigArtifact:
    vendor: str
    format: Format
    content: Any  # str for cli/graphql, dict for json
    site_name: str
    filename: Optional[str] = None

    def __post_init__(self):
        if not self.filename:
            extensions = {
                "cli": ".conf",
                "json": ".json",
                "graphql": ".graphql"
            }
            ext = extensions.get(self.format, ".txt")
            safe_site = self.site_name.replace(" ", "_")
            self.filename = f"{safe_site}_{self.vendor}{ext}"

    def get_mimetype(self) -> str:
        mimetypes = {
            "cli": "text/plain",
            "json": "application/json",
            "graphql": "text/plain"
        }
        return mimetypes.get(self.format, "text/plain")

    def as_bytes(self) -> bytes:
        if self.format == "json":
            if isinstance(self.content, str):
                return self.content.encode("utf-8")
            return json.dumps(self.content, indent=2).encode("utf-8")
        return str(self.content).encode("utf-8")

    def as_dict(self) -> dict:
        return {
            "vendor": self.vendor,
            "format": self.format,
            "content": self.content,
            "filename": self.filename,
            "mimetype": self.get_mimetype()
        }
