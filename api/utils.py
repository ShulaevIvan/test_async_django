import re
import os
import json
from pprint import pprint

import asyncio


async def select_email_template_by_order(order_type):
    json_path = f'{os.getcwd()}/email_tepmlates.json'
    with open(json_path, 'r') as json_file:
        template_data = json.load(json_file)
    
    target_template = list(filter(lambda item: item.get('template_name') == order_type, template_data))
    if len(target_template) > 0:
        return target_template[0]
    return target_template


