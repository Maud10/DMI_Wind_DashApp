# Import packages
import requests
import json
import pandas as pd
import datetime as dt
import plotly.graph_objects as go
from plotly.colors import n_colors
import numpy as np
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import dcc, html
from datetime import date
from plotly.subplots import make_subplots

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SUPERHERO])

# Set up colors
dict_layout_cols = {
    'primary': 'rgb(76,155,232)',
    'green': 'rgb(92,184,92)',
    'yellow': 'rgb(255,193,7)',
    'red': 'rgb(217,83,79)',
    'bg_blue': 'rgb(56, 97, 141)',
    'white': 'rgb(255, 255,255)',
    'bg_blue2': 'rgb(15,37,55)',
    'orange': 'rgb(246,105,35)',
    'transparent': 'rgba(255,255,255,0)'
}
# region FUNCTION FOR TRANSPARENT COLORS

def fun_col_to_trans(col, transparency):
    # Convert transparency to string
    t_trans = str(transparency)

    # Split text and insert transparency
    col_out = col.split(')')[0] + ',' + t_trans + ')'
    # Change color type to include transparency
    col_out = col_out.replace('rgb', 'rgba')

    return col_out


#endregion



# region Grid Map
"""
SET UP GRID MAP
"""

## READ GEOGPRAPHICAL DATA
# Set url to geojson
url = 'https://raw.githubusercontent.com/MartinJHallberg/DMI_Wind_DashApp/main/assets/DKN_10KM_epsg4326_filtered_wCent.geojson'
geoj_grid = json.loads(requests.get(url).text)


shp_grid = pd.json_normalize(geoj_grid['features'])

print(shp_grid.columns)
shp_grid.rename(columns={'properties.KN10kmDK': 'KN10kmDK',
                         'properties.Stednavn': 'Stednavn',
                         'properties.cent_lon': 'cent_lon',
                         'properties.cent_lat': 'cent_lat'}, inplace=True)

# Rename None to 'No name'
shp_grid['Stednavn'].fillna('No name', inplace=True)

## SET UP FIGURE
# Map center
dict_cent = {'lon': 13,
             'lat': 55.86
             }

# Color columns
shp_grid['Val'] = 1
shp_grid['Col'] = fun_col_to_trans(dict_layout_cols['primary'], 0.4)

# Hover columns
hover_data_map = np.stack(
    (shp_grid['Stednavn'],
     shp_grid['cent_lon'],
     shp_grid['cent_lat']), axis=1)

# Figure
fig_map = go.Figure(
    go.Choroplethmapbox(
        geojson=geoj_grid,
        featureidkey="properties.KN10kmDK",
        locations=shp_grid['KN10kmDK'],
        z=shp_grid['Val'],
        colorscale=shp_grid['Col'],
        showscale=False,
        customdata=hover_data_map,
        hovertemplate='%{customdata[0]}<extra></extra>',
        colorbar={'outlinecolor': dict_layout_cols['primary']}
    ),
    layout=go.Layout(
        mapbox=dict(
            accesstoken='pk.eyJ1IjoibWFqaGFsIiwiYSI6ImNrd3F3MmgyYTBxc3oydWxja3ZwNnB1enIifQ.XQ6h4h4UsdD_9y2WsOUbcw',
            center=dict_cent,
            zoom=7,
            style="dark"
        ),
        autosize=True,
        # width=1000,
        height=700,
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        clickmode='event+select'
    )
)

# Update layout
# fig_map.update_layout(
#     mapbox_style = "white-bg", #Decide a style for the map
#     mapbox_zoom = 7, #Zoom in scale
#     mapbox_center = dict_cent)

fig_map.update_traces(marker_line_width=0.3)

# fig_map.show()
# endregion


# region Wind Rose
"""
SET UP WIND ROSE
"""

## CREATE DIRECTIONS DATA FRAME
# Create bins
# Create bins
bins = np.arange(start=0, stop=360, step=22.5)
# Create list of directions
dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']

# Create data frame
df_wind_dir_col = pd.DataFrame({'Direction': dirs,
                                'Degree': bins,
                                'Radius': np.repeat(100, len(dirs))
                                }
                               )
