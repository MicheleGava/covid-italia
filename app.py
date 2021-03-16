# import libraries
import numpy as np
import pandas as pd
import pickle
from datetime import datetime

import dash
import dash_core_components as dcc 
import dash_html_components as html 
from dash.dependencies import Input, Output
import plotly.express as px 
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#######################
### Data preparation###
#######################

# load population data
df_pop = pd.read_csv("./data/pop_cleaned.csv")

# retrieve Covid data
nazionali = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv'
regioni   = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv'
province  = 'https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-province/dpc-covid19-ita-province.csv'

feat_nazionali = ['data', 'ricoverati_con_sintomi', 'terapia_intensiva',
            'totale_ospedalizzati', 'isolamento_domiciliare',
            'totale_positivi', 'variazione_totale_positivi', 'nuovi_positivi',
            'dimessi_guariti', 'deceduti', 'totale_casi','tamponi']
feat_regioni = ['data', 'denominazione_regione', 'lat','long','ricoverati_con_sintomi','terapia_intensiva',
            'totale_ospedalizzati', 'isolamento_domiciliare',
            'totale_positivi', 'variazione_totale_positivi', 'nuovi_positivi',
            'dimessi_guariti', 'deceduti', 'totale_casi','tamponi']
feat_province = ['data', 'denominazione_provincia', 'sigla_provincia','lat','long', 'totale_casi']

def get_data_from_url(kind, url, features):
    '''
    load data from dpc's github repo
    if failing, load from csv
    '''
    csv_file = './data/'+kind+'.csv'
    try:
        tmp_df = pd.read_csv(url)
        tmp_df.to_csv(csv_file, index=False)
    except:
        tmp_df = pd.read_csv(csv_file)
    tmp_df['data'] = pd.to_datetime(tmp_df['data']).dt.date
    tmp_df = tmp_df[features]
    return tmp_df
   
df_nazionali = get_data_from_url('nazionali', nazionali, feat_nazionali)
df_regioni = get_data_from_url('regioni', regioni, feat_regioni)
df_province = get_data_from_url('province', province, feat_province)

# aggiunta colonna Popolazione
df_nazionali['popolazione'] = df_pop.query("Territorio == 'Italia'")["Popolazione"][0]
df_province['popolazione'] = df_province.merge(df_pop,how='left', left_on='denominazione_provincia', right_on='Territorio')['Popolazione']
df_regioni['popolazione'] = df_regioni.merge(df_pop,how='left', left_on='denominazione_regione', right_on='Territorio')['Popolazione']

# Correzione: il numero cumulato di tamponi del 17.12.2020 sembra sbagliato (inferiore al giorno precedente). Lo sostituisco con NaN
df_nazionali.loc[297, "tamponi"] = np.nan

# aggiungo Nuovi tamponi ai dataset nazionali e regioni
df_nazionali['nuovi_tamponi'] = df_nazionali['tamponi'].diff()
df_nazionali.loc[0,'nuovi_tamponi'] = df_nazionali.loc[0,'tamponi']
df_regioni['nuovi_tamponi'] = df_regioni['tamponi'].diff()
df_regioni.loc[0,'nuovi_tamponi'] = df_regioni.loc[0,'tamponi']

# aggiungo Nuovi decessi ai dataset nazionali e regioni
df_nazionali['nuovi_decessi'] = df_nazionali['deceduti'].diff()
df_nazionali.loc[0,'nuovi_decessi'] = df_nazionali.loc[0,'deceduti']
df_regioni['nuovi_decessi'] = df_regioni['deceduti'].diff()
df_regioni.loc[0,'nuovi_decessi'] = df_regioni.loc[0,'deceduti']

# aggiungo media mobile settimanale decessi al dataset nazionale 
df_nazionali['decessi_media_mobile'] = df_nazionali["nuovi_decessi"].rolling(7).mean()

