import dash
from views.dropdown_list_view import DropDownView
from views.timeseries_view import TimeSeriesView
from views.layouts.basic_layout import Layout

from core.file_locator import download_from_aws

download_from_aws()

app = dash.Dash(__name__)
app.layout = Layout().base_layout()

DropDownView(app).register_to_dash_app()
TimeSeriesView(app).register_to_dash_app()

if __name__ == '__main__':

    app.run_server(debug=True)