# Calculate coordinates for angles
df_wind_dir_col['Y_cord'] = -round(np.cos(np.deg2rad(df_wind_dir_col['Degree'])), 2) * 12
df_wind_dir_col['X_cord'] = round(np.sin(np.deg2rad(df_wind_dir_col['Degree'])), 2) * 12
dict_dir_coord = df_wind_dir_col[['Direction', 'X_cord', 'Y_cord']].set_index('Direction').to_dict('index')


## CREATE FUNCTION TO CONVERT DEGREES TO CARDINAL DIRECTIONS
def fun_DegToCard(d):
    card = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = round(d / (360. / len(card)))
    card_text = card[ix % len(card)]
    return card_text



## DEFINE COLOR PALETTE
blues = n_colors('rgb(39, 18, 228)', 'rgb(68, 196, 228)', n_colors=4, colortype='rgb')
greens = n_colors('rgb(6, 121, 37)', 'rgb(129, 233, 49)', n_colors=4, colortype='rgb')
yellow = n_colors('rgb(218, 233, 10)', 'rgb(233, 166, 10)', n_colors=4, colortype='rgb')
reds = n_colors('rba(246, 105, 35)', 'rba(179, 0, 0)', n_colors=4, colortype='rgb')

#blues[0] = 'rgba(39.0, 18.0, 228.0,0.6)'

# Append colors
cols = blues + greens + yellow + reds

cols_trans = []

for col in cols:
    cols_trans.append(fun_col_to_trans(col, 0.8))

# Create dict with directions and colors
col_pal = dict(zip(dirs, cols))
col_pal_trans = dict(zip(dirs, cols_trans))

## SET UP FIGURE
# Create column with color for directions
cols_wind = df_wind_dir_col['Direction'].map(col_pal)
cols_wind_trans = df_wind_dir_col['Direction'].map(col_pal_trans)

# Add hover data
hover_data_windrose = np.stack(
    (df_wind_dir_col['Direction'], df_wind_dir_col['Degree']),
    axis=1)

# Set up figure
fig_windrose = go.Figure(
    go.Barpolar(
        r=df_wind_dir_col['Radius'],
        theta0=0,
        dtheta=22.5,
        marker=dict(color=cols_wind_trans),
        customdata=hover_data_windrose,
        # ids = df_wind_dir_col['Direction']
        hovertemplate='%{customdata[0]}<extra></extra>'
    ),
    layout=go.Layout(
        autosize=True,
        height=80,
        # width = 200,
        margin=dict(l=10, r=10, t=0, b=15),
        paper_bgcolor='rgba(255,255,255,0)',
        font_size=16,
        legend_font_size=16,
        polar_bgcolor='rgba(255,255,255,0)',
        polar_angularaxis_gridcolor='rgba(255,255,255,0)',
        polar_angularaxis_linecolor='rgba(255,255,255,0)',
        polar_radialaxis_gridcolor='rgba(255,255,255,0)',
        # hoverlabel=dict(bgcolor='rgba(255,255,255,0.1)',
        #                                font=dict(color='black')),
        polar_angularaxis_direction='clockwise',
        polar_angularaxis_rotation=90,
        polar_angularaxis_showticklabels=False,
        polar_radialaxis_showticklabels=False,
        polar_radialaxis_showline=False,
        # title={
        #     'text': 'Wind direction',
        #     'y': 0.95,
        #     'x': 0.5,
        #     'xanchor': 'center',
        #     'font': {'color': dict_layout_cols['white'],
        #              'size': 16
        #              }
        # }

    )
)

# fig_windrose.show()
# endregion


