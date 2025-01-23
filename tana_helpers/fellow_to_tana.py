import json
import re
from enum import Enum
import TanaAPI as tapi
from _helper_fxns import node_to_markup

MEETING_SUPERTAG = tapi.SuperTag(id='fSSZ0t72ib5W')
SUMMARY_FIELD = tapi.FieldNode(attributeId='rc9RrqE67ogA')
DATE_FIELD = tapi.FieldNode(attributeId='SYS_A90')
TRANSCRIPT_FIELD = tapi.FieldNode(attributeId='PjRWf5Mcrz_m')

tag_names = {
    MEETING_SUPERTAG.id: 'Meeting',
    SUMMARY_FIELD.attributeId: 'Summary',
    DATE_FIELD.attributeId: 'Date',
    TRANSCRIPT_FIELD.attributeId: 'Transcript',
}

class LineType(Enum):
    root = 0
    bullet = 1
    numbered = 2
    topic = 3
    action = 4
    text = 5
    empty = 6


def lambda_handler(event, context):
    """
    """
    body = event['body'].strip("\"- \n")
    body_dict = dict(re.findall(r"'(.*?)':\s+'(.*?)'", body))
    start_date = body_dict['event_start'].split('T')[0]

    # parse the lines
    cur_indent = -1
    root_node = tapi.PlainNode(name=body_dict['title'], supertags=[MEETING_SUPERTAG], children=[
        DATE_FIELD(tapi.DateNode(name=start_date)),
        tapi.URLNode(url=body_dict['fellow_url'], name=f'Link to Fellow Meeting: {body_dict["title"]} on {start_date}'),
    ])
    last_indent_node: dict[int, tapi.Node] = {-1: root_node, -2: root_node}
    for i, cur_line in enumerate(['root'] + body_dict['note_text'].replace('\\\\n','\n').splitlines()):
        if i == 0:
            continue
        elif cur_line == '':
            continue
        elif m := re.match(r'^(\s*)\([\sxX]\) (.*)', cur_line):
            # process the pattern
            spaces, text = m.groups()
            cur_type = LineType.topic
            extra_indent = 1
        elif m := re.match(r'^(\s*)•\s+(.*)', cur_line):
            # process the pattern
            spaces, text = m.groups()
            cur_type = LineType.bullet
            extra_indent = 1
        elif m := re.match(r'^(\s*)\[([\sxX])] (.*)', cur_line):
            spaces, checked, text = m.groups()
            cur_type = LineType.action
            extra_indent = 2
        elif m := re.match(r'^(\s*)(.*)', cur_line):
            spaces, text = m.groups()
            cur_type = LineType.text
            extra_indent = 0
        else:
            continue

        node_name = text.strip(' •')
        if node_name == '':
            continue

        if cur_type == LineType.action:
            cur_node = tapi.CheckboxNode(name=node_name, value=False if checked == ' ' else True)
        elif cur_type == LineType.topic:
            cur_node = tapi.PlainNode(name=f'**{node_name}**')
        else:
            cur_node = tapi.PlainNode(name=node_name)

        # figure out the indentation
        line_indent = len(spaces) + extra_indent
        parent_indent = line_indent - 1
        line_offset = 0
        while parent_indent > cur_indent:
            last_indent_node[line_indent] = cur_node
            cur_node = tapi.DummyNode(children=[cur_node])
            line_indent -= 1
            parent_indent -= 1
            line_offset += 1
        line_indent = parent_indent + 1

        # place in the graph
        parent_node = last_indent_node[parent_indent]
        if parent_node.children is None:
            parent_node.children = [cur_node]
        else:
            parent_node.children.append(cur_node)

        cur_indent = line_indent + line_offset
        last_indent_node[line_indent] = cur_node

    return {
        "statusCode": 200,
        "body": node_to_markup(root_node, tag_names),
    }

if __name__ == '__main__':
    with open('events/fellow_submission_2.json') as f:
        event = json.load(f)

    print(lambda_handler(event, None)['body'])