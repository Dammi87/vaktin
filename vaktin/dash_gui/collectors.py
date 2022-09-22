import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State


class Borg:
    _shared_state = {}
    def __init__(self):
        self.__dict__ = self._shared_state


class DropDowns(Borg):
    known_dropdowns = {}
    known_dropdowns_other = {}
    known_vendor = {}
    vaktin = None

    @classmethod
    def set_vaktin(cls, vaktin):
        cls.vaktin = vaktin

    @classmethod
    def add_dropdown(cls, id_name, part, brand, component):
        if part not in cls.known_dropdowns:
            cls.known_dropdowns[part] = {}
        if brand not in cls.known_dropdowns:
            cls.known_dropdowns[part][brand] = []
        cls.known_dropdowns[part][brand].append(id_name)
        cls.known_dropdowns_other[id_name] = (part, brand, component)

    @classmethod
    def add_vendor_dropdown(cls, id_name, vendor_name):
        cls.known_vendor[id_name] = vendor_name

    @classmethod
    def create_callbacks(cls, app):
        inputs = []
        for name in cls.known_dropdowns_other:
            inputs.append(Input(name, "n_clicks"))

        for name in cls.known_vendor:
            inputs.append(Input(name, "n_clicks"))
        
        # Add link between save/load buttons
        inputs.append(Input('load-table', 'children'))

        @app.callback(
            Output("card-content", "children"),
            inputs
        )
        def tab_content(*args):
            ctx = dash.callback_context

            if all([arg is None for arg in args]) :
                # if neither button has been clicked, return "Not selected"
                return "Not selected"

            if ctx.triggered:
                # this gets the id of the button that triggered the callback
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]

                # Set
                if button_id != 'load-table':
                    if button_id in cls.known_vendor:
                        cls.vaktin.set_vendor(cls.known_vendor[button_id])
                    else:
                        cls.vaktin.set_selected_component(*cls.known_dropdowns_other[button_id])

            df = cls.vaktin.get_build()
            return dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
