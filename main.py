import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime, timezone
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def fetch_weather_data():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 31.8715,
        "longitude": -116.6007,
        "hourly": ["apparent_temperature", "rain"],
        "timezone": "America/Los_Angeles",
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    hourly = response.Hourly()
    hourly_apparent_temperature = hourly.Variables(0).ValuesAsNumpy()
    hourly_rain = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )}

    hourly_data["apparent_temperature"] = hourly_apparent_temperature
    hourly_data["rain"] = hourly_rain

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    current_time = pd.Timestamp(datetime.now(timezone.utc))
    closest_hour = hourly_dataframe.iloc[(hourly_dataframe['date'] - current_time).abs().argsort()[:1]]
    
    return closest_hour

# Create the Dash app
app = dash.Dash(__name__)

# Layout of the dashboard
app.layout = html.Div(children=[
    html.H1(children='Dashboard del Clima', style={'color': 'white'}),

    html.Div(id='weather-data', children=[
        dcc.Graph(
            id='temp-graph',
            style={'display': 'inline-block', 'width': '48%'}
        ),
        dcc.Graph(
            id='rain-graph',
            style={'display': 'inline-block', 'width': '48%'}
        )
    ], style={'display': 'flex', 'justify-content': 'space-between'}),

    html.Div(children=[
        html.Button('Actualizar', id='update-button', n_clicks=0, style={
            'fontSize': '24px',  # Triple the font size
            'padding': '20px 40px',  # Increase padding
            'backgroundColor': '#4CAF50',  # Initial background color
            'color': 'white',  # Text color
            'border': 'none',
            'cursor': 'pointer',
            'transition': 'background-color 0.3s'  # Smooth transition for background color
        })
    ], style={'display': 'flex', 'justify-content': 'center', 'marginTop': '20px'}),

    dcc.Interval(
        id='interval-component',
        interval=1*60*1000,  # in milliseconds (1 minute)
        n_intervals=0
    )
], style={'backgroundColor': 'black', 'padding': '20px'})

# Add CSS for hover effect
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            #update-button:hover {
                background-color: #45a049;  # Change background color on hover
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

@app.callback(
    [Output('temp-graph', 'figure'),
     Output('rain-graph', 'figure')],
    [Input('update-button', 'n_clicks'),
     Input('interval-component', 'n_intervals')]
)
def update_graphs(n_clicks, n_intervals):
    closest_hour = fetch_weather_data()
    temp_fig = go.Figure(go.Indicator(
        mode="number",
        value=closest_hour['apparent_temperature'].values[0],
        title="🌡️ Temperatura Aparente",
        number={"font": {"size": 80, "color": "purple"}}
    ))
    rain_fig = go.Figure(go.Indicator(
        mode="number",
        value=closest_hour['rain'].values[0],
        title="🌧️ Lluvia",
        number={"font": {"size": 80, "color": "blue"}}
    ))
    return temp_fig, rain_fig

if __name__ == '__main__':
    app.run_server(debug=True)