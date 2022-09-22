import dash
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
from ..handlers import Vaktin
from .collectors import DropDowns
import flask
import io
import json
import base64
from flask.helpers import send_file
from flask import Flask


def menu(vaktin, drop_down):
    [drop_down.add_vendor_dropdown(vendor, vendor) for vendor in vaktin.get_vendors()]
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dcc.Upload(html.Button('Upload Build', id='load_build', className='btn btn-primary'), id='upload_build')),
            dbc.NavItem(html.A('Save Build', className='btn btn-primary', id='save_build_href', href='/save_build')),
            dbc.DropdownMenu(
                children=[dbc.DropdownMenuItem(vendor, id=vendor) for vendor in vaktin.get_vendors()],
                nav=True,
                in_navbar=True,
                label="Vendors",
            ),
        ],
        brand="Build-A-PC",
        brand_href="#",
        color="primary",
        dark=True,
    )

def create_dropdown(drop_down, items, part, brand):
    menu_items = []
    for item in items:
        id_name = '{}_{}_dd'.format(item, brand)
        id_name = id_name.replace('.', '')
        menu_items.append(dbc.DropdownMenuItem(item, id=id_name))
        drop_down.add_dropdown(id_name, part, brand, item)

    return dbc.DropdownMenu(
        label=brand,
        children=menu_items
    )


def create_tab_content(vaktin, drop_down, part):
    brands = vaktin.get_brands(part)
    drop_downs = []
    for brand in brands:
        drop_downs.append(
            dbc.Col(
                create_dropdown(drop_down, vaktin.get_components(part, brand), part, brand),
                width={"offset": 0}
            )
        )

    return dbc.CardBody(dbc.Row(drop_downs))


def get_tab_name(name):
    return '{}_tab'.format(name)


def create_part_tabs(vaktin, drop_down):
    tabs = []
    part_list = vaktin.get_parts()
    for part in part_list:
        tabs.append(dbc.Tab(create_tab_content(vaktin, drop_down, part), label=part, tab_id=get_tab_name(part)),)

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Tabs(
                    tabs,
                    id="card-tabs",
                    card=True,
                    active_tab=get_tab_name(part_list[0]),
                )
            ),
            dbc.CardBody(html.P(id="card-content", className="card-text")),
        ]
    )


# Save build callback
def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'json' in filename:
            # Assume that the user uploaded a CSV file
            return json.loads(decoded)
        else :
            return html.Div([
                'There was an error processing this file. Is it json?'
            ])
    except Exception as e:
        return html.Div([
            'There was an error processing this file.'
        ])

def run():
    vaktin = Vaktin()
    drop_down = DropDowns()
    drop_down.set_vaktin(vaktin)


    server = Flask(__name__)
    app = dash.Dash(
        external_stylesheets=[dbc.themes.CYBORG],
        # these meta_tags ensure content is scaled correctly on different devices
        # see: https://www.w3schools.com/css/css_rwd_viewport.asp for more
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ],
        server=server
    )
    app.layout = html.Div([menu(vaktin, drop_down), create_part_tabs(vaktin, drop_down), html.P(id='load-table', hidden=True)])

    # Activate dropdown callbacks
    drop_down.create_callbacks(app)

    @app.callback(
        Output('load-table', 'children'),
        [Input('upload_build', 'contents')],
        [State('upload_build', 'filename'),
        State('upload_build', 'last_modified')])
    def load_build(list_of_contents, list_of_names, list_of_dates):
        if list_of_contents is not None:
            out = parse_contents(list_of_contents, list_of_names, list_of_dates) 
            if 'vendor' not in out:
                return html.Div(['There was an error processing this file.'])
            else:
                vendor = out.pop('vendor')
                vaktin.set_vendor(vendor)
                for part in out:
                    brand, component = out[part]
                    vaktin.set_selected_component(part, brand, component)

        return 'Hello'

    @app.server.route('/save_build', methods=['GET']) 
    def download_csv():
        setting = {
            'vendor': vaktin.get_vendor()
        }
        for part in vaktin.get_parts():
            setting[part] = vaktin.get_selected_component(part)

        str_io = io.StringIO()
        str_io.write(json.dumps(setting))
        mem = io.BytesIO()
        mem.write(str_io.getvalue().encode('utf-8'))
        mem.seek(0)
        str_io.close()

        return send_file(mem, attachment_filename='mybuild.json', as_attachment=True)

    app.run_server(host="0.0.0.0", port=8000, debug=False)
