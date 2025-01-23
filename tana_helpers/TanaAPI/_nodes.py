import base64
import mimetypes
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

import tqdm.notebook
from tqdm import tqdm
from typing_extensions import Literal

from pydantic import BaseModel, field_serializer, model_serializer

from enum import Enum

ChildLike = Union["Node", str]

class NodeType(Enum):
    plain = 'plain'
    field = 'field'
    url = 'url'
    date = 'date'
    reference = 'reference'
    boolean = 'boolean'
    file = 'file'
    node = 'node'


class SuperTag(BaseModel):
    id: str


class Node(BaseModel):
    name: Optional[str] = None
    nodeId: Optional[str] = None
    children: Optional[List[ChildLike]] = None
    supertags: Optional[List[SuperTag]] = None
    description: Optional[str] = None
    dataType: Optional[NodeType] = None
    type: Optional[NodeType] = None

    @field_serializer('dataType', 'type')
    def serialize_types(self, node_type: NodeType, _info) -> str:
        return node_type.value

    @field_serializer('children')
    def serialize_children(self, children, _info) -> Optional[List[Dict[str, Any]]]:
        if children is None:
            return None

        out_list = []
        for cur_child in children:
            if isinstance(cur_child, Node):
                out_list.append(cur_child.model_dump())
            elif isinstance(cur_child, str):
                out_list.append({'name': cur_child})
        return out_list or None

    def model_dump(self, *, mode: Literal['json', 'python'] | str = 'python', include = None,
                   exclude = None, by_alias: bool = False, exclude_unset: bool = False,
                   exclude_defaults: bool = False, exclude_none: bool = True, round_trip: bool = False,
                   warnings: bool = True) -> dict[str, Any]:
        return super().model_dump(mode=mode, include=include, exclude=exclude, by_alias=by_alias,
                                  exclude_unset=exclude_unset, exclude_defaults=exclude_defaults,
                                  exclude_none=exclude_none, round_trip=round_trip, warnings=warnings)

class DummyNode(Node):
    name: str = ''

class PlainNode(Node):
    name: str

class DateNode(Node):
    dataType: NodeType = NodeType.date

class CheckboxNode(Node):
    name: str
    dataType: NodeType = NodeType.boolean
    value: bool = False

class URLNode(Node):
    url: str
    name: str = ''
    dataType: NodeType = NodeType.url

    @model_serializer()
    def serializer(self):
        return {
          "type": "field",
          "attributeId": "URLFieldId",
          "children": [
            {
              "dataType": NodeType.url.value,
              "name": self.url,
            }
          ]
        }


class FieldNode(Node):
    type: NodeType = NodeType.field
    attributeId: str = None

    def __call__(self, *values: ChildLike):
        return self.model_copy(update=dict(children=values), deep=True)


class ReferenceNode(Node):
    dataType: NodeType = NodeType.reference
    target: PlainNode

    @model_serializer()
    def serializer(self):
        return {'dataType': NodeType.reference.value,
                'id': self.target.nodeId}


class LargeFileError(ValueError):
    MAX_LEN = 4900

    def __init__(self, encoded_size):
        self.encoded_size = encoded_size
        super().__init__(f'File data string is too long to post: {encoded_size} > {self.MAX_LEN}')


class FileNode(Node):
    dataType: NodeType = NodeType.file
    file: str
    filename: str
    contentType: str

    @classmethod
    def from_bytes(cls, file_data: bytes, file_name: str):
        mime_type = mimetypes.guess_type(file_name)[0]
        encoded_data = base64.b64encode(file_data)
        tqdm.write(str(len(encoded_data)))
        # if len(encoded_data) > LargeFileError.MAX_LEN:
        #     raise LargeFileError(len(encoded_data))
        return cls(file=encoded_data, filename=file_name, contentType=mime_type)

    @classmethod
    def from_path(cls, path: Union[Path, str]):
        path = Path(path)
        return cls.from_bytes(path.read_bytes(), path.name)


class APIResponse(BaseModel):
    pass


if __name__ == '__main__':
    from pprint import pprint
    node_model = PlainNode(name='top', children=[PlainNode(name='first'), 'second'])
    pprint(node_model.model_dump(exclude_none=True))
