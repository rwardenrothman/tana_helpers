import json
import re

from requests import HTTPError

from _helper_fxns import format_event_body
import TanaAPI as tapi

MEETING_SUPERTAG = tapi.SuperTag(id='fSSZ0t72ib5W')
SUMMARY_FIELD = tapi.FieldNode(attributeId='rc9RrqE67ogA')
DATE_FIELD = tapi.FieldNode(attributeId='SYS_A90')


def lambda_handler(event, context):
    """
    """

    body = json.loads(event['body'])
    print(body)
    t = tapi.Tana().target_inbox().add_children(n := tapi.PlainNode(name=body['meeting_title'],
                                                                    supertags=[MEETING_SUPERTAG],
                                                                    children=[]))

    summary_head, summary_text, _, outline_head, *outline_lines = body['meeting_notes'].splitlines()
    n.children.append(SUMMARY_FIELD(summary_text))
    start_date = body['meeting_started_at'].split('T')[0]
    n.children.append(DATE_FIELD(tapi.DateNode(name=start_date)))
    n.children.append(outline_top := tapi.PlainNode(name=outline_head, children=[]))
    cur_base = outline_top
    header_re = re.compile(r'\d+.* • \d+:\d\d:\d\d')
    for line in outline_lines:
        if header_re.search(line):
            cur_base = tapi.PlainNode(name=line, children=[])
            outline_top.children.append(cur_base)
        else:
            cur_base.children.append(line.strip(' -'))

    try:
        t.submit(clear_nodes=False)
    except HTTPError:
        print(t.model_dump())
        raise

    return {
        "statusCode": 200,
        "body": "success",
    }