# App layout
app.layout = html.Div([

    dcc.Graph(id='map_figure', figure=fig_map,
              config={
                  'displayModeBar': False},
              style={'width': '100%',
                     'height': '100'}),

    html.Br(),

    # Date-picker div
    html.Div(
        [
            dcc.DatePickerSingle(
                id='date_picker',
                min_date_allowed=date(2019, 1, 1),
                max_date_allowed=date.today(),
                date=date.today() - dt.timedelta(days=1),
                display_format='YYYY-MM-DD'
            ),
        ],
        style={'top': '10px',
               'left': '10px',
               'position': 'absolute'}
    ),


    # About/figure div
    html.Div([

        html.Div([
            dbc.Button('About',
                       id='modal-button',
                       n_clicks=0, ),
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle('DMIWindApp')),
                    dbc.ModalBody([
                        html.Div([
                            html.Div(
                            'Data is collected from DMI Rest API:'
                            ),
                            html.A('DMI', href='https://confluence.govcloud.dk/display/FDAPI',
                                    target='_blank',
                                    style={'color': 'white'}),
                            html.Br(),
                            html.Br(),
                            html.Div('Source code can be found on GitHub:'),
                            html.A('GitHub', href='https://github.com/martinjhallberg/DMI_Wind_DashApp',
                                   target='_blank',
                                   style={'color': 'white'}),
                            html.Br(),
                            html.Br(),
                            html.Div('Life advice can be sent to'),
                            html.Div('martinjhallberg@gmail.com')

                            # dbc.ModalBody('Source code')

                    ])

                    ]
                    ),

                ],
                id='modal',
                is_open=False,
            ),
        ],
            style={'width': '85%'}),

        html.Div([
            html.A(
                html.Img(src=app.get_asset_url('dash-new-logo.png'),
                         style={'height': '40px'}),
                href="https://plotly.com/dash/",
                style={'width': '20%'}
            ),
        ]),
    ],
        style={'position': 'absolute',
               'width': '300px',
               'display': 'flex',
               'bottom': '28px',
               'right': '61%',
               "padding": "1rem 1rem",
               'backgroundColor': fun_col_to_trans(dict_layout_cols['primary'], 0.3),
               }
    ),


    # Side panel
    html.Div(
        [

            dcc.Loading(
                id='loading-1',
                type='default',
                color=dict_layout_cols['orange'],
                children=[

                    html.Br(),
                    html.H3(
                        id='area_headline',
                        style={'color': dict_layout_cols['white'],
                               'textAlign': 'center'}),

                    # html.Div([
                    #     dcc.Graph(
                    #         id='wing_rose', figure=fig_windrose,
                    #         config={
                    #             'displayModeBar': False}
                    #     )
                    # ],
                    #     style={'position': 'absolute',
                    #            'top': '15px',
                    #            'left': '-290px'},
                    # ),

                    #html.Br(),



                    # Backcast panel
                    html.Div(
                        [


                            dcc.Graph(
                                id='bar_chart', figure={},
                                config={
                                    'displayModeBar': False},
                                style={'height': '230px',
                                       'width': '95%',
                                       "display": "block",
                                       "margin-left": "auto",
                                       "margin-right": "auto",
                                       },
                            )
                            # ]),
                        ]
                        , style={'height': '300px',
                                 'width': '94%',
                                 "display": "flex",
                                 "margin-left": "auto",
                                 "margin-right": "auto",
                                 'backgroundColor': fun_col_to_trans(dict_layout_cols['bg_blue2'],0.5),
                                 }
                    ),


                    #Compare buttons
                    html.Div([

                        dbc.Button(
                            'Previous condition',
                            id = 'prev-button',
                            color = 'primary',
                            n_clicks= 0
                        ),
                        # Backcast panel
                        dbc.Collapse(
                            html.Div([

                                dcc.DatePickerSingle(
                                    id='date_picker_prev',
                                    min_date_allowed=date(2019, 1, 1),
                                    max_date_allowed=date.today(),
                                    date=date.today() - dt.timedelta(days=1),
                                    display_format='YYYY-MM-DD'
                                ),

                                dcc.Graph(
                                    id='bar_chart_2', figure={},
                                    config={
                                        'displayModeBar': False},
                                    style={'height': '200px',
                                           'width': '95%',
                                           "display": "block",
                                           "margin-left": "auto",
                                           "margin-right": "auto",
                                           },
                                ),

                            ]),

                            id='prev-collapse',
                            is_open= False,
                        ),


                    ],
                        style={'height': '60%',
                               'width': '94%',
                               "display": "block",
                               "margin-left": "auto",
                               "margin-right": "auto",
                               }
                    ),

                    # # Forecast panel
                    # html.Div([
                    #
                    #     html.Div([
                    #         #dcc.Loading(
                    #         #    id='loading-2',
                    #         #    type='default',
                    #         #    children=[
                    #                 dcc.Graph(
                    #                     id='bar_chart_3', figure={},
                    #                     config={
                    #                         'displayModeBar': False},
                    #                     style={'height': '200px',
                    #                            'width': '95%',
                    #                            "display": "block",
                    #                            "margin-left": "auto",
                    #                            "margin-right": "auto",
                    #                            },
                    #                 )
                    #           # ]),
                    #     ], style={'height': '50%',
                    #               'width': '100%',
                    #               'right': '0px',
                    #               'top': '0px',
                    #               #'position': 'relative',
                    #               },
                    #
                    #     ),
                    #
                    #     # html.Div([
                    #     #     #dcc.Loading(
                    #     #     #    id='loading-3',
                    #     #     #    type='default',
                    #     #     #    children=[
                    #     #             dcc.Graph(
                    #     #                 id='bar_chart_3', figure={},
                    #     #                 config={
                    #     #                     'displayModeBar': False},
                    #     #                 style={'height': '200px',
                    #     #                        'width': '95%',
                    #     #                        "display": "block",
                    #     #                        "margin-left": "auto",
                    #     #                        "margin-right": "auto",
                    #     #                        },
                    #     #             )
                    #     #       #  ]),
                    #     # ], style={'height': '50%',
                    #     #           'width': '100%',
                    #     #           'right': '0px',
                    #     #           'top': '0px',
                    #     #           #'position': 'absolute',
                    #     #           },
                    #     # )
                    #
                    # ],style={'height': '60%',
                    #          'width': '94%',
                    #          "display": "block",
                    #          "margin-left": "auto",
                    #          "margin-right": "auto",
                    #          'backgroundColor': 'rgba(246,105,35,0.3)'
                    #
                    #              #'top': '250px',
                    #              #'position': 'absolute',
                    #             },
                    #
                    #
                    # ),
                ]),

        ],
        style={'height': '700px',
                  'width': '60%',
                  'right': '0px',
                  'top': '0px',
                  'position': 'absolute',
                  'backgroundColor': fun_col_to_trans(dict_layout_cols['bg_blue2'], 0.5),
                  'border-color': fun_col_to_trans(dict_layout_cols['orange'], 0.5),
                  'border-left-style': 'solid'
                  },
    ),

], style={'position': 'relative',
          'height': '100%'}, )


