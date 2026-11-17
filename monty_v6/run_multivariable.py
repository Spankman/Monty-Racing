"""Backward-compatible entry point; implementation lives in monty/."""
from monty.normalization import normal,full_clock_seconds,clean_person,condition,numeric_class,distance_band
from monty.ingestion import join_sources,validate_overlay,add_overlays
from monty.features import statistics,residual,build_features
from monty.pipeline import run
if __name__=='__main__':run()
