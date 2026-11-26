"""Create a scoped Excel copy with one FIFO analysis sheet and native chart."""
from collections import defaultdict, deque
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

from openpyxl import load_workbook
from openpyxl.chart import LineChart, Reference
from openpyxl.chart.data_source import AxDataSource, StrRef

FIELDS = ("id", "pair", "time", "side", "quantity")
MIDNIGHT = datetime(1970, 1, 1)


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def input_book(source):
    if not source.is_file() or source.suffix.lower() != ".xlsx" or source.stat().st_size > 20_000_000:
        raise ValueError("expected bounded local .xlsx input")
    with ZipFile(source) as archive:
        entries = archive.infolist()
        if len(entries) > 2000 or sum(item.file_size for item in entries) > 80_000_000:
            raise ValueError("workbook decompressed size exceeds limit")
        if any("/externalLinks/" in item.filename or "vbaProject" in item.filename for item in entries):
            raise ValueError("external links and macros are outside this copy contract")
    return load_workbook(source)


def inspect(source):
    book = input_book(source)
    return {"sheets": [{"title": sheet.title, "headers": [c.value for c in sheet[1]]}
                       for sheet in book.worksheets if sheet.max_column <= 256]}


def execution_rows(sheet, columns):
    headers = [c.value for c in sheet[1]]
    if set(columns) != set(FIELDS) or len(set(columns.values())) != len(FIELDS) or any(
        headers.count(columns[field]) != 1 for field in FIELDS
    ):
        raise ValueError("fields must map to distinct known headers")
    idx = [headers.index(columns[field]) for field in FIELDS]
    if sheet.max_row > 10001 or sheet.max_column > 256:
        raise ValueError("source tab exceeds row or column limit")
    unique = {}
    for line, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
        if not any(cell is not None for cell in row):
            continue
        key, pair, time, side, amount = (row[i] for i in idx)
        if any(value is None or isinstance(value, bool) or value == "" for value in (key,pair,time,side,amount)):
            raise ValueError(f"incomplete execution at row {line}")
        if isinstance(time, str):
            time = datetime.fromisoformat(time.replace("Z", "+00:00"))
        if not isinstance(time, datetime):
            raise ValueError(f"invalid execution time at row {line}")
        if time.tzinfo is not None:
            from datetime import timezone
            time = time.astimezone(timezone.utc).replace(tzinfo=None)
        num = Decimal(str(amount))
        side = str(side).upper().strip()
        if side not in {"BUY", "SELL"} or not num.is_finite() or not Decimal("1e-18") <= num <= Decimal("1e18"):
            raise ValueError(f"unsupported side or quantity at row {line}")
        identity = str(pair), str(key)
        record = (time, line, side, num)
        if identity in unique:
            old = unique[identity]
            if (old[0], old[2], old[3]) != (time, side, num):
                raise ValueError(f"conflicting duplicate execution at row {line}")
            continue
        unique[identity] = record
    return sorted(((*record, *identity) for identity, record in unique.items()))


