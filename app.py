import dash
from views.dropdown_list_view import DropDownView
from views.timeseries_view import TimeSeriesView
from views.layouts.basic_layout import Layout
from configparser import ConfigParser
from core.file_locator import FileLoader
from envyaml import EnvYAML

RESOURCE_CONFIG = ConfigParser()
RESOURCE_CONFIG.read("config/resources.ini")
ENV_RESOLVER = EnvYAML('app.yaml')

def start_app_server():
    app = dash.Dash(__name__)
    app.layout = Layout().base_layout()
    DropDownView(app, RESOURCE_CONFIG).register_to_dash_app()
    TimeSeriesView(app, RESOURCE_CONFIG).register_to_dash_app()
    print("Starting Server ..")
    app.run_server(debug=True)

def download_dataset():
    print("Downloading dataset ......")
    FileLoader(ENV_RESOLVER, RESOURCE_CONFIG).download_from_aws()
    print("Download completed")

if __name__ == '__main__':
    download_dataset()
    start_app_server()