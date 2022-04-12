from time import strftime
import json
from urllib.request import urlopen
from urllib.error import HTTPError
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def check_df_quality(df: pd.DataFrame):
    '''
    verify data populated correctly and give a glance at datatypes
    upon dataframe load.
    '''
    print('Checking dataframe integrity:')
    if df.size > 0:
        print(f'DataFrame shape:{df.shape}')
        print(f'DataFrame dtypes:\n{df.dtypes}\n')
    else:
        print('DataFrame loaded but does not contain information. Check source.')


def LOAD_DATA(url: str) -> pd.DataFrame:
    '''load covid case data from a public url
    Paramters
    ---
    path: str, specified url to read data from

    returns:
    ---
    df: pd.DataFrame
    '''
    print(f'Loading data from  {url}...\n')
    try:
        df = pd.read_csv(url)
        assert df.size > 0
        check_df_quality(df)
        print('Data loaded.')
    except IOError as err:
        print(f'{url} is not valid. Check link and try again.\n', err)
    return df


RAW_DATA_URL = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/live/us-counties.csv'
daily_case_df = LOAD_DATA(RAW_DATA_URL)


def preprocess(df):
    '''
    All preprocessing is done here. There are only a handful 
    of operations done in this pipeline, mostly around explicit type casting
    and data cleaning.

    Returns: pd.DataFrame, the inputted df as a cleaned, preprocessed DataFrame
    '''
    # remove samples where county and fips data are missing
    df = df.loc[(pd.notna(df['fips'])) & (df['county']!='Unknown')].copy()

    # set missing values to 0 for specific discete-valued columns
    fill_cols = ['cases', 'deaths', 'confirmed_cases', 'confirmed_deaths', 'probable_cases', 'probable_deaths']
    df[fill_cols] = df[fill_cols].fillna(value=0)

    # remove decimals in fips field before casting to string
    df = df.astype({'fips': 'int64'})

    df = df.astype({'date': 'datetime64[ns]',
                    'fips': 'string',
                    'county': 'string',
                    'cases': 'int32',
                    'deaths': 'int32',
                    'confirmed_cases': 'int32',
                    'confirmed_deaths': 'int32',
                    'probable_cases': 'int32',
                    'probable_deaths': 'int32'})
    
    # front-pad fips to conform to naming convention
    df['fips'] = df['fips'].str.pad(width=5, side='left', fillchar='0')
    return df


def load_county_data(path: str, sep: str=';'):
    '''
    load and process a local .csv file containing
    county code and fips code information from a public
    database. 
    '''
    data = pd.read_csv(path, sep=sep)
    
    assert 'GEOID' in data, 'GEOID not in county data'
    data = data.rename(columns={'GEOID': 'fips'})
    data['fips'] = data['fips'].astype('string').str.pad(width=5, side='left', fillchar='0')
    return data


daily_case_df = preprocess(daily_case_df)

us_county_data = load_county_data('./us_county_data_reduced.csv', sep=';')

# merge lat-long coords using fips field from us_county_data (for mapping purposes)
daily_case_df = daily_case_df.merge(us_county_data, on='fips', how='left', indicator=True)

daily_case_df = daily_case_df.astype({'INTPTLAT': 'float64','INTPTLON': 'float64'})

## init plots
target = 'confirmed_cases' # could integrate dynamic switching with Dash
limits = [(0, 10e2), (10e2+1, 10e3), (10e3+1, 10e4), (10e4+1, 10e5), (10e5+1, 10e8)]
colors = ["#BCC8FF", "#86D8FF", "#FFDC75", "#FFA76F", "#FF686F", '#FF344E']

scale = 6

bubble_fig = go.Figure()

for i, val in enumerate(limits):
    df_bin = daily_case_df.loc[(daily_case_df[target] > val[0]) &
                               (daily_case_df[target] < val[1])]
    bubble_fig.add_trace(go.Scattergeo(
        locationmode='USA-states',
        lon=df_bin['INTPTLON'],
        lat=df_bin['INTPTLAT'],
        text=df_bin['county'] + ' County, ' + df_bin['state'] + '<br>' +
        (df_bin[target]/10e5).astype('string') + 'M total confirmed cases',
        marker=dict(
            size=np.sqrt(df_bin[target])/scale,
            color=colors[i],
            line_color='rgba(40,40,40, 0.5)',
            line_width=0.3,
            sizemode='area'),
            name=f'{int(val[0])} - {int(val[1])}'))

