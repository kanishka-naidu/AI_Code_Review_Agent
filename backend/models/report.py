from dataclasses import dataclass, asdict


@dataclass
class Report:
    status: str
    language: str
    summary: dict
    findings: list

    def to_dict(self):
        return asdict(self)