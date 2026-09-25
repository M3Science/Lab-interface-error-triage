"""Minimal HL7 v2 parser for laboratory result (ORU^R01) messages.

Deliberately small and dependency-free so every step is easy to follow.
Accepts segments separated by carriage returns (the HL7 standard) or
newlines (common when messages are saved to text files).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SEGMENT_NAME = re.compile(r"^[A-Z][A-Z0-9]{2}$")
FIELD_SEP = "|"
COMPONENT_SEP = "^"


@dataclass
class Segment:
    name: str
    parts: list[str]
    line_no: int

    def field(self, n: int) -> str:
        """Return field n using HL7 numbering (e.g. PID-3 -> field(3)).

        MSH is special: MSH-1 is the field separator itself, so MSH-n
        sits one position earlier in the split list than other segments.
        """
        if self.name == "MSH":
            if n == 1:
                return FIELD_SEP
            idx = n - 1
        else:
            idx = n
        return self.parts[idx].strip() if idx < len(self.parts) else ""

    def component(self, n: int, c: int) -> str:
        """Return component c of field n (e.g. OBX-3.1 -> component(3, 1))."""
        comps = self.field(n).split(COMPONENT_SEP)
        return comps[c - 1].strip() if c - 1 < len(comps) else ""


@dataclass
class Message:
    source: str
    segments: list[Segment] = field(default_factory=list)
    # (line number, raw text) for lines that are not valid segments
    malformed: list[tuple[int, str]] = field(default_factory=list)

    def first(self, name: str) -> Segment | None:
        return next((s for s in self.segments if s.name == name), None)

    def all(self, name: str) -> list[Segment]:
        return [s for s in self.segments if s.name == name]


def parse_message(text: str, source: str = "<string>") -> Message:
    msg = Message(source=source)
    lines = [ln for ln in re.split(r"\r\n|\r|\n", text) if ln.strip()]
    for i, line in enumerate(lines, start=1):
        name = line[:3]
        well_formed = SEGMENT_NAME.match(name) and (len(line) == 3 or line[3] == FIELD_SEP)
        if not well_formed:
            msg.malformed.append((i, line))
            continue
        msg.segments.append(Segment(name=name, parts=line.split(FIELD_SEP), line_no=i))
    return msg