# calcolo KPIs fissi (non dipendono dai filtri)
delta_pos = 100*(df_nazionali.sort_values(by='data', ascending=False).iloc[0]['nuovi_positivi'] - df_nazionali.sort_values(by='data', ascending=False).iloc[1]['nuovi_positivi']) / df_nazionali.sort_values(by='data', ascending=False).iloc[1]['nuovi_positivi']
perc_tamponi = 100 * df_nazionali.sort_values(by='data', ascending=False).iloc[0]['nuovi_positivi'] /  df_nazionali.sort_values(by='data', ascending=False).iloc[0]['nuovi_tamponi']
delta_dec = 100*(df_nazionali.sort_values(by='data', ascending=False).iloc[0]['nuovi_decessi'] - df_nazionali.sort_values(by='data', ascending=False).iloc[1]['nuovi_decessi']) / df_nazionali.sort_values(by='data', ascending=False).iloc[1]['nuovi_decessi']

last_date = df_nazionali['data'].max()
first_date = df_nazionali['data'].min()
delta_t = (last_date - first_date).days

#######################
### Graphs def      ###
#######################

# Nazionale - nuovi positivi
# fig_1_1_1 = make_subplots(specs=[[{"secondary_y": True}]])
# fig_1_1_1.add_trace(
#    go.Scatter(x=df_nazionali["data"], y=df_nazionali["nuovi_positivi"], name='Nr. assoluto'), 
#    secondary_y=False
# )
# fig_1_1_1.add_trace(
#    go.Scatter(x=df_nazionali["data"], y=100*df_nazionali["nuovi_positivi"]/df_nazionali["nuovi_tamponi"], name='% su tamponi'),
#    secondary_y=True
# )
# fig_1_1_1.update_layout(title_text='Nuovi positivi')

# Nazionale - decessi
fig_1_1_2 = make_subplots()
fig_1_1_2.add_trace(
    go.Scatter(x=df_nazionali["data"], y=df_nazionali["nuovi_decessi"],name='Nr. assoluto',opacity=0.5)
)
fig_1_1_2.add_trace(
    go.Scatter(x=df_nazionali["data"], y=df_nazionali["decessi_media_mobile"],name='Media mobile settimanale')
)
fig_1_1_2.update_layout(title_text='Decessi')

#Nazionale - ospedalizzazioni
fig_1_2_1 = make_subplots(specs=[[{"secondary_y": True}]])
fig_1_2_1.add_trace(
    go.Scatter(x=df_nazionali["data"], y=df_nazionali["totale_ospedalizzati"],name='Totale ospedalizzati'), 
    secondary_y=False
)
fig_1_2_1.add_trace(
    go.Bar(x=df_nazionali["data"], y=df_nazionali["terapia_intensiva"],name='Terapia intensiva', opacity=0.5), 
    secondary_y=True
)
fig_1_2_1.update_layout(title_text='Ospedalizzati')

#######################
### Inizio App      ###
#######################

app = dash.Dash(__name__)

app.layout = html.Div(children = [
    html.H1(children='Covid 19 Italia'),
    html.Div(  # grafico casi con intervallo di selezione
        [
            #html.Div(["Periodo:", dcc.DatePickerRange(id='periodo', display_format='DD-MM-YYYY', start_date=first_date, end_date=last_date)]),
            dcc.RangeSlider(
                id = 'periodo',
                min = 0,
                max = delta_t,
                step = 1,
                value = [0, delta_t]
            ),
            dcc.Graph(id='gn_casi')
        ]
    ),
    # dcc.Graph(
    #     id='gn_casi',
    #     figure=fig_1_1_1 
    # ),
    dcc.Graph(
        id='gn_decessi',
        figure=fig_1_1_2 
    ),
    dcc.Graph(
        id='gn_osp',
        figure=fig_1_2_1 
    )

])

@app.callback(
    Output('gn_casi','figure'),
    [Input('periodo','value')]
)
def update_gn_casi(value):
    data_da = first_date + pd.Timedelta(value[0], unit='days')
    data_a  = first_date + pd.Timedelta(value[1], unit='days')
    filtered_df = df_nazionali[(df_nazionali.data >= data_da) & (df_nazionali.data <= data_a)]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
       go.Scatter(x=filtered_df["data"], y=filtered_df["nuovi_positivi"], name='Nr. assoluto'), 
       secondary_y=False
    )
    fig.add_trace(
       go.Scatter(x=filtered_df["data"], y=100*filtered_df["nuovi_positivi"]/filtered_df["nuovi_tamponi"], name='% su tamponi'),
       secondary_y=True
    )
    fig.update_layout(title_text='Nuovi positivi')
    return fig 

if __name__ == '__main__':
    app.run_server(debug=True)