def build(source, destination, request):
    if set(request) != {"sheet", "columns", "window_minutes"}:
        raise ValueError("expected source sheet, field map and window minutes")
    window = request["window_minutes"]
    if type(window) is not int or not 1 <= window <= 1440:
        raise ValueError("window_minutes must be an integer 1–1440")
    source_digest = digest(source)
    request_id = hashlib.sha256(json.dumps([source_digest,request],sort_keys=True).encode()).hexdigest()
    if destination.exists():
        raise FileExistsError("authorized output already exists")
    book = input_book(source)
    sheet = book[request["sheet"]]
    entries = execution_rows(sheet, request["columns"])
    if not entries:
        raise ValueError("source tab has no executions")
    lots = defaultdict(deque)
    metrics = defaultdict(lambda: [Decimal(0), Decimal(0), Decimal(0)])
    matches = []
    for time, _, side, amount, pair, key in entries:
        if side == "BUY":
            lots[pair].append((time, key, amount))
            continue
        bucket = MIDNIGHT + ((time - MIDNIGHT) // timedelta(minutes=window)) * timedelta(minutes=window)
        totals = metrics[pair, bucket]
        while amount and lots[pair]:
            opened, buy, quantity = lots[pair].popleft()
            matched = min(quantity, amount)
            duration = Decimal(str((time - opened).total_seconds())) / 60
            matches.append([pair, buy, key, opened, time, float(matched), float(duration)])
            totals[0] += matched
            totals[1] += matched * duration
            amount -= matched
            if quantity > matched:
                lots[pair].appendleft((opened,buy,quantity-matched))
        if amount:
            totals[2] += amount
            matches.append([pair, None, key, None, time, float(amount), None])
    if not metrics:
        raise ValueError("source tab has no sells")
    pairs = sorted({pair for pair, _ in metrics})
    buckets = sorted({bucket for _, bucket in metrics})
    if len(pairs) > 40 or len(pairs)*len(buckets) > 20000:
        raise ValueError("chart exceeds series or point limit")
    analysis = book.create_sheet("FIFO holding turnover")
    analysis.append(["FIFO holding turnover (UTC)","Window minutes",window,"Unique executions",len(entries)])
    analysis.append(["Sell window UTC", "Pair", "Matched base quantity", "Weighted holding minutes", "Unmatched sell quantity"])
    for (pair,bucket),(qty,total,unmatched) in sorted(metrics.items()):
        analysis.append([bucket,pair,float(qty),float(total/qty) if qty else None,float(unmatched)])
        analysis.cell(analysis.max_row,1).number_format = "yyyy-mm-dd hh:mm"
    analysis.append([None])
    first = analysis.max_row + 1
    analysis.append(["Window",*pairs])
    for bucket in buckets:
        row = [bucket.isoformat(sep=" ",timespec="minutes")]
        for pair in pairs:
            qty,total,_ = metrics.get((pair,bucket),(0,0,0))
            row.append(float(total/qty) if qty else None)
        analysis.append(row)
    chart = LineChart()
    chart.title = "Weighted holding minutes by sell window"
    chart.y_axis.title = "Minutes"
    chart.x_axis.title = "Window start UTC"
    chart.display_blanks = "gap"
    chart.add_data(Reference(analysis,min_col=2,max_col=len(pairs)+1,min_row=first,max_row=analysis.max_row),titles_from_data=True)
    labels = Reference(analysis,min_col=1,min_row=first+1,max_row=analysis.max_row)
    for series in chart.series:
        series.cat = AxDataSource(strRef=StrRef(f=str(labels)))
    analysis.add_chart(chart,"I3")
    analysis.append([None])
    analysis.append(["Pair","Buy execution","Sell execution","Buy UTC","Sell UTC","Matched / unmatched quantity","Holding minutes"])
    for row in matches:
        analysis.append(row)
    analysis.freeze_panes = "C3"
    if digest(source) != source_digest:
        raise ValueError("source workbook changed during calculation")
    book.properties.identifier = f"legion-fifo:{request_id}"
    # Link is atomic and fails with EEXIST. A resumed worker never overwrites the sink.
    with tempfile.TemporaryDirectory(dir=destination.parent) as staging:
        temporary = Path(staging) / "workbook.xlsx"
        book.save(temporary)
        with temporary.open("r+b") as saved:
            os.fsync(saved.fileno())
        os.link(temporary, destination)
        if os.name != "nt":
            fd = os.open(destination.parent, os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    return report(source,destination,request)


def report(source, destination, request):
    wanted = hashlib.sha256(json.dumps([digest(source),request],sort_keys=True).encode()).hexdigest()
    if destination.is_symlink() or not destination.is_file():
        raise ValueError("workbook receipt is missing")
    book = input_book(destination)
    if book.properties.identifier != f"legion-fifo:{wanted}":
        raise ValueError("workbook receipt does not match request")
    sheet = book.worksheets[-1]
    return {"file":str(destination),"sha256":digest(destination),
            "request_sha256":wanted,"analysis_sheet":sheet.title,"charts":len(sheet._charts)}


if __name__ == "__main__":
    action,raw_source,*target = sys.argv[1:]
    source=Path(raw_source)
    if action=="inspect":
        outcome=inspect(source)
    else:
        if action not in ("build","report"):
            raise ValueError("unknown XLSX operation")
        request=json.load(sys.stdin)
        outcome=(build if action=="build" else report)(source,Path(target[0]),request)
    print(json.dumps(outcome,ensure_ascii=False,default=str))