# Figure callback
@app.callback(
    # Output('output_date_picker', 'children'),
    Output('bar_chart', 'figure'),
    Output('bar_chart_2', 'figure'),
    #Output('bar_chart_3', 'figure'),
    Output('area_headline', 'children'),
    Input('date_picker', 'date'),
    Input('map_figure', 'clickData'),
)
def update_output(date_value, clk_data):
    # Input data
    date_object = date.fromisoformat(date_value)
    date_string = date_object.strftime('%Y-%m-%d')
    date_to_str = date_string

    # Initialize default chart
    if clk_data is None:
        # print('empty')
        # Get DMI data
        cellid = shp_grid['KN10kmDK'].sample(n=1).values[0]
        cellname = shp_grid.loc[shp_grid['KN10kmDK'] == cellid, 'Stednavn'].values[0]
        # cell_lon = clk_data['points'][0]['customdata'][1]
        # cell_lat = clk_data['points'][0]['customdata'][2]
        # print(cellid)
        # Get DMI data
        df, date_from_str = fun_get_filter_dmi_data(
            date_to_str=date_to_str
            , cellid=cellid)

        print(date_from_str[0:10])
        print(date_to_str)

        print('Waves at {} - {}'.format(date_from_str[0:10], date_to_str))

        # Create figure
        fig_out = fun_fig_chart(
            df=df,
            mag_col='mean_wind_speed',
            dir_col='mean_wind_dir',
            dt_col='from_datetime',
            date_from_str=date_from_str,
            date_to_str=date_to_str,
            fig_type=1
        )

    else:
        # Help prints
        print(f'Click data: {clk_data}')
        cellid = clk_data['points'][0]['location']
        cellname = clk_data['points'][0]['customdata'][0]
        cell_lon = clk_data['points'][0]['customdata'][1]
        cell_lat = clk_data['points'][0]['customdata'][2]

        # Get DMI data
        df, date_from_str = fun_get_filter_dmi_data(
            date_to_str=date_to_str
            , cellid=cellid)

        # print(df)

        # Create figure
        fig_out = fun_fig_chart(
            df=df,
            mag_col='mean_wind_speed',
            dir_col='mean_wind_dir',
            dt_col='from_datetime',
            date_from_str=date_from_str,
            date_to_str=date_to_str,
            fig_type=1
        )

    string_prefix = 'You have selected: '
    string_suffix = 'Area: '
    string_out = string_prefix + date_string + string_suffix + cellname + ' CellID: ' + cellid

    # print(string_out)
    # return string_out,\

    return fig_out, fig_out, cellname
    #return fig_out, cellname


