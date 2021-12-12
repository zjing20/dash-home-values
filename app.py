#!/usr/bin/env python
# coding: utf-8

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import dcc
from dash import html
import plotly.express as px
import plotly.figure_factory as ff
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

import numpy as np
import pandas as pd

from whitenoise import WhiteNoise

import warnings
warnings.filterwarnings("ignore")

# read data
df = pd.read_csv('County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv')
df = df.rename({'RegionName':'County'},axis=1)
df['County'] = df['County'] + ' (' + df['State'] + ')'
df['Annualized YTD % Growth'] = ((df['2021-10-31']/df['2020-12-31'])**(12/10) - 1)*100
df['Annualized 3yr % Growth'] = ((df['2021-10-31']/df['2018-10-31'])**(12/36) - 1)*100
df['Annualized 10yr % Growth'] = ((df['2021-10-31']/df['2011-10-31'])**(12/120) - 1)*100
# df.head()


# prep data for time series
df_ts = pd.melt(df, id_vars=['RegionID','County','State','Metro'], value_vars=df.columns[9:-1])
df_ts.columns = ['RegionID','County','State','Metro','Date','Home Value']
all_states = sorted(df_ts['State'].unique())

# prep data for growth
df_growth = pd.melt(df, id_vars=['County','State'], value_vars=['Annualized YTD % Growth','Annualized 3yr % Growth','Annualized 10yr % Growth'])
df_growth.columns = ['County','State','Type','Annualized % Growth']

# prep data for state of 100 most expensive counties
df_100_2021_10_31 = df[['County','State','2021-10-31']]
df_100_2021_10_31 = df_100_2021_10_31.sort_values(by='2021-10-31', ascending=False)[:100].groupby('State').count().reset_index()[['State','County']]
df_100_2018_10_31 = df[['County','State','2018-10-31']]
df_100_2018_10_31 = df_100_2018_10_31.sort_values(by='2018-10-31', ascending=False)[:100].groupby('State').count().reset_index()[['State','County']]
df_100_2011_10_31 = df[['County','State','2011-10-31']]
df_100_2011_10_31 = df_100_2011_10_31.sort_values(by='2011-10-31', ascending=False)[:100].groupby('State').count().reset_index()[['State','County']]

current_100 = px.pie(df_100_2021_10_31, values='County', names='State', title='2021-10-31')
current_100.update_layout(title_x=0.5)
three_yr_100 = px.pie(df_100_2018_10_31, values='County', names='State', title='2018-10-31')
three_yr_100.update_layout(title_x=0.5)
ten_yr_100 = px.pie(df_100_2011_10_31, values='County', names='State', title='2011-10-31')
ten_yr_100.update_layout(title_x=0.5)

# put data on map
df['StateCodeFIPS_2d'] = df['StateCodeFIPS'].apply(lambda x: "0"+str(x) if len(str(x)) == 1 else str(x))
df['MunicipalCodeFIPS_3d'] = df['MunicipalCodeFIPS'].apply(lambda x: "00"+str(x) if len(str(x)) == 1 else ("0"+str(x) if len(str(x))==2 else str(x)))
df['FIPS'] = df['StateCodeFIPS_2d'] + df['MunicipalCodeFIPS_3d']
df_map = df[df.columns[-1:].append(df.columns[9:-6])]
df_map = pd.melt(df_map, id_vars=['FIPS'], value_vars=df_map.columns[1:])
df_map.columns = ['FIPS','Date','Home Value']

all_dates = sorted(df_map['Date'].unique(),reverse=True)

app = dash.Dash(__name__,external_stylesheets = [dbc.themes.BOOTSTRAP])
server = app.server
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/')

