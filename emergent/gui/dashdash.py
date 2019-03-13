import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import emergent
import sys

def dropdown(items, obj_id = ''):
    options = []
    for item in items:
        options.append({'label': item, 'value': item})
    
    return html.Div([
            dcc.Dropdown(
                    options=options,
                    id = obj_id+'-dropdown',
                    value=items[0]
                        ),
            html.Div(id=obj_id+'-container')])


def table(d, obj_id = ''):
    rows = []
    for key in list(d.keys()):
        r = html.Tr([html.Td(key), html.Td(d[key])])
        rows.append(r)
    return dbc.Table(html.Table(rows), bordered=True, dark=True, hover=True, responsive=True, striped=True, id=obj_id+'-table')
            
external_stylesheets=[dbc.themes.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets = external_stylesheets, static_folder = 'media')

network_style = {'background-color': 'white',
               'opacity': 0.9,
               'width': 'parent.width',
               'height': 'parent.height',
               'x':0,
               'y':20
               }

panel_style = {'background-color': 'white',
               'opacity': 0.9,
               'width': 'parent.width',
               'height': 'parent.height',
               'x':20,
               'y':20
               }

panel_style = {}
''' Network tree '''
tree = html.Div([html.H1('Network'), html.P('Network here')], className = 'network-tree')


''' Models column '''
models_dropdown = dropdown(['GaussianProcess', 'Nonlinear'], obj_id='models')
#model_table = table({}, 'models')
columns = [{'name': 'Parameter', 'id': 'Parameter'}, {'name': 'Value', 'id': 'Value'}]
model_table = dash_table.DataTable(data=[{}], columns=columns, id='models-table', editable=True)
model_col = html.Div([dbc.Col([html.H2('Models'), models_dropdown, model_table])], style=panel_style)


''' Samplers column '''
samplers_dropdown = dropdown(['Grid', 'Online'], 'samplers')
sampler_table = dash_table.DataTable(data=[{}], columns=columns, id='samplers-table')

samplers_col = html.Div([dbc.Col([html.H2('Samplers'), samplers_dropdown, sampler_table])], style=panel_style)

''' Experiments column '''
experiments_dropdown = dropdown(['fluorescence', 'slope'], 'experiments')
experiment_table = table({}, 'experiments')
experiments_col = html.Div([dbc.Col([html.H2('Experiments'), experiments_dropdown, experiment_table])], style=panel_style)
experiment_settings = html.Div([], id='experiment-settings', className = 'experiment-settings')

experiment_panel = dbc.Col([dbc.Row([ experiments_col, model_col, samplers_col], className='experiment-panel'), experiment_settings])


'''Task panel '''
task_panel = html.Div([html.H1('Tasks'), html.P('Tasks here')], className = 'task-panel')

''' Layout '''
body = html.Div([tree, experiment_panel, task_panel], className='container-body')

#app.layout = html.Div([body], style=body_style, className='body')
app.layout = body
    
def get_default_params(module, name):
    app.logger.warning('testing warning log')
    if name == 'None':
        return {}
    module_name = {'sampler': 'samplers', 'model': 'models',
                   'algorithm': 'optimizers', 'servo': 'servos'}[module]
    module = getattr(emergent, module_name)
    instance = getattr(module, name)()
    params = instance.params
    params_dict = {}
    for p in params:
        params_dict[p] = params[p].value

    return params_dict

@app.callback(dash.dependencies.Output('experiment-settings', 'children'),
              [dash.dependencies.Input('models-table', 'data'), dash.dependencies.Input('samplers-table', 'data')])
def update_all_params(data, sampler_data):
    params = {'model': {}, 'sampler': {}}
    for d in data:
        params['model'][d['Parameter']] = d['Value']
    for d in sampler_data:
        params['sampler'][d['Parameter']] = d['Value']
    return '{}'.format(params)

@app.callback(dash.dependencies.Output('samplers-container', 'children'),
              [dash.dependencies.Input('samplers-dropdown', 'value')])
def update_sampler_params(value):
    d = sampler_table.children
    return 'You have selected "{}"'.format(d)

@app.callback(dash.dependencies.Output('experiments-container', 'children'),
              [dash.dependencies.Input('experiments-dropdown', 'value')])
def update_experiment_params(value):
    return 'You have selected "{}"'.format(value)

@app.callback(dash.dependencies.Output('samplers-table', 'data'),
              [dash.dependencies.Input('samplers-dropdown', 'value')])
def update_sampler_table(value):
    print('Updating sampler table')
    d = get_default_params('sampler', value)
    data = []
    rows = []
    for key in d:
        rows.append(html.Tr([html.Td(key), html.Td(d[key])]))
        data.append({'Parameter': key, 'Value': d[key]})
    return data

@app.callback(dash.dependencies.Output('models-table', 'data'),
              [dash.dependencies.Input('models-dropdown', 'value')])
def update_model_table(value):
    d = get_default_params('model', value)
    rows = []
    data = []
    for key in d:
        rows.append(html.Tr([html.Td(key), html.Td(d[key])]))
        data.append({'Parameter': key, 'Value': d[key]})

#    return rows 
    return data
    
if __name__ == '__main__':
    app.run_server(debug=True, port=54031)
    print('started server')