# Modal callback
@app.callback(
    Output("modal", "is_open"),
    Input("modal-button", "n_clicks"),
    [State("modal", "is_open")],
)
def toggle_modal(n1, is_open):
    if n1:
        return not is_open
    return is_open

# Backcast collaps callback
@app.callback(
    Output("prev-collapse", "is_open"),
    Input('prev-button', "n_clicks"),
    [State("prev-collapse", "is_open")],
)
def toggle_modal(c1, is_open):
    if c1:
        return not is_open
    return is_open



# Prev/forc callback
# @app.callback(
#     Output("prev-collapse", "is_open"),
#     Input("prev-button", "n_clicks"),
#     [State("prev-collapse", "is_open")],
# )
# def toggle_modal(n, is_open):
#     if n:
#         return not is_open
#     return is_open


# region HELPER FUNCTIONS
# region DEFINE FUNCTION FOR GETTING DMI DATA
def fun_get_filter_dmi_data(
        date_to_str,  # the last date for which the data is gotten
        cellid,  # id from grid cell
        obs_values=['mean_wind_speed', 'max_wind_speed_3sec', 'mean_wind_dir'], # which observations from DMI data to keep
        no_days=2,  # number of days to get data for
        api_key='604e80dd-9ee9-454b-aea0-12edc1ead8bf',  # api key for DMI API
        stationid='',  # extra parameter, if weather station data
        # is used instead of grid data
        limit=10000  # max number of observations to get
):
    ## Calculate first date
    # Create date format from string
    date_to = dt.date.fromisoformat(date_to_str)

    # Add hour to get CEST (ignoring summertime)
    date_to = date_to + dt.timedelta(hours=1)

    # Calculate start date
    date_from = date_to - dt.timedelta(days=no_days)

    # Create string to connection string
    date_to_str = date_to_str + 'T23:00:00Z'
    date_from_str = str(date_from) + 'T00:00:00Z'

    ## Set up connection string
    if not stationid:
        str_geo = '&cellId=' + cellid
        dmi_path = 'https://dmigw.govcloud.dk/v2/climateData/collections/10kmGridValue/items?'
    else:
        str_geo = '&stationId=' + stationid
        dmi_pah = 'https://dmigw.govcloud.dk/v2/climateData/collections/stationValue/items?'

    time_res = 'hour'  # time interval for obersvations
    str_datetime = 'datetime=' + date_from_str + "/" + date_to_str
    str_time_res = '&timeResolution=' + time_res
    str_limit = '&limit=' + str(limit)
    str_api_key = '&api-key=' + api_key

    # Concatenate all
    req_str = dmi_path + str_datetime + str_time_res + str_geo + str_limit + str_api_key
    # print(req_str)

    ### Get data ###
    # Get data and create data
    data = json.loads(
        requests.get(req_str).text
    )

    # Get date into data frame
    data = pd.json_normalize(data['features'])

    ## Transform data ##

    # 1) Subset relevant columns
    cols_keep = [col for col in list(data.columns) if 'properties' in col]
    data = data[cols_keep].copy()

    # 2) Rename columns
    cols_keep_new_name = [col.replace("properties.", "") for col in cols_keep]
    data.columns = cols_keep_new_name

    # 3) Filter rows
    data = data[data['parameterId'].isin(obs_values)]

    # 4) Pivot table
    data = pd.pivot_table(data, values='value',
                          index='from',
                          columns='parameterId').reset_index()

    # 5) Create date columns
    data['from_datetime'] = pd.to_datetime(data['from'].str.replace('\+00:00', "", regex=False))
    data['date'] = data['from_datetime'].dt.date

    # 6) Drop rows with na
    data.dropna(inplace=True)

    # Return
    return data, date_from_str


