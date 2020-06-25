import numpy as np
import pandas as pd
import datetime
import plotly.graph_objects as plotgraph
from datasync.file_locator import FIRSTJAN


class TimeSeriesPlot:

    def timeseries_data_plot(self, I, R, Severe_H, R_Fatal, date, cumsum):
        I = np.array([int(n) for n in I])
        R = np.array([int(n) for n in R])
        Severe_H = np.array([int(n) for n in Severe_H])
        R_Fatal = np.array([int(n) for n in R_Fatal])

        T = np.array([(FIRSTJAN + datetime.timedelta(days=i)) for i in range(241)])
        days = (datetime.datetime.now() - FIRSTJAN).days
        low_offset = -30
        high_offset = 35
        ht_delta = '''%{fullData.name}	<br> &#931; :%{y:,}<br> &#916;: %{text}<br> Day :%{x} <extra></extra>'''
        ht_active = '''%{fullData.name}	<br> &#931; :%{y:,}<br> Day :%{x} <extra></extra>'''
        active = I[days+low_offset:days+high_offset]
        trace1 = plotgraph.Scatter(x=T[days + low_offset:days + high_offset], y=active, name='Active Infectious', text=np.diff(active),
                                   marker=dict(color='rgb(253,192,134,0.2)'), hovertemplate=ht_active)
        total=I[days+low_offset:days+high_offset]+R[days+low_offset:days+high_offset]
        trace2 = plotgraph.Scatter(x=T[days + low_offset:days + high_offset], y=total, name='Predicted Infected', text=total,
                                   marker=dict(color='rgb(240,2,127,0.2)'), hovertemplate=ht_active)

        severe=Severe_H[days+low_offset:days+high_offset]
        trace3 = plotgraph.Scatter(x=T[days + low_offset:days + high_offset], y=severe, name='Critical hospitalized', text=np.diff(severe),
                                   marker=dict(color='rgb(141,160,203,0.2)'), hovertemplate=ht_active)
        fatal=R_Fatal[days+low_offset-15:days+high_offset-15]
        trace4 = plotgraph.Scatter(x=T[days + low_offset:days + high_offset], y=fatal, name='Fatalities', text=np.diff(fatal),
                                   marker=dict(color='rgb(56,108,176,0.2)'), hovertemplate=ht_active)

        date = pd.to_datetime(date, format='%Y-%m-%d').date
        ts = pd.DataFrame({"Date Announced":date, "cumsum":cumsum})
        r = pd.date_range(start=ts['Date Announced'].min(), end =datetime.datetime.now().date())
        lastValue = list(ts['cumsum'])[-1]
        ts = ts.set_index("Date Announced").reindex(r).fillna(lastValue).rename_axis("Date Announced").reset_index()
        filter = ts["Date Announced"].dt.date >= datetime.datetime.now().date()- datetime.timedelta(days=-low_offset)
        y_actual = [0]*(-low_offset - len(ts[filter]["cumsum"])) + list(ts[filter]["cumsum"])

        trace5 = plotgraph.Scatter(x=T[days + low_offset:days], y=y_actual, name='Reported Infected &nbsp; &nbsp;', text=total,
                                   marker=dict(color='rgb(0,0,0,0.2)'), hovertemplate=ht_active)

        data = [trace1, trace2, trace3, trace4, trace5]

        # find infected and Fatal after 15 and 30 days
        all_dates = [i.date() for i in T]
        today = datetime.date.today()
        dateAfter15days = today+datetime.timedelta(days=15)
        dateAfter30days = today+datetime.timedelta(days=30)
        today = today-datetime.timedelta(days=1)
        todayIndex = all_dates.index(today)
        indexAfter15day = all_dates.index(dateAfter15days)
        indexAfter30day = all_dates.index(dateAfter30days)

        textToday =  ["", today.strftime("%d %b")+',<br>Infected : {:,}'.format((I[todayIndex]+R[todayIndex])) + '<br>'\
                      +'Fatal : {:,}<br>Hospitalized : {:,}'.format(R_Fatal[todayIndex-15],Severe_H[todayIndex])]
        barAtToday = plotgraph.Scatter(y=[0, (max(I[days + low_offset:days + high_offset]) + max(R[days + low_offset:days + high_offset])) / 1.5],
                                       x=[T[todayIndex], T[todayIndex]],
                                       mode='lines+text',
                                       showlegend=False,
                                       text=textToday,
                                       textfont_size=12,
                                       line=dict(dash='dash', width=1,color='black'),
                                       textposition="top left", hoverinfo="none")
        data.append(barAtToday)

        textAt15day =  ["", dateAfter15days.strftime("%d %b")+',<br>Infected : {:,}'.format((I[indexAfter15day]+R[indexAfter15day])) + '<br>'\
                      +'Fatal : {:,}<br>Hospitalized : {:,}'.format(R_Fatal[indexAfter15day-15],Severe_H[indexAfter15day])]
        barAt15day = plotgraph.Scatter(y=[0, (max(I[days + low_offset:days + high_offset]) + max(R[days + low_offset:days + high_offset])) / 1.5],
                                       x=[T[indexAfter15day], T[indexAfter15day]],
                                       mode='lines+text',
                                       showlegend=False,
                                       text=textAt15day,
                                       textfont_size=12,
                                       line=dict(dash='dash', width=1,color='black'),
                                       textposition="top left", hoverinfo="none")
        data.append(barAt15day)
        textAt30day = ["", dateAfter30days.strftime("%d %b")+',<br>Infected : {:,}'.format(I[indexAfter30day]+R[indexAfter30day]) + '<br>'\
                    +'Fatal : {:,}<br>Hospitalized : {:,}'.format(R_Fatal[indexAfter30day-15],Severe_H[indexAfter30day])]
        barAt30day = plotgraph.Scatter(y=[0, (max(I[days + low_offset:days + high_offset]) + max(R[days + low_offset:days + high_offset])) / 1.5],
                                       x=[T[indexAfter30day], T[indexAfter30day]],
                                       mode='lines+text',
                                       showlegend=False,
                                       text=textAt30day,
                                       textfont_size=12,
                                       line=dict(dash='dash', width=1, color='black'),
                                       textposition="top left", hoverinfo="none")
        data.append(barAt30day)
        return data