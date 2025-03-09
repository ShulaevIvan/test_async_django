import re
import os
import json
from pprint import pprint


def select_email_template_by_order(order_type):
    json_path = f'{os.getcwd()}/email_tepmlates.json'
    with open(json_path, 'r') as json_file:
        template_data = json.load(json_file)

    pprint(template_data)