app.layout = html.Div(
    dbc.Container([
        html.H1('United States County Home Values', className="display-3"),

        html.P(
                "This dashboard demostrates how home values of various counties change from time to time. It also shows states with the most expensive counties, and compares county home values across the map.",
                className="lead",
        ),
        
        
        html.Hr(className="my-2"),
        
        dbc.Alert([
            
            html.P(
                    "Home types include single family and condo/co-op. Data retrived from Zillow Home Value Index (ZHVI). ZHVI is a smoothed, seasonally adjusted measure of the typical home value and market changes across a given region and housing type. It reflects the typical value for homes in the 35th to 65th percentile range.",
                ),

            html.P(
                    "Data as of 2021/10/31"
                ),

            html.P(
                    "Data Source: https://www.zillow.com/research/data/"
                )
            ], 
            color="dark"
        ),
        
        dbc.Container([
            html.H2('County Home Values from 2000 to 2021', style={"fontSize": 18}),
            html.Hr(className="my-2"),
            html.Div([
                html.Label("Choose State: "),
                dcc.Dropdown(
                    id="dropdown_ts",
                    options=[{"label": x, "value": x} 
                             for x in all_states],
                    value=['AK'],
                    multi=True)
                ],
            ),
            html.Br(),
            html.Div(dcc.Graph(id="ts")),
            ],
            className="p-3 bg-white rounded-3"
        ),
        
        html.Br(),
        
        dbc.Container([
            html.H2('County Home Value Annualized % Growth', style={"fontSize": 18}),
            html.Hr(className="my-2"),
            html.Div([
                html.Label("Choose State: "),
                dcc.Dropdown(
                    id="dropdown_growth",
                    options=[{"label": x, "value": x} 
                             for x in all_states],
                    value=['AK'],
                    multi=True)
                ],
            ),
            html.Br(),
            html.Div(dcc.Graph(id="growth")),
            ],
            className="p-3 bg-white rounded-3"
        ),
        
        html.Br(),
        
        dbc.Container([
            html.H2('States with The Most Expensive 100 Counties', style={"fontSize": 18}),
            html.Hr(className="my-2"),
            html.Div(
                dbc.Row([
                dbc.Col(dcc.Graph(id="current_100",figure=current_100)),
                dbc.Col(dcc.Graph(id="three_yr_100",figure=three_yr_100)),
                dbc.Col(dcc.Graph(id="ten_yr_100",figure=ten_yr_100))
                ])
            ),
            ],
            className="p-3 bg-white rounded-3"
        ),
        
        html.Br(),
        
        dbc.Container([
            html.H2('County Home Values (*This takes some time to run.)', style={"fontSize": 18}),
            html.Hr(className="my-2"),
            html.Div([
                html.Label("Choose Date: "),
                dcc.Dropdown(
                    id="dropdown_map",
                    options=[{"label": x, "value": x} 
                              for x in all_dates[:2]],
                    value='2021-10-31',
                    multi=False)
                ],
            ),
            html.Br(),
            dbc.Row(
                dbc.Col(
                    dcc.Graph(id="map"),
                    width={"size": 8, "offset": 2}
                )
            ),
            ],
            className="p-3 bg-white rounded-3"
        ),
        
    ], 
    className="py-3"
    ),
    className="p-3 bg-light rounded-3"
)

@app.callback(
    Output("ts", "figure"), 
    [Input("dropdown_ts", "value")])
def update_line_chart(states):
    mask = df_ts['State'].isin(states)
    fig = px.line(df_ts[mask], 
        x="Date", y="Home Value", color='County')
    return fig

@app.callback(
    Output("growth", "figure"), 
    [Input("dropdown_growth", "value")])
def update_growth_chart(states):
    mask = df_growth['State'].isin(states)
    fig = px.bar(df_growth[mask], 
        x="County", y="Annualized % Growth", color='Type', barmode='group', template='plotly_dark')
    fig.update_layout(xaxis={'categoryorder':'total descending'})
    return fig

@app.callback(
    Output("map", "figure"), 
    Input("dropdown_map", "value"))
def update_map(date):
    mask = df_map['Date'] == date
    fig = ff.create_choropleth(df_map[mask]['FIPS'].to_list(), df_map[mask]['Home Value'].to_list(),
                               binning_endpoints = list(np.linspace(0,500000,11,dtype=int)),
                               centroid_marker={'opacity': 0},
                               asp=2.9, title='United States County Home Values',
                               legend_title='Home Value'
                               )
    fig.layout.template = None
    # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

if __name__ == '__main__':
    app.run_server()


