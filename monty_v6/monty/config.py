from pathlib import Path
import json,numpy as np
HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'results'
def dump(n,v):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/n).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)))