bubble_fig.update_layout(
    title_text='Total US COVID-19 confirmed cases (Click legend elements to toggle traces)',
    showlegend=True,
    legend_title_text='Total cases',
    geo=dict(scope='usa', landcolor='rgb(230, 230, 240)'),
    height=400)

## Create a custom theme dict to switch easier
# themes: https://plotly.com/python/reference/layout/mapbox/#layout-mapbox-style
theme = 'light'

if theme == 'dark':
    styles = {'mapbox-style': 'carto-darkmatter',
            'colorscale': 'Electric',
            'primary-color': '#1c1c1c',
            'text-color': '#eeeeee',
            'button-color': '#303030'
            }
else:
    styles = {'mapbox-style': 'carto-positron',
            'colorscale': 'dense',
            'primary-color': '#ffffff',
            'text-color': '#000000',
            'button-color': '#fafafa'
            }

## bottom left choropleth
# LOAD FIPS MAP DATA
FIPS_JSON_URL = 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json'
try:
    with urlopen(FIPS_JSON_URL) as response:
        counties = json.load(response)
except HTTPError as err:
    print('Issue loading countyJSON file: ', err)

choropleth = go.Figure(go.Choroplethmapbox(geojson=counties, 
                locations=daily_case_df['fips'],
                z=daily_case_df[target], 
                zmin=0, 
                zmax=daily_case_df[target].max()*0.05,
                colorbar_title='Total cases', 
                colorscale=styles['colorscale'],
                marker_line_width=0.25,
                marker_opacity=0.8))

choropleth.update_layout(title=strftime('Total US COVID-19 confirmed cases (as choropleth, count as of %m/%d/%Y)'),
                mapbox_style=styles['mapbox-style'],
                geo_scope='usa',
                mapbox_zoom=1.5,
                mapbox_center={"lat": 37.0902, "lon": -95.7129},
                margin= {'t': 80, 'r': 0, 'b':0, 'l':0},
                height=400)

# bar chart
first_n = 10
top_conf_cases_by_county = daily_case_df.groupby('county')[target].sum().sort_values(ascending=False)[:first_n]

cases_bar = go.Figure(go.Bar(x=top_conf_cases_by_county.index, y=top_conf_cases_by_county.to_numpy()))
cases_bar.update_layout(title=f'Top {first_n} US counties by total confirmed cases', height=800)

# create layout
app = dash.Dash()
app.layout = html.Div(style={'backgroundColor': styles['primary-color'], 
                    'color': styles['text-color'], 
                    'margin': 0, 
                    'padding': 0, 
                    'fontFamily': 'SF Pro Display',
                    'height': '95%'}, children=[
    html.Div(children=[
        html.H1('COVID-19 Case Visualization - Jacob Gomez Rubio',
            style={
                'backgroundColor': styles['primary-color'],
                'margin': 10,
                'padding': 10,
                'fontFamily': 'SF Pro Text'
            }
        )
    ]),
    html.Div(style={'display': 'flex', 
                    'flex-direction': 'row',
                    'margin': 0}, children=[
        html.Div(style={'display': 'flex',
                        'flex-direction': 'column',
                        'align-items': 'center',
                        'justify-content': 'center',
                        'width': '60%',
                        'margin': 0}, children=[
            html.Div(style={'width': '90%'}, children=[
                dcc.Graph(id='bubblemap', figure=bubble_fig),
            ]),
            html.Div(style={'width': '90%'}, children=[
                dcc.Graph(id='choromap', figure=choropleth),
            ])
        ]),
        html.Div(children=[
            html.Div(children=[
                dcc.Graph(id='cases-bar', figure=cases_bar),
            ])
        ])
    ])
])


if __name__ == '__main__':
    app.run_server(debug=True)
