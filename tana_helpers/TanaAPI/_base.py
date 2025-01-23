import os
import time

import requests

from ._nodes import Node, PlainNode

TANA_API_KEY = os.environ['TanaKey']
API_HEADERS = {'Authorization': f'Bearer {TANA_API_KEY}', 'Content-Type': 'application/json'}
TANA_ENDPOINT = 'https://europe-west1-tagr-prod.cloudfunctions.net/addToNodeV2'

LAST_CALL_TIME = 0

def get_tana_endpoint() -> str:
    global LAST_CALL_TIME
    if LAST_CALL_TIME + 2 > time.time():
        time.sleep(2)

    LAST_CALL_TIME = time.time()
    return TANA_ENDPOINT


class Tana:
    def __init__(self, *children: Node, target_id: str = None):
        self.target_id = target_id
        self.children = list(children)

    def set_target_id(self, target_id: str) -> "Tana":
        self.target_id = target_id
        return self

    def target_inbox(self) -> "Tana":
        return self.set_target_id('INBOX')

    def target_schema(self) -> "Tana":
        return self.set_target_id('SCHEMA')

    def add_children(self, *new_children: Node) -> "Tana":
        self.children += list(new_children)
        return self

    def add_strings(self, *new_names: str) -> "Tana":
        self.children += [PlainNode(name=n) for n in new_names]
        return self

    def submit(self, clear_nodes=True) -> Node:
        data = self.model_dump()

        resp = requests.post(get_tana_endpoint(), headers=API_HEADERS, json=data)
        if resp.status_code == 429:
            time.sleep(5)
            resp = requests.post(get_tana_endpoint(), headers=API_HEADERS, json=data)

        resp.raise_for_status()
        response_json = resp.json()
        response_model = Node.model_validate(response_json)
        if clear_nodes:
            self.children = []
        return response_model

    def model_dump(self):
        data = {'nodes': [n.model_dump(exclude_none=True) for n in self.children]}
        if self.target_id:
            data['targetNodeId'] = self.target_id
        return data

    def change_name(self, new_name: str) -> Node:
        assert self.target_id is not None
        resp = requests.post(get_tana_endpoint(), headers=API_HEADERS, json={
            'targetNodeId': self.target_id,
            'setName': new_name
        })
        resp.raise_for_status()
        return Node.model_validate(resp.json())


if __name__ == '__main__':
    tapi = Tana().target_inbox().add_children(PlainNode(name='hello again', description='huh?', children=['still good?']))
    print(tapi.submit())
