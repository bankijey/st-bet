import streamlit as st
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from supabase import create_client
import os
import json
from datetime import datetime, timezone, timedelta
import pytz



load_dotenv()
url= os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def time_in_past(minutes_past):
    # Get the current time in UTC
    utc_now = datetime.utcnow()
    
    # Convert the current time to GMT (London) timezone
    london_tz = pytz.timezone('Europe/London')
    london_time = pytz.utc.localize(utc_now).astimezone(london_tz)
    
    # Calculate the time 'minutes_past' minutes ago
    past_time = london_time - timedelta(minutes=minutes_past)
    
    # Return the past time as a string
    return past_time.strftime('%Y-%m-%d %H:%M:%S')

def time_difference(datetime_str):
    # Parse the given datetime string as a timezone-aware datetime
    given_time = datetime.fromisoformat(datetime_str)
    
    # Ensure current time is timezone-aware by setting it to UTC
    current_time = datetime.now(timezone.utc)
    
    # Calculate the difference
    delta = given_time - current_time
    
    # Determine if it's in the past or future
    if delta.total_seconds() < 0:
        past_future = "in the past"
        delta = -delta  # Convert to positive for easy calculation
    else:
        past_future = "in the future"
    
    # Extract the difference in days, seconds, hours, and minutes
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    # Build the result string based on the non-zero values
    parts = []
    if days > 0:
        parts.append(f"{days} days")
    if hours > 0:
        parts.append(f"{hours} hours")
    if minutes > 0:
        parts.append(f"{minutes} minutes")
    
    # If no days, hours, or minutes, return "0 minutes"
    if not parts:
        parts.append("0 minutes")
    
    # Combine the parts and add the past/future information
    return f"{', '.join(parts)} {past_future}"

market_translation = {
    'h2h': 'Head to Head',
    'draw_no_bet': "Draw no bet",
    "gg_ng": "Goal or no goal"
}


# Query supabase and create df


@st.cache_data
def get_data(start):
    data = supabase.table('results_v2').select("*").gte("created_at", start).execute().data

    df = pd.DataFrame(data).query('1.005 <= arbitrage <= 1.05').sort_values('start', ignore_index = True, ascending = False)
    return df

def get_eventIds(row):
        eids = ';'.join([o['event_id'] for o in row.market['outcomes']])
        
        return f"{row.market['key']}=={eids}"
    



minutes_past = st.sidebar.number_input('Results from how many minutes ago?:', value = 75, min_value= 75,step = 15)
start = time_in_past(minutes_past=minutes_past)
try:
    df = get_data(start)
    df['eid_key'] = df.apply(lambda row: get_eventIds(row), axis = 1)
    old_len = len(df)
    df = df.drop_duplicates(subset=['arbitrage', 'eid_key'], keep = 'last', ignore_index=True)
     
    st.write(df)
    
    st.write(f"Droped {old_len - len(df)} duplicate(s)")
    
except Exception as e:
    st.write(e)


# Initialize session state variables

if 'index' not in st.session_state:
    st.session_state.index = 0
    
# Display the current row of data
def process_col(col, data):
    if not data['url'].contains('https:'):
        data['url'] = f"https://{data['url']}"
    col.write(f"**Event ID:** {data['event_id']}")
    col.write(f"**Bookmaker:** {data['bookmaker']}")
    col.write(f"**Tournament:** {data['tournament']}")
    col.write(f"**Match:** {data['home_team']} vs {data['away_team']}")
    col.write(f"**Odd:** {data['odd']}")
    col.write(f"[Link]({data['url']})")  # Avoid using links as per the rules
    # return col_data


    
def display_row(index):
    st.header(f"{index+1} of {len(df)}")
    row_data = df.iloc[index]
    
    st.subheader(f"**Start: {row_data['start'].split('+')[0].replace('T', ' ')}: {time_difference(row_data['start'])}**")
    st.markdown(f"*Computed {time_difference(row_data['created_at'])}*")
    
    # st.write(f"{time_difference(row_data['start'])}")
    st.subheader(f"**Market:** {market_translation[row_data['market']['key']]}")
    profit = 100*(row_data['arbitrage'] - 1)
    st.subheader(f"*Profit:* {round(profit, 3)}%")
    
    st.divider()
    outcomes = row_data['market']['outcomes']
    market_keys = [o['market_key'] for o in outcomes]
    odds = [o['odd'] for o in outcomes]
    cols = st.columns(len(outcomes))
    wrongs = [0,0,0]
    
    
    for i, col in enumerate(cols):
        k = market_keys[i]
        
        col_data = outcomes[i]
        
        # col.write(f"**Event ID:** {col_data['event_id']}")
        
        col.subheader(f"**{k.title()}: {col_data['bookmaker']}** ")
        # col.write(k.title())
        col.divider()
        col.subheader(f"{col_data['tournament'].replace(';', ', ')}")
        # col.write(f"**Game:** {col_data['home_team']} vs {col_data['away_team']}")
        col.subheader(f"[{col_data['home_team']} vs {col_data['away_team']}]({col_data['url']})")
        col.write(f"***Odd: {col_data['odd']}***")
        ratio = round(row_data['arbitrage']/col_data['odd'],3)
        col.write(f"**Bet ratio: {ratio}**")
        
        
        wrong = col.checkbox('Wrong match', key= f"1_{index}_{i+1}")
        inactive = col.checkbox('Inactive', key= f"2_{index}_{i+1}")
        actual_odd = col.number_input('Current odd?', key = f"3_{index}_{i+1}", value=col_data['odd'])
        
        if actual_odd != col_data['odd']:
            odds[i] = actual_odd
            new_arb = 1 / sum(1/i for i in odds)
            new_profit = 100*(new_arb - 1)
            if new_profit > 0:
                st.subheader(f"*Current Profit:* {round(new_profit, 3)}%")
            else:
                st.subheader(f"*Cuurent Loss:* {round(new_profit, 3)}%")

        # col.write(f"[Link]({col_data['url']})")  # Avoid using links as per the rules
        # col.divider()

    

# Next button logic
def next_row():
    if st.session_state.index < len(df) - 1:
        st.session_state.index += 1

# Previous button logic
def previous_row():
    if st.session_state.index > 0:
        st.session_state.index -= 1

# Display the current row
display_row(st.session_state.index)

# Disable buttons based on the index
next_button_disabled = st.session_state.index >= len(df) - 1
previous_button_disabled = st.session_state.index == 0
st.divider()
# Create buttons with disabled states
col1, col2, col3 = st.columns(3)

with col1:
    st.button("Previous", on_click=previous_row, disabled=previous_button_disabled)

with col3:
    st.button("Next", on_click=next_row, disabled=next_button_disabled)
