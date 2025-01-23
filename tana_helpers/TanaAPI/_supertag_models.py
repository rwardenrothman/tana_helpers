from pydantic_core import ValidationError

from ._nodes import *


class SupertagField:
    def __init__(self, field_id: str, field_type: NodeType = NodeType.plain):
        self.type = field_type
        self.node = FieldNode(attributeId=field_id)

    def __set_name__(self, owner, name):
        self.private_name = f'_field_{name}'
        self.resolver_name = f'_field_{name}_resolver'

    def __set__(self, instance, value: List[ChildLike]):
        setattr(instance, self.private_name, value)
        setattr(instance, self.resolver_name, lambda x: self.resolve_field(x))

    def __get__(self, instance, owner) -> List[ChildLike]:
        try:
            return getattr(instance, self.private_name)
        except AttributeError:
            self.__set__(instance, [])
            return getattr(instance, self.private_name)

    def _make_child(self, value):
        match (self.type, value):
            case (NodeType.plain, str()):
                return PlainNode(name=value)
            case (NodeType.plain, Node()):
                return value
            case (NodeType.plain, _):
                return PlainNode(name=str(value))
            case (NodeType.reference, str()):
                return ReferenceNode(target=PlainNode(nodeId=value, name=''))
            case (NodeType.reference, Node()):
                return ReferenceNode(target=value)
            case _:
                return PlainNode(name=value, dataType=self.type.value)

    def resolve_field(self, instance) -> FieldNode:
        self.node.children = [self._make_child(v) for v in getattr(instance, self.private_name, [])]
        return self.node



class SupertagBase:
    supertag_id: str = ''

    def __init__(self, name: str):
        self.node = PlainNode(name=name, supertags=[SuperTag(id=self.supertag_id)])
        self.children: List[ChildLike] = []

    def model_dump(self, *, mode: Literal['json', 'python'] | str = 'python', include = None,
                   exclude = None, by_alias: bool = False, exclude_unset: bool = False,
                   exclude_defaults: bool = False, exclude_none: bool = True, round_trip: bool = False,
                   warnings: bool = True) -> dict[str, Any]:

        # generate children from fields
        self.node.children = []

        for potential_field in self.__dir__():
            if potential_field.endswith('_resolver') and getattr(self, potential_field.replace('_resolver', '')):
                try:
                    self.node.children.append(
                        getattr(self, potential_field)(self)
                    )
                except ValidationError:
                    raise

        self.node.children.extend(self.children)

        return self.node.model_dump(mode=mode, include=include, exclude=exclude, by_alias=by_alias,
                                  exclude_unset=exclude_unset, exclude_defaults=exclude_defaults,
                                  exclude_none=exclude_none, round_trip=round_trip, warnings=warnings)



