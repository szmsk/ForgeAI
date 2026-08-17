#!/usr/bin/env python3
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"backend"))
from app.agent.engine import ForgeAgent
from app.models.schemas import RunRequest

def main():
 tasks=[]
 for path in sorted((Path(__file__).parent/"tasks").glob("*.json")):
  tasks.append(json.loads(path.read_text()))
 if not tasks:
  print("No benchmark tasks found"); return
 results=[]; started=time.time()
 for t in tasks:
  r=ForgeAgent().run(RunRequest(**t)); results.append({"task_id":t["id"],"success":r.status.value=="success","tests_passed":r.tests_passed,"tests_total":r.tests_total,"iterations":r.iterations,"duration_ms":r.duration_ms,"cost_usd":r.cost_usd})
 success=sum(x["success"] for x in results)/len(results)
 out={"tasks":len(results),"success_rate":success,"avg_duration_ms":sum(x["duration_ms"] for x in results)/len(results),"results":results,"wall_time_s":time.time()-started}
 print(json.dumps(out,indent=2))
(Path(__file__).parent/"report.json").write_text(json.dumps(out,indent=2))
if __name__=="__main__": main()
