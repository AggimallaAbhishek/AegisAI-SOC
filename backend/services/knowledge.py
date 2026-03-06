from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from backend.core.config import get_settings


@dataclass
class KBEntry:
    entry_id: str
    title: str
    content: str
    tags: list[str]
    references: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "references": self.references,
        }


_DEFAULT_ENTRIES = [
    {
        "entry_id": "KB-001",
        "title": "Mimikatz Credential Dumping",
        "content": "Mimikatz execution indicates possible credential dumping from LSASS memory."
        " Prioritize host isolation and credential reset.",
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


class KnowledgeService:
    def __init__(self, knowledge_base_file: Path | None = None) -> None:
        settings = get_settings()
        self.knowledge_base_file = (
            knowledge_base_file or settings.resolve_path(settings.knowledge_base_path)
        )
        self._entries = self._load_entries()

    def _load_entries(self) -> List[KBEntry]:
        if self.knowledge_base_file.exists():
            try:
                raw_entries = json.loads(self.knowledge_base_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                raw_entries = _DEFAULT_ENTRIES
        else:
            raw_entries = _DEFAULT_ENTRIES

        entries: list[KBEntry] = []
        for item in raw_entries:
            entries.append(
                KBEntry(
                    entry_id=str(item.get("entry_id", "KB-UNKNOWN")),
                    title=str(item.get("title", "Untitled")),
                    content=str(item.get("content", "")),
                    tags=[str(tag) for tag in item.get("tags", [])],
                    references=[str(ref) for ref in item.get("references", [])],
                )
            )
        return entries

    def search(self, query: str, limit: int = 5) -> List[KBEntry]:
        query = query.strip().lower()
        if not query:
            return []

        terms = [term for term in query.split() if len(term) > 2]
        if not terms:
            terms = [query]

        scored: list[tuple[int, KBEntry]] = []
        for entry in self._entries:
            haystack = " ".join([entry.title, entry.content, " ".join(entry.tags)]).lower()
            score = sum(1 for term in terms if term in haystack)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda item: (-item[0], item[1].title))
        return [entry for _, entry in scored[:limit]]
