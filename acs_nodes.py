import time
import re
import json
import asyncio
import aiohttp
from termcolor2 import colored
import colorama
import logging

SERIAL = '53434F4D1A0A12BB'
NODE_RE = re.compile(r'(\S+)\s*:\s*(\S+)')
HEADERS = json.loads('{"Content-Type":"application/json"}')
logging.basicConfig(level=logging.DEBUG)
logging.disable(logging.DEBUG)
colorama.init()

def get_nodes():
    nodelist = []
    with open("tr_nodes.txt", 'r') as f:
        for line in f:
            line = re.search(NODE_RE, line)
            if line is not None:
                node_key = line.group(1)
                node_value = line.group(2)
                nodelist.append({node_key: node_value})
    return nodelist

async def request_nodes(post_fields, session):
    result = {}
    acs_url_reutov = 'http://172.17.87.238:9673/rtk/CPEManager/DMInterfaces/rest/v1/action/GetParameterValues'
    async with session.post(acs_url_reutov, json = post_fields) as response:
        data = await response.json()
        logging.debug(data)
        if data['Result']['code'] == 200:
            data_key = str( data['Result']['details'][0]['key'])
            data_value = str(data['Result']['details'][0]['value'])
        else:
            data_key = data['Result']['code']
            data_value = data['Result']['message']
        result[data_key] = data_value
        return result


async def main():
    tasks = []
    nodelist = get_nodes()
    conn = aiohttp.TCPConnector(limit=50)
    auth = aiohttp.BasicAuth(login='nwt', password='testlab123')
    async with aiohttp.ClientSession(connector=conn, auth=auth) as session:
        for node in nodelist:
            post_fields = json.loads('{"CPEIdentifier": {"cpeid": "%s"}, "CommandOptions": {"Sync":1, "Lifetime":60}, "Parameters": ["%s"]}' % (SERIAL, list(node.keys())[0]))
            task = asyncio.create_task(request_nodes(post_fields, session))
            tasks.append(task)
        result = await asyncio.gather(*tasks)

    with open('result.txt', 'w+') as f:

        for node in nodelist:
            if list(node.keys())[0] in [list(line.keys())[0] for line in result]:
                for line in result:
                    if list(line.keys())[0] == list(node.keys())[0]:
                        if line[list(node.keys())[0]] == list(node.values())[0]:
                            msg = 'OK {} = {}'.format(list(node.keys())[0], list(line.values())[0])
                            print(colored(msg, 'green'))
                            f.write('{}\n'.format(msg))
                        else:
                            msg = 'ERROR {} should be {},  actual {}'.format(list(node.keys())[0], node[list(node.keys())[0]],
                                                                           line[list(line.keys())[0]])
                            print(colored(msg, 'red'))
                            f.write('{}\n'.format(msg))
            else:
                print(colored('No NODE', 'red'))
                f.write('NO NODE\n')

if __name__ == "__main__":
    t0 = time.time()
    asyncio.run(main())
    print('Request time: {}'.format(time.time() - t0))





