"""Dependency-free failure envelopes; never publish raw errors or old picks."""
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone


def failed(out,run_id,day,reason):
    public=Path(out)/'public';public.mkdir(parents=True,exist_ok=True)
    value=dict(schema='monty.operations.v1',run_id=run_id,date=day,status='FAILED',
               generated_at=datetime.now(timezone.utc).isoformat(),source_mode='LIVE',
               models={},races=[],blockers=[reason],qualifying_forecasts=0)
    raw=(json.dumps(value,indent=2)+'\n').encode()
    (public/'forecast.json').write_bytes(raw)
    (public/'receipt.json').write_text(json.dumps(dict(schema='monty.operations.v1',run_id=run_id,date=day,status='FAILED',
          generated_at=value['generated_at'],source_mode='LIVE',forecast_sha256=hashlib.sha256(raw).hexdigest(),
          model_artifacts_unchanged=None,blockers=[reason]),indent=2)+'\n')
