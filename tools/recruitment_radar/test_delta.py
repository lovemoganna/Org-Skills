"""No-network regression tests for radar duplicate and evidence gates."""
import unittest
from delta import plan, job_key, url_clean, HEADER, LOG_HEADER, SHEET_ID

def candidate(**kw):
    data={
        "company":"Binance","title":"Risk Strategist","official_url":"https://job-boards.eu.greenhouse.io/binance/jobs/5011782101?gh_src=x&utm_campaign=y",
        "official_status":"open","application_verified":True,
        "evidence_url":"https://job-boards.eu.greenhouse.io/binance/jobs/5011782101",
        "checked_at_beijing":"2026-11-25 12:00 北京","location":"Hong Kong",
        "newness_basis":"proven_absent_prior_snapshot",
        "newness_evidence_url":"https://example.org/prior",
    }
    data.update(kw)
    return data

def input_data(**changes):
    data={"spreadsheet_id":SHEET_ID, "main_rows":[HEADER], "change_rows":[LOG_HEADER],
          "historical_complete":False, "historical_keys":[], "candidates":[]}
    data.update(changes)
    return data

class TestDelta(unittest.TestCase):
    def test_gh_tracking_key(self):
        self.assertEqual(job_key(candidate()), "binance|5011782101")
        self.assertEqual(url_clean(candidate()["official_url"]), "https://job-boards.eu.greenhouse.io/binance/jobs/5011782101")
    def test_lever_key(self):
        self.assertEqual(job_key(candidate(company="Coins.ph",official_url="https://jobs.lever.co/coins/1096d07a-86c5-460d-a800-d3f155da0d38")), "coinsph|1096d07a-86c5-460d-a800-d3f155da0d38")
    def test_incomplete_history_no_new(self):
        r=plan(input_data(candidates=[candidate()]))
        self.assertEqual(r["status"],"NO_PROVEN_DELTA")
    def test_new_label_never_a_publish_date(self):
        r=plan(input_data(historical_complete=True,candidates=[candidate(newness_basis="linkedIn_new")]))
        self.assertEqual(r["status"],"NO_PROVEN_DELTA")
    def test_verified_new_once(self):
        r=plan(input_data(historical_complete=True,candidates=[candidate(),candidate()]))
        self.assertEqual(len(r["writes"]),1)
        self.assertEqual(r["writes"][0]["row"][19],"未投递")
    def test_known_historical_key_not_new(self):
        r=plan(input_data(historical_complete=True,historical_keys=["binance|5011782101"],candidates=[candidate()]))
        self.assertFalse(r["writes"])
    def test_existing_change_only_verified_fields(self):
        old=["binance|5011782101","Binance","Binance","Risk Strategist","Trading Risk","Hong Kong","Remote","待确认","Greenhouse","https://job-boards.eu.greenhouse.io/binance/jobs/5011782101","","","","","","旧状态","历史存量","","重点","已投递","用户备注"]
        c=candidate(prior_comparable_evidence="snapshot", material_changes={"申请状态":{"before":"旧状态","after":"官方申请入口开放"}})
        r=plan(input_data(main_rows=[HEADER,old],candidates=[c]))
        self.assertEqual(len(r["writes"]),1)
        self.assertEqual([x["column"] for x in r["writes"][0]["changes"]],[15])
        self.assertFalse(set([18,19,20]) & {x["column"] for x in r["writes"][0]["changes"]})
    def test_missing_comparison_no_change(self):
        old=["binance|5011782101","Binance"]
        r=plan(input_data(main_rows=[HEADER,old],candidates=[candidate()]))
        self.assertFalse(r["writes"])
    def test_apply_unverified_blocked(self):
        r=plan(input_data(historical_complete=True,candidates=[candidate(application_verified=False)]))
        self.assertFalse(r["writes"])
    def test_duplicate_base_blocked(self):
        r=plan(input_data(main_rows=[HEADER,["x"],["x"]]))
        self.assertEqual(r["status"],"BLOCKED_BASELINE")
    def test_wrong_spreadsheet_blocked(self):
        with self.assertRaises(ValueError):
            plan(input_data(spreadsheet_id="wrong"))
    def test_official_first_publish_after_baseline_is_allowed(self):
        c=candidate(newness_basis="official_first_published",
                    first_published_source="official_ats",
                    first_published="2026-11-25",
                    historical_last_push_date="2026-11-24")
        r=plan(input_data(candidates=[c]))
        self.assertEqual(len(r["writes"]),1)
    def test_official_first_publish_before_baseline_is_blocked(self):
        c=candidate(newness_basis="official_first_published",
                    first_published_source="official_ats",
                    first_published="2026-11-20",
                    historical_last_push_date="2026-11-24")
        r=plan(input_data(candidates=[c]))
        self.assertFalse(r["writes"])
if __name__=="__main__":unittest.main()