# endregion

# region DEFINE FUNCTION FOR FORECAST DATA (FCOO)
# Define function to get data
def fun_get_fcoo_data(var, lat, lon):
    # Base string to FCOO
    fcoo_path = 'https://app.fcoo.dk/metoc/v2/data/timeseries?variables='

    # Construct request string
    req_str = fcoo_path + var + '&lat=' + str(lat) + '&lon=' + str(lon)
    print(req_str)

    # Collect data
    data = json.loads(
        requests.get(req_str).text
    )

    l_cols = list(data[var].keys())

    if len(l_cols) == 1:
        df = pd.DataFrame(
            {'WavePeriod': data[var][l_cols[0]]['data'],
             'Time': data[var][l_cols[0]]['time']
             })
    else:
        df = pd.DataFrame(
            {l_cols[0]: data[var][l_cols[0]]['data'],
             l_cols[1]: data[var][l_cols[1]]['data'],
             'Time': data[var][l_cols[0]]['time']
             })

    # Set time as index to simpify join
    # df.set_index('Time', inplace=True)

    df['Time'] = pd.to_datetime(df['Time'])
    return df


# Define function to calcualate wind direction and magnitude
def fun_vec_to_dir_mag(df,
                       u_vec,
                       v_vec,
                       var):
    dir_name = var + 'Dir'
    mag_name = var + 'Magnitude'

    df[dir_name] = round(np.arctan2(df[u_vec], df[v_vec]) * 180 / np.pi + 180, 0)
    df[mag_name] = round(np.sqrt(df[u_vec] ** 2 + df[v_vec] ** 2), 1)

    return df




# endregion

# region DEFINE FUNCTION FOR FIGURE

