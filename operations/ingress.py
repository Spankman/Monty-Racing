"""Acknowledge and validate an opened Monty issue before provisioning scoring."""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from operations import issue_delivery, transport


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    issue = event['issue']
    if not transport.addressed_to_monty(issue):
        return
    number = issue['number']
    workflow = f"https://github.com/{transport.REPO}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    try:
        request = transport.validated_request(issue)
    except (ValueError, TypeError, KeyError) as exc:
        reason = str(exc) if type(exc) is ValueError else 'Missing issue metadata.'
        issue_delivery.report(number, 'ack', f'**Monty received request #{number}.** [Workflow]({workflow})')
        if not issue_delivery.report(number, 'terminal', f'**Monty FAILED — invalid request.** {reason} [Workflow]({workflow})'):
            raise RuntimeError('Unable to deliver invalid-command diagnostic')
        return
    # A comment outage must not prevent a valid request from reaching scoring.
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
        output.write('route=true\n')
    issue_delivery.report(number, 'ack',
        f"**Monty QUEUED** · Request #{number} accepted. "
        f"Requested command: `{request['command']}`. [Workflow]({workflow}). "
        "The terminal result will appear on this issue.")


if __name__ == '__main__':
    main()
