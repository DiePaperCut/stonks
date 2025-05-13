import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import requests
from test_gen import StockDataGenerator

# Ініціалізуємо Dash з Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = "X11AAMEF5Y6V31PR"

# Функція отримання даних акцій з Alpha Vantage
def get_stock_data(ticker, days_back=90, test_data = True):
    if not test_data:
        source = "Використовується Alpha Vantage API"
        limit = "Обмеження API: 25 запитів за день"
        try:
            # Отримати щоденний звіт з акцій
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url)
            data = response.json()
            
            # Дії при помилках API
            if "Error Message" in data:
                raise Exception(data["Error Message"])
            
            # Конвертувати в датафрейм
            time_series = data.get('Time Series (Daily)', {})
            if not time_series:
                raise Exception("Не отримано ніякої інформації з API")
                
            df = pd.DataFrame(time_series).T
            df.columns = [col.split('. ')[1].lower() for col in df.columns]
            
            # Перейменування колонок, для відповідності оригінальномк формату
            column_mapping = {
                'open': 'open',
                'high': 'high', 
                'low': 'low', 
                'close': 'close',
                'volume': 'volume'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            df.index.name = 'date'
            df = df.reset_index()
            df['date'] = pd.to_datetime(df['date'])
            
            df = df.sort_values('date')
            if days_back > 0:
                start_date = datetime.now() - timedelta(days=days_back)
                df = df[df['date'] >= start_date]
            
            for col in df.columns:
                if col != 'date':
                    df[col] = pd.to_numeric(df[col])
                    
            df['adj_close'] = df['close']
            
            return (df, source, limit)
            
        except Exception as e:
            print(f"Error fetching data: {str(e)}")
            # Повернути порожній датафрейм з очікуваними колонками
            return (pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume']), source, limit)
    
    test_generator = StockDataGenerator()
    source = "Використовується тестова генерація даних"
    limit = "Обмеження API: Немає"
    return (test_generator.gen_stock_data(ticker, days_back), source, limit)
        

# Параметри за замовчуванням
DEFAULT_TICKER = "AAPL"
DEFAULT_DAYS = 90

# Тікери
stock_options = [
    {'label': 'Apple (AAPL)', 'value': 'AAPL'},
    {'label': 'Microsoft (MSFT)', 'value': 'MSFT'},
    {'label': 'Google (GOOGL)', 'value': 'GOOGL'},
    {'label': 'Amazon (AMZN)', 'value': 'AMZN'},
    {'label': 'Tesla (TSLA)', 'value': 'TSLA'},
    {'label': 'NVIDIA (NVDA)', 'value': 'NVDA'},
    {'label': 'Meta/Facebook (META)', 'value': 'META'},
    {'label': 'Netflix (NFLX)', 'value': 'NFLX'}
]

# Define app layout with organized sections
app.layout = dbc.Container([
    # Заголовок
    dbc.Row([
        dbc.Col([
            html.H1("STONKS", className="text-center my-4")
        ], width=12)
    ]),
    
    dbc.Row([
        # Панель керування
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Параметри акцій"),
                        dbc.CardBody([
                            html.Label("Виберіть компанію:"),
                            dcc.Dropdown(id='ticker-dropdown', options=stock_options, value=DEFAULT_TICKER, clearable=False),
                            
                            html.Br(),
                            
                            html.Label("Період (днів):"),
                            dcc.Slider(
                                id='days-slider',
                                min=30, max=365, step=30, value=DEFAULT_DAYS,
                                marks={30: '30д', 90: '90д', 180: '180д', 365: '365д'}
                            ),
                            
                            html.Br(),
                            
                            dbc.Button("Оновити дані", id="update-button", color="primary", className="me-2"),

                            dbc.Button("Завантажити CSV", id="btn-download-csv", color="success"),
                            dcc.Download(id="download-dataframe-csv"),
                            
                            dbc.Spinner(html.Div(id="loading-output", className="mt-3")),
                            
                            html.Div([
                                html.P("Використовується Alpha Vantage API", className="text-muted small mt-3", id="source"),
                                html.P("Обмеження API: 25 запитів за день", className="text-muted small", id = "limit")
                            ])
                        ])
                    ]),
                ], width = 12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Статистика"),
                        dbc.CardBody([
                            html.Div(id='stats-table')
                        ])
                    ])
                ], width = 12)
            ], className="mb-4")
        ], width=3),
        
        # Основний графік
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Графік цін акцій"),
                        dbc.CardBody([
                            dcc.Graph(id='stock-price-chart', style={'height': '300px'})
                        ])
                    ])
                ])
            ], className="mb-4"),
            # Аналіз об'єму
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Аналіз об'єму торгів"),
                        dbc.CardBody([
                            dcc.Graph(id='volume-chart', style={'height': '250px'})
                        ])
                    ])
                ], width=12)
            ], className="mb-4")
        ], width=9)
    ], className="mb-4"),
    
    # Футер
    html.Footer([
        html.P("Dash-додаток для аналізу цін акцій з використанням Alpha Vantage API", className="text-center")
    ])
], fluid=True)