def fun_fig_chart(
        df,  # dataframe to be visualized
        mag_col,  # column containing magnitude values
        dir_col,  # column containing direction values
        dt_col,  # column containing datetime values
        date_from_str,  # start date for period
        date_to_str,  # end date for period
        fig_type,  # set figure type for:
        # backcast wind (1),
        # forecast wind (2),
        # forecast wave (3)
):
    print(fig_type)

    # Create column with cardinal direction
    df['Wind_CardDir'] = df[dir_col].apply(fun_DegToCard)
    # Assign color based on cardinal direction
    df['Wind_Dir_Col'] = df['Wind_CardDir'].map(col_pal_trans)

    # print(df['Wind_Dir_Col'])

    # Hover data
    hover_data_chart = np.stack((df[dir_col], df['Wind_CardDir'], df[dt_col].dt.hour.astype(str) + ':00'), axis=1)

    # Figure
    if fig_type == 3:
        fig_chart = make_subplots(specs=[[{"secondary_y": True}]])
    else:
        fig_chart = go.Figure()

    # Add bar trace
    fig_chart.add_trace(
        go.Bar(
            x=df[dt_col],
            y=df[mag_col],
            marker=dict(
                color=dict_layout_cols['primary'],
                opacity=0.7,
                # line_color = dict_layout_cols['orange'],
                line_width=0
            ),
            customdata=hover_data_chart,
            hovertemplate=
            'Mean wind speed: %{y} m/s' +
            '<br>Wind direction: %{customdata[1]} (%{customdata[0]}\xb0)' +
            '<br>Time: %{customdata[2]}<extra></extra>',
            hoverlabel=dict(
                bgcolor='rgba(255,255,255,0.3)',
                font=dict(color='black')
            ),
            showlegend=True,
            name='Avg. wind speed',
            legendrank=2,
        ))

    # Set text for figure type
    if fig_type == 1 or fig_type == 2:
        # Assign text variable
        t_fig_type = 'wind'

        #
        fig_chart.update_traces(
            customdata=hover_data_chart,
            hovertemplate='Mean wind speed: %{y} m/s' +
                          '<br>Wind direction: %{customdata[1]} (%{customdata[0]}\xb0)' +
                          '<br>Time: %{customdata[2]}<extra></extra>',
            name='Avg. {} speed'.format(t_fig_type),
            legendrank=2
        )

        h = 285

        title_text = '{} - {}'.format(date_from_str[0:10], date_to_str)

        y_ax_range = dict(range=[0, 30])

        if fig_type == 1:
            fig_chart.add_trace(go.Scatter(x=df[dt_col],
                                           y=df['max_wind_speed_3sec'],
                                           hovertemplate=
                                           'Max wind speed (3s): %{y} m/s<extra></extra>',
                                           line=dict(
                                               # opacity = 0.8,
                                               color="rgb(255,255,255)",  # dict_layout_cols['bg_blue']
                                               width=2,
                                               dash='dash'

                                           ),
                                           # hoverlabel=dict(
                                           #     bgcolor='rgba(255,255,255,0.3)',
                                           #     font=dict(color='black')
                                           # ),
                                           showlegend=True,
                                           name='Max. wind speed',
                                           legendrank=1
                                           ),
                                # secondary_y=True
                                ),



    elif fig_type == 3:

        t_fig_type = 'Wave'

        fig_chart.update_traces(
            customdata=hover_data_chart,
            hovertemplate='Wave height: %{y} m' +
                          '<br>Wave direction: %{customdata[1]} (%{customdata[0]}\xb0)' +
                          '<br>Time: %{customdata[2]}<extra></extra>',
            name='{} height'.format(t_fig_type),
            legendrank=2,
        )

        h = 150
        title_text = '{} - {}'.format('1','2')#format(date_from_str[0:10], date_to_str),


        y_ax_range = dict(range=[0, 5])




    else:
        hover_text_1 = ''
        h = ''
        title_text = ''
        y_ax_range = ''

    # Add direction arrows
    for i, row in df.iterrows():
        x_date = row[dt_col]

        ax = dict_dir_coord[row['Wind_CardDir']]['X_cord']
        ay = dict_dir_coord[row['Wind_CardDir']]['Y_cord']

        fig_chart.add_annotation(
            x=x_date,
            y=row[mag_col] + 1,
            ax=ax,
            ay=ay,
            arrowhead=3,
            arrowsize=1.6,
            arrowwidth=1.1,
            arrowcolor=dict_layout_cols['orange'],
            xref="x",
            yref="y"
        )

    # Set axes
    y_axes = dict(gridcolor='rgba(255,255,255,0.4)',
                  color=dict_layout_cols['white'],
                  gridwidth=0.0001
                  )

    x_axes = dict(color=dict_layout_cols['white'],
                  linewidth=0.1
                  )

    fig_chart.update_yaxes(y_axes)

    fig_chart.update_xaxes(x_axes)

    # Set layout
    fig_chart.update_layout(
        yaxis=y_ax_range,  # , yaxis2=y_ax_range
        autosize=True,
        # width=800,
        height=h,
        hovermode='x unified',
        hoverlabel=dict(bgcolor='rgba(255,255,255,0.75)',
                        font=dict(color='black')
                        ),
        margin=dict(l=0, r=20, t=20, b=20),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        legend=dict(
            yanchor="top",
            y=1.02,
            xanchor="left",
            x=0.01,
            bgcolor=dict_layout_cols['transparent'],
            font=dict(color=dict_layout_cols['white'])
        ),
        title={'text': title_text,
               'x': 0.5,
               'y': 0.94,
               'font': {'color': dict_layout_cols['white']}
               }
    )

    if fig_type == 3:
        if df['Sealevel'][0] == -9999:
            df[mag_col] = 0

            fig_chart = go.Figure()

            fig_chart.add_trace(go.Bar(
                x=df[dt_col],
                y=df[mag_col]
            )
            )

            fig_chart.update_layout(
                plot_bgcolor='rgba(0, 0, 0, 0)',
                paper_bgcolor='rgba(0, 0, 0, 0)',
                title={'text': 'No wave forecast to display',
                       'x': 0.5,
                       'y': 0.94,
                       'font': {'color': dict_layout_cols['white']}
                       }
            )

            fig_chart.update_yaxes(y_axes)
            fig_chart.update_xaxes(x_axes)

            # print(df.head())
            return fig_chart

        else:
            return fig_chart

    return fig_chart


# endregion

# endregion


if __name__ == '__main__':
    app.run_server(debug=True)
