"""This module helps to create the documentation in all notebooks in this folder."""


import requests
import urllib
import pandas as pd
from markdown import markdown
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter
from pprint import pformat
from IPython.core.display import display, HTML
from IPython.display import display as display_df

server = "http://0.0.0.0:5000"
#server = "http://api.ebel.scai.fraunhofer.de"
api_version = "/api/v1"
basic_url = server + api_version

example_protein = requests.get(f"{basic_url}/bel/edges?subject_node_class=protein&relation=bel_relation&page_size=1&page=1").json()['results'][0]
example_protein_rid = example_protein['subject_rid']
example_protein_name = example_protein['subject_name']
example_protein_namespace = example_protein['subject_namespace']

swagger = requests.get(server + "/openapi.json").json()
additional_paramters = {
    '/api/v1/bel/adjacent_nodes_by_rid': {'rid': example_protein_rid},
    '/api/v1/bel/by_rid': {'rid': example_protein_rid},
    '/api/v1/bel/pure_rid': {'name': example_protein_name, 'namespace': example_protein_namespace}
}

def get_api_methods_by_tag(tag):
    index = 0
    for c  in swagger['paths'].items():
        method, config = c
        if 'get' in config and 'tags' in config['get'] and tag in config['get'].get('tags'):
            index += 1
            data = config['get']
            operationId = data['operationId']
            display(HTML(f"<h2>{index}. {data['summary']}</h2>"))
            description = markdown(data['description'])
            display(HTML(f"<b style=\"color: rgb(98,98,98); text-decoration: underline;\">Description:</b> {description}"))
            display(HTML(f"<b>Tags:</b> {data['tags']}"))
            display(HTML(f"<b>Server path:</b> {method}"))
            pd_df_data = []
            cols=['parameter name', 'data type', 'description', 'example', 'options', 'default', 'required']
            parameters = data.get('parameters')
            url = server + method
            if parameters:
                for x in parameters:
                    param_props = (x['name'], 
                                x['schema']['type'], 
                                x.get('description'), 
                                x['schema'].get('example'),
                                x['schema'].get('enum'),
                                x['schema'].get('default'),
                                bool(x.get('required')))
                    pd_df_data.append(param_props)
                df_params = pd.DataFrame(pd_df_data, columns=cols).set_index('parameter name').fillna('')
                display_df(df_params)
                example_params = {}
                for param_name, param_conf  in df_params.to_dict('index').items():
                    if param_conf['example']:
                        if param_conf['data type'] == 'integer':
                            example_params[param_name] = int(param_conf['example'])
                        else:
                            example_params[param_name] = param_conf['example']
                if method in additional_paramters:
                    example_params.update(additional_paramters[method])
                    additional_parameter_names = ', '.join([str(x) for x in additional_paramters[method].keys()])
                    explanation = "Because values in the knowledge graph are dependent from the imported BEL docuemnts," \
                        f" we added to the parameters ({additional_parameter_names}) the following values:"
                    print(explanation)
                    display_df(pd.DataFrame(additional_paramters[method].items(), columns=['paramter', 'value']).set_index('paramter'))
                url = server + method + "?" +urllib.parse.urlencode(example_params)
                
            else:
                print('without paramters')
            display(HTML(f"<b>Example URL:</b> <a href=\"{url}\">{url}</a>"))
            result = requests.get(url).json()
            
            if isinstance(result, list):
                print(f"\nThe result is a list and have {len(result)} entries. Here we show only the first entry.\n")
                show_result = result[0]
            else:
                show_result = result
            display(HTML(f"<b style=\"color: rgb(98,98,98); text-decoration: underline;\">Example response:</b>"))
            print(highlight(pformat(show_result), PythonLexer(), Terminal256Formatter()))
            print(f"For further testing go to {server}/ui/#/{tag}/{operationId}")
                