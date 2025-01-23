from TanaAPI import Node, FieldNode, SuperTag, CheckboxNode, ReferenceNode, URLNode, DateNode, DummyNode


def format_event_body(event) -> str:
    return event['body'].strip('"').replace(r'\\n', '\n').replace(r'\n', '\n')


def _node_to_markup_formatter(root_node: Node, tag_field_names: dict[str, str]) -> list[str]:
    out_lines = []
    child_offset = '  '
    if isinstance(root_node, ReferenceNode):
            line = f'- [[{root_node.name or ""}^{root_node.target}]]'
    elif isinstance(root_node, CheckboxNode):
            line = f'- [{"x" if root_node.value else " "}] {root_node.name}'
    elif isinstance(root_node, FieldNode):
            line = f'- [[{tag_field_names.get(root_node.attributeId, "")}^{root_node.attributeId}]]::'
    elif isinstance(root_node, URLNode):
        line = f'- [{root_node.name or root_node.url}]({root_node.url})'
    elif isinstance(root_node, DateNode):
        line = f'- [[date:{root_node.name}]]'
    elif isinstance(root_node, DummyNode):
        line = ''
        child_offset = ''
    elif isinstance(root_node, Node):
            line = f'- {root_node.name}'
    else:
        raise ValueError(f'Unknown node type: {type(root_node)}')

    for cur_supertag in root_node.supertags or []:
        supertag_name = tag_field_names.get(cur_supertag.id, '')
        line = f'{line} #[[{supertag_name}^{cur_supertag.id}]]'

    if line:
        out_lines.append(line)

    for child_node in root_node.children or []:
        child_lines = [child_offset + l for l in _node_to_markup_formatter(child_node, tag_field_names)]
        out_lines.extend(child_lines)

    return out_lines

def node_to_markup(root_node: Node, tag_field_names: dict[str, str], include_tana=False) -> str:
    if include_tana:
        return '\n'.join(['%%tana%%'] + _node_to_markup_formatter(root_node, tag_field_names))
    else:
        return '\n'.join(_node_to_markup_formatter(root_node, tag_field_names))
