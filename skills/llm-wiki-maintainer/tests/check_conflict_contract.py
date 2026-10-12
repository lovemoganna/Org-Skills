#!/usr/bin/env python3
"""Synthetic contract regression for evidence conflict gates. NOT real-source T17."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Claim:
    subject: str
    predicate: str
    scope: str
    time: str
    revision: str
    polarity: str
    quantifier: str = "assertion"

def classify(a: Claim, b: Claim) -> str:
    if (a.subject,a.predicate) != (b.subject,b.predicate):
        return "NOT_COMPARABLE"
    if not all((a.scope,b.scope,a.time,b.time,a.revision,b.revision)):
        return "UNKNOWN"
    if (a.scope,a.time,a.revision) != (b.scope,b.time,b.revision):
        return "CONTEXT_DIFFERENCE"
    if a.quantifier != b.quantifier:
        return "NOT_STRICT_CONTRADICTION"
    if a.polarity not in {"YES","NO"} or b.polarity not in {"YES","NO"}:
        return "UNKNOWN"
    return "STRICT_CONTRADICTION" if a.polarity != b.polarity else "AGREEMENT"

def ingest_decision(source, known_sources, event, known_events):
    return "NOOP" if source in known_sources or event in known_events else "PROPOSE_WRITE"

def lease_decision(expected_head, actual_head):
    return "SAFE_TO_ATTEMPT" if expected_head == actual_head else "STOP_AND_REBASE"

def main():
    d=dict(subject="FixtureUser",predicate="active",scope="spot",time="2026-10-01T00:00:00Z",revision="r1")
    yes=Claim(**d,polarity="YES")
    no=Claim(**d,polarity="NO")
    tests={
        "strict synthetic P vs not-P": classify(yes,no)=="STRICT_CONTRADICTION",
        "same assertion": classify(yes,yes)=="AGREEMENT",
        "version drift": classify(yes,Claim(**{**d,"revision":"r2"},polarity="NO"))=="CONTEXT_DIFFERENCE",
        "scope mismatch": classify(yes,Claim(**{**d,"scope":"futures"},polarity="NO"))=="CONTEXT_DIFFERENCE",
        "time mismatch": classify(yes,Claim(**{**d,"time":"2026-10-02T00:00:00Z"},polarity="NO"))=="CONTEXT_DIFFERENCE",
        "predicate mismatch": classify(yes,Claim(**{**d,"predicate":"eligible"},polarity="NO"))=="NOT_COMPARABLE",
        "quantifier mismatch": classify(Claim(**d,polarity="YES",quantifier="exists"),Claim(**d,polarity="NO",quantifier="all"))=="NOT_STRICT_CONTRADICTION",
        "unknown scope": classify(yes,Claim(**{**d,"scope":""},polarity="NO"))=="UNKNOWN",
        "Binance category negative control": classify(
            Claim("Binance","has_control","US access","2019-2023","historical","YES"),
            Claim("Binance","bypass_exists","US access","2019-2023","historical","YES"))=="NOT_COMPARABLE",
        "repeat ingest no-op": ingest_decision("s@1",{"s@1"},"event",{"event"})=="NOOP",
        "new source proposes write": ingest_decision("s@2",set(),"new",set())=="PROPOSE_WRITE",
        "concurrent HEAD mismatch stops": lease_decision("A","B")=="STOP_AND_REBASE",
        "unchanged HEAD permits attempt": lease_decision("A","A")=="SAFE_TO_ATTEMPT",
    }
    for name,ok in tests.items():
        print(("PASS" if ok else "FAIL")+": "+name)
    assert all(tests.values()),"Contract regression failed"
    print("PASS: %d synthetic assertions; real-source T17 remains unverified"%len(tests))

if __name__=="__main__":
    main()