# Колбек для завантаження CSV
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    State("ticker-dropdown", "value"),
    State("days-slider", "value"),
    prevent_initial_call=True,
)
def download_csv(n_clicks, ticker, days):
    df = get_stock_data(ticker, days)
    return dcc.send_data_frame(df.to_csv, f"{ticker}_data.csv")

# Основний колбек для оновлення графіків
@app.callback(
    [Output('stock-price-chart', 'figure'),
     Output('volume-chart', 'figure'),
     Output('stats-table', 'children'),
     Output('loading-output', 'children'),
     Output('source', 'children'),
     Output('limit', 'children')],
    [Input('update-button', 'n_clicks')],
    [State('ticker-dropdown', 'value'),
     State('days-slider', 'value')]
)
def update_charts(n_clicks, ticker, days):
    try:
        # Підтягнути дані
        df, source, limit = get_stock_data(ticker, days)
        
        # Опрацювання кейсу з порожніми даними
        if df.empty:
            empty_fig = go.Figure().update_layout(title="Дані не знайдено")
            return (empty_fig, empty_fig, "Дані не знайдено", 
                    "Помилка: Не вдалося отримати дані", source, limit)
        
        # 1. Створити графік ціни (candlestick за замовчуванням)
        fig_price = go.Figure()
        
        fig_price.add_trace(
            go.Candlestick(
                x=df['date'], open=df['open'], high=df['high'],
                low=df['low'], close=df['close'], name='OHLC'
            )
        )
        
        fig_price.update_layout(
            title=f"Ціни акцій {ticker}",
            xaxis_title="Дата", yaxis_title="Ціна ($)",
            template="plotly_white", xaxis_rangeslider_visible=False,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # 2. Створити графік об'єму
        fig_volume = go.Figure()
        fig_volume.add_trace(
            go.Bar(x=df['date'], y=df['volume'], name='Об\'єм', marker_color='dodgerblue')
        )
        fig_volume.add_trace(
            go.Scatter(x=df['date'], y=df['close'], name='Ціна закриття', 
                      line=dict(color='red', width=1), yaxis="y2")
        )
        fig_volume.update_layout(
            title=f"Об'єм торгів {ticker}",
            xaxis_title="Дата", yaxis_title="Об'єм",
            yaxis2=dict(title="Ціна ($)", overlaying="y", side="right", showgrid=False),
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # 3. Створення таблиці статистики
        if len(df) > 0:
            latest = df.iloc[-1]
            oldest = df.iloc[0]
            price_change = latest['close'] - oldest['close']
            pct_change = (price_change / oldest['close']) * 100
            
            stats_table = html.Div([
                html.H5(f"Статистика для {ticker}"),
                html.Table([
                    html.Tr([html.Td("Остання дата:"), html.Td(latest['date'].strftime('%Y-%m-%d'))]),
                    html.Tr([html.Td("Ціна відкриття:"), html.Td(f"${latest['open']:.2f}")]),
                    html.Tr([html.Td("Ціна закриття:"), html.Td(f"${latest['close']:.2f}")]),
                    html.Tr([html.Td("Найвища ціна:"), html.Td(f"${latest['high']:.2f}")]),
                    html.Tr([html.Td("Найнижча ціна:"), html.Td(f"${latest['low']:.2f}")]),
                    html.Tr([html.Td("Об'єм:"), html.Td(f"{latest['volume']:,}")]),
                    html.Tr([html.Td("Зміна за період:"), html.Td(f"${price_change:.2f} ({pct_change:.2f}%)")], 
                           style={'color': 'green' if price_change > 0 else 'red'})
                ], className="table table-striped")
            ])
        else:
            stats_table = html.Div("Недостатньо даних для відображення статистики")
        
        return (fig_price, fig_volume, stats_table, f"Дані оновлено для {ticker}", source, limit)
    
    except Exception as e:
        empty_fig = go.Figure().update_layout(title="Помилка при отриманні даних")
        error_message = html.Div([
            html.H5("Помилка при отриманні даних"),
            html.P(f"Деталі помилки: {str(e)}")
        ])
        return (empty_fig, empty_fig, error_message, f"Помилка: {str(e)}", source, limit)

if __name__ == '__main__':
    app.run(debug=False)