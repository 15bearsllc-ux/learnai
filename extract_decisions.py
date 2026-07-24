"""
Exercise 1: Decision Block Extractor

This script reads the C0 Conventions document (as text) and extracts
all Decision blocks into a structured JSON format.

What you're learning:
- Python file I/O
- String parsing and manipulation
- Data structures (lists, dictionaries)
- JSON output
"""

import json
import re

# The raw text content from C0 Conventions
c0_text = """
DECISION Question. Illustrative only — this is the shape every Decision block takes. Options considered. Option A — stated plainly, with its appeal. Option B — the chosen one. Option C — a third, with why it loses. Choice & rationale. Option B, because it best fits the constraint that matters most here. Trade-off / revisit. Accepts a minor cost; revisit if that cost grows or a named condition changes. Phase. P1.

GUIDING PRINCIPLE Trust through auditability, not prevention. Where a capability cannot or should not be technically prevented, the control is to make its use visible and accountable rather than to lock it away. The system does not pretend to prevent what it cannot; it guarantees that what happens is recorded, attributable, and — where the customer is affected — visible to them. Instances: the tenant administrator may self-grant additional roles, but every self-grant is an audit event (permit-and-log, not lock); the audit hash chain detects tampering rather than claiming to make it impossible; staff reach customer data through time-boxed, reason-required, tenant-visible break-glass grants rather than being walled off entirely; even root/superuser is treated as break-glass, minimized and logged, because it cannot be prevented.

GUIDING PRINCIPLE Name by system function, not company title. Roles are named for what they do to the system, not for who happens to hold them or which department they sit in. Company titles are personal and temporary; system functions are structural and permanent. Naming by function means a role need not be renamed when the person or team holding it changes. Instances: the tenant "administrator" is a system-administration role, not necessarily IT; the "Platform Administrator" staff role is defined by platform operation, not by being the founder (who merely holds it initially); the pricing-authority function is defined by setting guardrails, even where the label "Finance" is retained for recognizability.
"""

def extract_decisions(text):
    """
    Parse the text and extract Decision blocks.
    Returns a list of dictionaries, one per decision.
    """
    decisions = []
    
    decision_blocks = text.split("DECISION")[1:]
    
    for i, block in enumerate(decision_blocks, start=1):
        decision_dict = {
            "decision_id": f"1.{i}",
            "component": "C0",
            "type": "DECISION",
            "raw_text": block.strip()[:200] + "..."
        }
        
        decisions.append(decision_dict)
    
    return decisions


def extract_principles(text):
    """
    Parse the text and extract GUIDING PRINCIPLE blocks.
    Returns a list of dictionaries, one per principle.
    """
    principles = []
    
    principle_blocks = text.split("GUIDING PRINCIPLE")[1:]
    
    for i, block in enumerate(principle_blocks, start=1):
        principle_dict = {
            "principle_id": f"GP-{i}",
            "component": "C0",
            "type": "GUIDING_PRINCIPLE",
            "raw_text": block.strip()[:300] + "..."
        }
        
        principles.append(principle_dict)
    
    return principles


def main():
    """
    Main function: extract decisions and principles, output as JSON
    """
    print("Starting Decision Block Extraction...")
    print("-" * 50)
    
    decisions = extract_decisions(c0_text)
    print(f"Found {len(decisions)} Decision block(s)")
    
    principles = extract_principles(c0_text)
    print(f"Found {len(principles)} Guiding Principle(s)")
    
    output = {
        "document": "C0_Conventions",
        "decisions_count": len(decisions),
        "principles_count": len(principles),
        "decisions": decisions,
        "principles": principles
    }
    
    output_filename = "decisions.json"
    with open(output_filename, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSuccessfully wrote {len(decisions) + len(principles)} items to {output_filename}")
    print("-" * 50)
    
    print("\nSummary of extracted items:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()