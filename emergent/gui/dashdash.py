import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

def dropdown(items):
    options = []
    for item in items:
        options.append({'label': item, 'value': item})
    
    return dcc.Dropdown(
        options=options
        )


def table(d):
    rows = []
    for key in list(d.keys()):
        r = html.Tr([html.Td(key), html.Td(d[key])])
        rows.append(r)
    return dbc.Table(html.Table(rows), bordered=True, dark=True, hover=True, responsive=True, striped=True)
            

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], static_folder = 'media')

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

''' Network tree '''
tree = dbc.Card(dbc.CardBody([dbc.CardTitle("Network"), html.Div([html.P('Network')], style=network_style)]), style={'opacity': 0.9})

''' Models column '''
models_dropdown = dropdown(['gaussian', 'nonlinear'])
model_params = {'amplitude': 1.0}
model_col = html.Div([dbc.Col([html.P('Models'), models_dropdown, table(model_params)])], style=panel_style)

''' Samplers column '''
samplers_dropdown = dropdown(['grid', 'online'])
sampler_params = {'leash': 0.25, 'batch size': 10, 'iterations': 10, 'presampled': 15}
samplers_col = html.Div([dbc.Col([html.P('Samplers'), samplers_dropdown, table(sampler_params)])], style=panel_style)


''' Experiments column '''
experiments_dropdown = dropdown(['fluorescence', 'slope'])
experiment_params = {'delay': 1, 'cycles_per_sample': 2}
experiments_col = html.Div([dbc.Col([html.P('Experiments'), experiments_dropdown, table(experiment_params)])], style=panel_style)


body_style = {#'background-image': 'url(https://upload.wikimedia.org/wikipedia/commons/2/22/North_Star_-_invitation_background.png)',
              'background-image': 'url(./media/background.jpg)',
              'background-size': 'cover',
#              'background-color': 'red !important',
              'margin': 0, 
              'padding': 0,
              'min-height': '100%',
              'height': 'auto !important',
              'min-width': '100%',
              'position': 'absolute'}
body = dbc.Container([dbc.Row([tree, dbc.Row([ experiments_col, model_col, samplers_col])])])
app.layout = html.Div([body], style=body_style)

    

if __name__ == '__main__':
    app.run_server(debug=True, port=54031)