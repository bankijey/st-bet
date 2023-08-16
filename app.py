import streamlit as st 
import pandas as pd
import numpy as np
import json
import datetime

def convert_unix_timestamp(unix_timestamp):
    timestamp = datetime.datetime.fromtimestamp(unix_timestamp)
    date = timestamp.strftime('%d-%m-%Y')
    time = timestamp.strftime('%H:%M')
    return [date, time]


# SIDEBAR
st.sidebar.write("Input values")
file = st.sidebar.file_uploader('Select bet data file:')

data = json.load(file)
dates = list(data.keys())
markets = list(data[dates[0]].keys())

new_data = {}
for date in dates:
    x2_data = data[date]['1x2']['categories'][0]['competitions']
    for i, competition in enumerate(x2_data):
        # st.write(competition)
        for j, event in enumerate(competition['events']):
            # st.write(event)
            for markt in markets[1:]:
                # st.write(markt)
                try:
                    event['markets'].append(data[date][markt]['categories'][0]['competitions'][i]["events"][j]['markets'][0])
                except:
                    pass
    
    new_data[date] = x2_data

select_date = st.sidebar.selectbox('Dates', dates, 0)
st.header(select_date)
dat_data = new_data[select_date]

competitions = []
for competition in dat_data:
    competitions.append(competition['name'])
    
select_competition = st.sidebar.selectbox('Competitions', competitions, 0)

compIdx = competitions.index(select_competition)
compEvents = dat_data[compIdx]['events']
st.subheader(select_competition)
# st.write(compEvents)
dfData = {
    "start":[],
    "home":[],
    "away":[],
    "1":[],
    "X":[],
    "2":[],
    # "Over":[],
    # "Under":[],
    # "hand":[]
}
for event in compEvents:
    dfData["home"].append(event["eventNames"][0])
    dfData["away"].append(event["eventNames"][1])
    dfData["start"].append(event["startTime"])
    dfData["1"].append(float(event['markets'][0]["outcomes"][0]["value"]))
    dfData["X"].append(float(event['markets'][0]["outcomes"][1]["value"]))
    dfData["2"].append(float(event['markets'][0]["outcomes"][2]["value"]))
    
# st.subheader("out Data")
df = pd.DataFrame(data = dfData)
df['start'] = pd.to_datetime(df['start'] // 1000, unit='s')
df['start'] = df['start'].dt.strftime('%d-%m-%Y %H:%M')
st.write(df)