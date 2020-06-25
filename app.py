import dash
from views.dropdown_list_view import DropDownView
from views.timeseries_view import TimeSeriesView
from views.layouts.basic_layout import Layout
from configparser import ConfigParser
from datasync.file_locator import FileLoader
import os

RESOURCE_CONFIG = ConfigParser()
RESOURCE_CONFIG.read("config/resources.ini")
ENV_RESOLVER = {
    "BUCKET_NAME": os.environ["BUCKET_NAME"],
    "ACCESS_KEY": os.environ["ACCESS_KEY"],
    "SECRET_KEY": os.environ["SECRET_KEY"],
    "OPTIMIZER_ACCESS_KEY": os.environ["OPTIMIZER_ACCESS_KEY"],
    "OPTIMIZER_SECRET_KEY": os.environ["OPTIMIZER_SECRET_KEY"],
    "OPTIMIZER_BUCKET_NAME": os.environ["OPTIMIZER_BUCKET_NAME"]
}

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