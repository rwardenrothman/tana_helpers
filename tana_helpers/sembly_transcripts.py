import json
import re

from requests import HTTPError

from _helper_fxns import format_event_body
import TanaAPI as tapi

MEETING_SUPERTAG = tapi.SuperTag(id='fSSZ0t72ib5W')
SUMMARY_FIELD = tapi.FieldNode(attributeId='rc9RrqE67ogA')
DATE_FIELD = tapi.FieldNode(attributeId='SYS_A90')
TRANSCRIPT_FIELD = tapi.FieldNode(attributeId='PjRWf5Mcrz_m')


def lambda_handler(event, context):
    """
    """

    body = json.loads(event['body'])
    print(body)
    transcript_blocks = []
    for cur_block in body['meeting_transcription'].split('\n\n'):
        if not cur_block:
            continue

        # print(repr(cur_block))
        speaker, *text = [l.strip() for l in cur_block.splitlines()]
        if len(text) > 1:
            s_node = tapi.PlainNode(name=speaker, children=text)
        else:
            s_node = tapi.PlainNode(name=f'**{speaker}:** {text[0]}')

        transcript_blocks.append(s_node)

    tx_node = tapi.PlainNode(name='Sembly Transcript', children=transcript_blocks[:90])
    t = tapi.Tana().target_inbox().add_children(n := tapi.PlainNode(name=body['meeting_title'],
                                                                    # supertags=[MEETING_SUPERTAG],
                                                                    children=[
                                                                        TRANSCRIPT_FIELD(tx_node)
                                                                    ]))
    try:
        out_node = t.submit(clear_nodes=True)
        print(out_node.model_dump())
        transcript_node_id = out_node.children[0].children[0].nodeId
        t.set_target_id(transcript_node_id)
        while len(transcript_blocks) > 90:
            transcript_blocks = transcript_blocks[90:]
            t.add_children(*transcript_blocks[:90])
            t.submit()

    except HTTPError:
        print(t.model_dump())
        raise

    return {
        "statusCode": 200,
        "body": "success",
    }
