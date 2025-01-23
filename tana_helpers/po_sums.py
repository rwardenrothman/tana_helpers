import re

from _helper_fxns import format_event_body


def lambda_handler(event, context):
    """
    """

    body = format_event_body(event)
    total_re = re.compile(r'- Total:: (\d+)')
    total = sum(map(int, total_re.findall(body)))

    return {
        "statusCode": 200,
        "body": total,
    }
