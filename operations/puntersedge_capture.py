"""Explicit staged PE acquisition -> unchanged shared frozen inference.

Not imported by the production worker or six-day trial. One existing board call,
no automatic form/history/acceptance acquisition and no default provider switch.
"""
from puntersedge_adapter import canonical_race,ProviderError

class Acquisition:
    def __init__(self,client,*,day,venue,race_id,book='tab',acceptance=None):
        self.client=client;self.day=day;self.venue=venue;self.race_id=race_id;self.book=book;self.acceptance=acceptance
        self.used=False
    def __call__(self,recorder):
        if self.used:raise ProviderError('Acquisition already consumed; no duplicate provider call')
        self.used=True
        previous=self.client.observer
        # Original bytes are captured before parsing/canonicalisation. No receipt
        # claims complete raw evidence when retention is not authorised.
        self.client.observer=recorder.raw if recorder.enabled else None
        try:
            rows=self.client.get('/v1/racing/next-to-go',dict(num_races=20,categories='horse',country='AU',venue=self.venue),command='STAGED_EVIDENCE')
            if not isinstance(rows,list):raise ProviderError('Board shape invalid')
            matches=[r for r in rows if r.get('race_id')==self.race_id and r.get('venue')==self.venue]
            if len(matches)!=1:raise ProviderError('Exact requested race missing or duplicated; no substitution')
            payload=canonical_race(matches[0],day=self.day,book=self.book,acceptance=self.acceptance)
            payload['meta']['capture_scope']='Exact requested race; original full returned board retained if permitted'
            payload['meta']['field_completeness']='PROVIDER ACCEPTANCE MATCH ONLY' if self.acceptance is not None else 'INDEPENDENT COMPLETENESS UNVERIFIED'
            return payload
        finally:self.client.observer=previous


def execute(client,day,output,v7_root,*,run_id,venue,race_id,request,policy=None,certificate=None,book='tab',acceptance=None,**testing):
    from monty_operations import execute as infer
    # A caller must explicitly select this integration. C is rejected before any
    # acquisition even if invoked incorrectly instead of using the read-only client.
    if request.get('command','').strip().upper()=='C':raise ProviderError('C is read-only')
    source=Acquisition(client,day=day,venue=venue,race_id=race_id,book=book,acceptance=acceptance)
    return infer(day,output,v7_root,run_id=run_id,request=request,evidence_policy=policy,
                 evidence_certificate=certificate,evidence_source='PuntersEdge',acquisition=source,**testing)
