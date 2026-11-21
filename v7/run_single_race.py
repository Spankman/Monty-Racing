"""Explicit research-only canonical-to-V7 single-race execution.

Does not fetch live fields, independently verify sources, or authorise bets.
Use only after an operator independently verifies all active runners, scratchings,
fixed-win quotes and source attribution. Missing optional features are imputed
by the original trained V7 model; never invent missing identities or prices.
"""
import argparse
from pathlib import Path
import pandas as pd
from .canonical_bridge import to_v7_fields
from .predict import run

def execute(input_csv, *, date, country, source_url, model_path, output_dir,
            independently_verified=False):
    if not independently_verified:
        raise ValueError("Explicit independent field and scratching verification required")
    rows=pd.read_csv(input_csv,dtype={"meeting":str,"race":str,"number":str,"horse":str})
    if rows[["meeting","race"]].drop_duplicates().shape[0]!=1:
        raise ValueError("Single-race mode requires exactly one race")
    fields=to_v7_fields(rows,date=date,country=country,source_url=source_url,
                        field_verified=True)
    output_dir=Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError("Output directory must be empty to protect frozen predictions")
    output_dir.mkdir(parents=True,exist_ok=True)
    prepared=output_dir/"verified_v7_input.csv"
    fields.to_csv(prepared,index=False)
    run(Path(model_path),prepared,output_dir)
    return output_dir/"v7_research_scores.csv"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_csv",type=Path)
    p.add_argument("--date",required=True)
    p.add_argument("--country",choices=["AU","NZ"],required=True)
    p.add_argument("--source-url",required=True)
    p.add_argument("--model",type=Path,default=Path("v7/artifacts/fold_3_model.json"))
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--independently-verified",action="store_true")
    a=p.parse_args()
    print(execute(a.input_csv,date=a.date,country=a.country,source_url=a.source_url,
                  model_path=a.model,output_dir=a.output_dir,
                  independently_verified=a.independently_verified))

if __name__=="__main__":
    main()
