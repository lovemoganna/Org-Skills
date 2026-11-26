import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from openpyxl import Workbook, load_workbook

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from greenhouse_jobs import verify, identity
from xlsx_fifo import build, report

class StandardToolsTests(unittest.TestCase):
    def test_ats_filters_closed_and_deduplicates(self):
        base="https://job-boards.greenhouse.io/exchange/jobs/"
        seen=[]
        def fetch(board,job):
            seen.append(job)
            if job=="42":
                return "api",None,"HTTP_404"
            return "api",{"id":int(job),"absolute_url":base+job,"title":"KYB analyst",
               "location":{"name":"Singapore; Hong Kong"},
               "questions":[{"fields":[{"type":"input_text"}]}],"content":"KYB customer due diligence"} ,None
        entries=[{"url":base+v} for v in ("41","41?x=1","42")]
        entries.append({"url":"https://job-boards.greenhouse.io.evil.invalid/exchange/jobs/43"})
        d=verify(entries,["KYB"],["Singapore"],["due diligence"],3,fetch,lambda _:("board",{"jobs":[]},None))
        self.assertEqual(sorted(seen),["41","42"])
        self.assertEqual(len(d["roles"]),1)
        self.assertEqual(d["attempts"][1]["reason"],"HTTP_404")
        self.assertIsNone(identity("file:///exchange/jobs/43"))

    def test_live_board_fallback_discards_expired_search_hit(self):
        base="https://job-boards.greenhouse.io/ex/jobs/"
        current={"id":43,"absolute_url":base+"43","title":"KYB Analyst","location":{"name":"Singapore"}}
        def fetch(board,job):
            if job=="42":
                return "api",None,"HTTP_404"
            return "api",{**current,"questions":[{"fields":[{"type":"text"}]}],"content":"customer due diligence"},None
        d=verify([{"url":base+"42"}],["KYB"],["Singapore"],["due diligence"],1,fetch,
                 lambda board:("live-board",{"jobs":[{**current,"title":"Backend Engineer - KYB"},current]},None),
                 exclude_titles=["engineer"])
        self.assertEqual(d["attempts"][0]["reason"],"HTTP_404")
        self.assertEqual(d["roles"][0]["job_id"],"43")
        self.assertEqual(d["fallback_boards"][0]["candidates"],[["ex","43"]])

    def test_fifo_create_only_and_verified_request(self):
        with TemporaryDirectory() as tmp:
            src=Path(tmp)/"source.xlsx"
            dst=Path(tmp)/"result.xlsx"
            book=Workbook()
            s=book.active
            s.append(["Ref","Market","UTC","Side","Qty"])
            s.append(["S0","M","2026-02-01T09:00:00Z","SELL",2])
            s.append(["B1","M","2026-02-01T09:01:00Z","BUY",3])
            s.append(["S1","M","2026-02-01T09:10:00Z","SELL",4])
            s.append(["S1","M","2026-02-01T09:10:00Z","SELL",4])
            book.save(src)
            args={"sheet":s.title,"columns":dict(id="Ref",pair="Market",time="UTC",side="Side",quantity="Qty"),"window_minutes":20}
            actual=build(src,dst,args)
            self.assertEqual(actual,report(src,dst,args))
            output=load_workbook(dst)
            self.assertEqual(list(output.worksheets[0].values),list(s.values))
            self.assertEqual(list(output.worksheets[1].values)[2][2:5],(3,9,3))
            self.assertIsNotNone(output.worksheets[1]._charts[0].series[0].cat.strRef)
            with self.assertRaises(FileExistsError):
                build(src,dst,args)
            with self.assertRaises(ValueError):
                report(src,dst,{**args,"window_minutes":30})
