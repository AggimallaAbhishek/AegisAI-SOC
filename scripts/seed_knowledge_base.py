from __future__ import annotations

import json
from pathlib import Path

DEFAULT_ENTRIES = [
    {
        "entry_id": "KB-001",
        "title": "Mimikatz Credential Dumping",
        "content": (
            "Mimikatz execution indicates possible credential dumping from LSASS memory. "
            "Prioritize host isolation and credential reset."
        ),
        "tags": ["credential_access", "mimikatz", "lsass", "T1003"],
        "references": ["MITRE ATT&CK T1003"],
    },
    {
        "entry_id": "KB-002",
        "title": "Suspicious PowerShell Encoded Commands",
        "content": "PowerShell encoded commands are often used for defense evasion and payload delivery.",
        "tags": ["powershell", "execution", "defense_evasion", "T1059"],
        "references": ["MITRE ATT&CK T1059.001"],
    },
    {
        "entry_id": "KB-003",
        "title": "Host Isolation Guidance",
        "content": "If active compromise is suspected, isolate host from network while preserving forensic data.",
        "tags": ["containment", "isolation", "incident_response"],
        "references": ["NIST 800-61"],
    },
]



def main() -> None:
    output = Path(__file__).resolve().parent / "sample_data" / "knowledge_base.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(DEFAULT_ENTRIES, indent=2), encoding="utf-8")
    print(f"Seeded knowledge base with {len(DEFAULT_ENTRIES)} entries at {output}")


if __name__ == "__main__":
    main()
