import plotly.graph_objects as go

map_layout = dict(title="Covid-19 Intervention Modelling", autosize=False,
                  margin={"r": 0, "t": 0, "l": 0, "b": 0},
                  height=600, width=580,
                  paper_bgcolor="rgb(247, 247, 245)",
                  geo=go.layout.Geo(
                      center={"lat": 22, "lon": 82.5},
                      resolution=110,
                      scope='asia',
                      showframe=False,
                      showcoastlines=True,
                      fitbounds="locations",
                      landcolor="rgb(247, 247, 245)",
                      oceancolor="rgb(247, 247, 245)",
                      bgcolor="rgb(247, 247, 245)",
                      framecolor="rgb(247, 247, 245)",
                      countrycolor="black",
                      coastlinecolor="black",
                      projection_type='mercator',
                      lonaxis_range=[-4.0, 26.0],
                      lataxis_range=[-10.5, 20.0],
                      domain=dict(x=[0, 1], y=[0, 1])))


def get_bar_layout(city):
    layout = dict(
        title=dict(
            text='SEIR Model for {0}'.format(city),
            font=dict(family="Open Sans, sans-serif", size=15, color="#515151"),
        ),
        paper_bgcolor="rgb(247, 247, 245)",
        plot_bgcolor="rgb(247, 247, 245)",
        updatemenus=list([
            dict(active=1,
                 buttons=list([
                     dict(label='Log Scale',
                          method='update',
                          args=[{'visible': [True, True]},
                                {'title': 'Log scale',
                                 'yaxis': {'type': 'log'}}]),
                     dict(label='Linear Scale',
                          method='update',
                          args=[{'visible': [True, True]},
                                {'title': 'Linear scale',
                                 'yaxis': {'type': 'linear'}}])
                 ]),
                 )
        ]),
        legend=dict(
            x=-0.185,
            y=-0.1,
            traceorder="reverse",
            font=dict(
                family="sans-serif",
                size=12,
                color="black"
            ),
            bgcolor="rgb(247, 247, 245)",
            bordercolor="rgb(247, 247, 245)",
            borderwidth=2
        ),
        # barmode='stack',
        width=1100,
        height=400,
        font=dict(family="Open Sans, sans-serif", size=13),
        hovermode="all",
        xaxis=dict(title="Days"), yaxis=dict(title="Records"))
    return layout
