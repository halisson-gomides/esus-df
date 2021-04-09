import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd


lst_columns = ['dataNotificacao', 'ocupacaoSuspeitoCli', 'saidaConfirmadaObitos', 'NO_FANTASIA',
               'NU_LATITUDE', 'NU_LONGITUDE']
df = pd.read_csv('dados/processados/e-sus-ocupacao-estabelecimento.csv', parse_dates=['dataNotificacao'], usecols=lst_columns)

# Agregações para mostrar na tabela
df_tabela = df.groupby([
    df['dataNotificacao'].dt.to_period('M'),
    'NO_FANTASIA',
    'NU_LATITUDE',
    'NU_LONGITUDE'
]).agg({'ocupacaoSuspeitoCli': 'mean', 'saidaConfirmadaObitos': 'sum'}).reset_index()


# Agregações para mostrar no mapa
df_mapa = df_tabela.groupby(['NO_FANTASIA', 'NU_LATITUDE', 'NU_LONGITUDE']).agg({
    'ocupacaoSuspeitoCli': 'mean',
    'saidaConfirmadaObitos': 'sum'
}).reset_index()


periodos_range = {i: {'label': label.strftime('%m-%Y'), 'style': {'transform': 'rotate(-40deg)'}} for i, label in enumerate(df_tabela['dataNotificacao'].unique())}


def generate_table(dataframe, max_rows=50, idT='id_padrao'):
    data = dataframe.copy()
    data.columns = ['Notificação', 'Hospital', 'Ocupação média', 'Total Óbitos']
    data['Ocupação média'] = data['Ocupação média'].round(2)
    data = data.sort_values(by=['Notificação', 'Hospital'])
    for col in data.columns:
        if data[col].dtype not in ['object', 'int64', 'float64']:
            data[col] = data[col].dt.strftime('%m-%Y')

    return html.Table(id=idT, children=[
        html.Thead(
            html.Tr([html.Th(col) for col in data.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(data.iloc[i][col]) for col in data.columns
            ]) for i in range(min(len(data), max_rows))
        ])
    ])


def generate_map(dataframe, colunas=''):
    colunas = dataframe.columns if colunas == '' else colunas
    mapa = px.scatter_mapbox(dataframe[colunas], lat='NU_LATITUDE', lon='NU_LONGITUDE',
                             hover_name='NO_FANTASIA',
                             hover_data=['ocupacaoSuspeitoCli', 'saidaConfirmadaObitos'],
                             color_continuous_scale="viridis",
                             color='saidaConfirmadaObitos',
                             size='ocupacaoSuspeitoCli',
                             height=300,
                             zoom=9)
    mapa.update_layout(mapbox_style='carto-positron')
    mapa.update_layout(height=600, margin={'r': 0, 't': 0, 'l': 0, 'b': 0})
    return mapa


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title='e-SUS - DF')

app.layout = html.Div(children=[
    html.H1(children='Ocupação dos Leitos SUS na linha do tempo'),

    html.Div(className="row", children='Dados do Distrito Federal.'),

    html.Label('Linha do Tempo'),
    html.Div(
        style={
            "width": "90%",
            "padding-bottom": "20px"
        },
        children=[
                dcc.RangeSlider(
                    id='dtnotificacao_range',
                    updatemode='mouseup',  # nao deixa atualizar ate que o botao do mouse seja liberado
                    min=0,
                    max=len(periodos_range)-1,
                    marks=periodos_range,
                    value=[min(periodos_range), max(periodos_range)],
                    allowCross=False,
                    step=None,
                )
        ]
    ),

    dcc.Graph(
        id='map-estabelecimentos',
        figure=generate_map(df_mapa)
    ),

    html.H4(children='Amostra dos Dados'),
    generate_table(df_tabela[['dataNotificacao', 'NO_FANTASIA', 'ocupacaoSuspeitoCli', 'saidaConfirmadaObitos']], idT='tb_amostra')
])


@app.callback(
    [
        Output(component_id='map-estabelecimentos', component_property='figure'),
        Output(component_id='tb_amostra', component_property='children')
    ],
    Input(component_id='dtnotificacao_range', component_property='value')
)
def filtro_date(date_range):
    idx_min = min(date_range)
    idx_max = max(date_range)
    date_min = periodos_range[idx_min]["label"]
    date_max = periodos_range[idx_max]["label"]
    # print(f'date_range: {date_range}')
    # print(f'idx_min: {idx_min} | periodo: {date_min}')
    # print(f'idx_max: {idx_max} | periodo: {date_max}')
    df_filtrado = df_tabela.loc[(df_tabela['dataNotificacao'] >= date_min) & (df_tabela['dataNotificacao'] <= date_max)]
    df_mapa = df_filtrado.groupby(['NO_FANTASIA', 'NU_LATITUDE', 'NU_LONGITUDE']).agg({
        'ocupacaoSuspeitoCli': 'mean',
        'saidaConfirmadaObitos': 'sum'
    }).reset_index()
    return generate_map(df_mapa),  generate_table(df_filtrado[['dataNotificacao', 'NO_FANTASIA', 'ocupacaoSuspeitoCli', 'saidaConfirmadaObitos']], idT='tb_amostra')


if __name__ == '__main__':
    app.run_server(debug=True)
