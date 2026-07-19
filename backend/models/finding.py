from dataclasses import dataclass, asdict


@dataclass
class Finding:
    issue: str
    severity: str
    line: int
    message: str

    fix: str = ""
    owasp_reference: str = ""
    secure_example: str = ""

    def to_dict(self):
        return asdict(self)