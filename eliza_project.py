"""
Streamlit webpage to provide a list of followers and followings on Instagram, as well as
the subtraction of those sets.
Requires downloading the Instagram-provided JSON files.

Requested by Eliza - 7-14-2024.

ToDo:
- How to spread out the columns more: give more space to the df and make the graph not go so far out??
(if you change the columns back to being the df and the graph, instead of stats and df)
- change the hover text on graph to also show date, maybe time
- show multiple lines on same chart?


- refactor process data repeated part?

- Add more info to the "time" column in the df
- Figure out how to expand the df/more visually appealing



- Document the set theory relationship (219 | 403 | 105)



Done:
- Figure out weird caching thing - why does it save data no matter the input?????
    -- had to delete the directory everytime a new file was uploaded. this involved using session state to track the
    current file, and use shutil to remove directory
- add bullet points for initial text if expanding capabilities of website
- Get the error message for inputted files working.
- Possibly a graph of followers v. following over time?????
"""

import streamlit as st
import zipfile
import os
import json
import pandas as pd
from datetime import datetime
from shutil import rmtree
import plotly.express as px


def set_session_state():
    """Initializes global session state variables if not already done."""
    if 'data_processed' not in st.session_state:
        st.session_state.data_processed = False
    if 'current_file' not in st.session_state:
        st.session_state.current_file = ''


def extract_data(file):
    """
    Extracts the zip file (must be in downloads folder) to the local project directory, and returns string of the
    path to the zip folder.
    """
    # zip_folder = f'C:/Users/rjc52/Downloads/{file.name}'
    # extract_location = 'C:/Users/rjc52/PycharmProjects/instagram_projects/current_extract_folder'

    with zipfile.ZipFile(file, 'r') as zip_file:
        zip_file.extractall('extracted_file')

    return 'extracted_file'


def process_data(zip_folder):
    """

    :param zip_folder: path to the zip file downloaded from instagram - must have connections folder
    :return: a dictionary containing 2 dataframes - followers and following, with names and times recorded for each
    """
    followers_list, following_list = [], []

    followers_path = os.path.join(zip_folder, 'connections/followers_and_following/followers_1.json')
    following_path = os.path.join(zip_folder, 'connections/followers_and_following/following.json')

    # Ensures that both files exist in the folder before opening and parsing
    if not (os.path.isfile(followers_path) and os.path.isfile(following_path)):
        st.write(f':red[Error: necessary files not found in folder.]')
        return None
    else:
        with open(followers_path, 'r') as followers_file_object:
            # The followers file contains 1 list of dictionaries, where each dict contains data about each follower
            # I simply loop through the list and grab the name and timestamp for each follower
            followers_json_data = json.load(followers_file_object)
            for dictionary in followers_json_data:
                # OLD JSON FORMAT
                # name = dictionary['['string_list_data'][0]['value']']
                # NEW JSON FORMAT
                name = dictionary['title']
                timestamp = dictionary['string_list_data'][0]['timestamp']
                datetime_object = datetime.fromtimestamp(timestamp)
                # Appends retrieved data to master dictionary
                followers_list.append([name, datetime_object])
            followers_df = pd.DataFrame(followers_list, columns=['Name', 'Time'])

    # Repeats same process with following. Could refactor both into one function called twice, but would have to catch
    # the extra dict index of 'relationships_following' for the following file
        with open(following_path, 'r') as followers_file_object:
            followers_json_data = json.load(followers_file_object)
            for dictionary in followers_json_data['relationships_following']:
                # OLD JSON FORMAT
                # name = dictionary['['string_list_data'][0]['value']']
                # NEW JSON FORMAT
                name = dictionary['title']
                timestamp = dictionary['string_list_data'][0]['timestamp']
                datetime_object = datetime.fromtimestamp(timestamp)
                # Appends retrieved data to master dictionary
                following_list.append([name, datetime_object])
            following_df = pd.DataFrame(following_list, columns=['name', 'time'])

    df_dict = {'followers': followers_df, 'following': following_df}
    return df_dict


def get_set_differences(df1, df2):
    """
    Creates a df containing everything in df1 that is not in df2 (can be thought of as the
    subtraction of the two sets).

    Takes two dataframes as input and returns a dataframe containing the set difference of df1-df2.
    """

    df2_names_list = []
    for row in df2.itertuples():
        # Starts at 1 because 0 is just index; 1 is the name
        df2_names_list.append(row[1])

    new_df_rows_list = []

    for row in df1.itertuples():
        if row[1] not in df2_names_list:
            new_df_rows_list.append(row[1:])

    return pd.DataFrame(new_df_rows_list, columns=['name', 'time'])


def display_page_setup():
    """Configures page and displays initial text. Returns the selected file object to be used in main method."""
    st.set_page_config(page_title='Instagram Analysis', page_icon='📊')
    st.write('# Instagram Analysis Tool 📊')
    st.write('This page provides several tools for analyzing your Instagram data, including:')
    st.write('- Basic stats about your follower and following counts')
    st.write('- Lists of your followers and following accounts')
    st.write('- Lists of people who don\'t follow you back and vice versa')
    st.write('To begin, go to your Instagram settings, search "download your information", and make sure you select '
             '"followers" and "following" in the connections section.')
    st.write('Once it is downloaded, upload the ZIP file here.')

    uploaded_file = st.file_uploader('Choose a file', label_visibility='hidden')
    return uploaded_file


def display_stats():
    st.write('#### Stats:')
    num_followers = len(dataframes_dict['followers'])
    num_following = len(dataframes_dict['following'])
    # This could also be calculated by doing followers - len of the other dataframe
    num_mutuals = num_following - len(dataframes_dict['accounts you follow that don\'t follow back'])
    st.write(f'Total followers: {num_followers}')
    st.write(f'Total following: {num_following}')
    st.write(f'\# of mutual followers: {num_mutuals}')
    st.write(f'\# of following who don\'t follow you back: {num_following - num_mutuals}')
    st.write(f'\# of followers you don\'t follow back: {num_followers - num_mutuals}')


def get_graph_data(dfs_dict):
    """
    Takes a dictionary of data frames as input, goes through each df, and returns a dict
    with corresponding keys each pointing now to another dict containing x: all timestamp,
    and y: # of followers at that point.
    """
    graph_data_dict = {}
    for key, current_df in dfs_dict.items():
        # Uses .iloc to grab all rows in the second (index 1) column, reversing them to get
        # time moving forwards
        timestamps = current_df.iloc[::-1, 1]
        # In this case, getting the y vals (num of followers at each timestamp) is easy -
        # the nature of the data means it just increments by one each timestamp, so a list of indices
        # + 1 (I chose to measure followers at the end of each day - you have 1 the day you get your first follower...)
        num_followers_at_curr_time = list(range(1, len(current_df)+1))
        graph_data_dict[key] = {'x': timestamps, 'y': num_followers_at_curr_time}
    return graph_data_dict


# Driver Code
if __name__ == '__main__':
    set_session_state()
    uploaded_file = display_page_setup()

    if uploaded_file is not None:
        instagram_data_folder = extract_data(uploaded_file)
        # Gets a dictionary of dataframes each containing info about followers and following
        dataframes_dict = process_data(instagram_data_folder)
        if dataframes_dict is not None:
            st.session_state.data_processed = True
            st.session_state.current_file = instagram_data_folder
            # Gets the set differences (followers you don't follow back and vice versa), adds to the dict of dfs,
            # and creates a selectbox with all 4 dataframes
            dataframes_dict['accounts you follow that don\'t follow back'] = get_set_differences(
                dataframes_dict['following'], dataframes_dict['followers']
            )

            dataframes_dict['accounts who follow you that you don\'t follow back'] = get_set_differences(
                dataframes_dict['followers'], dataframes_dict['following']
            )

            st.divider()

            selected_key = st.selectbox(label='Select an option to display', options=dataframes_dict)
            # Displays selected dataframe - the initial purpose of this project (just to see a list of all followers..)
            selected_df = dataframes_dict[selected_key]

            col1, col2 = st.columns(2)
            with col1:
                display_stats()

            with col2:
                st.dataframe(selected_df)
            line_chart_data_dict = get_graph_data(dataframes_dict)
            plotly_chart = px.scatter(line_chart_data_dict[selected_key], x='x', y='y',
                                   title=f'# of {selected_key}, over time')
            plotly_chart.update_layout(xaxis_title='Date',
                                       yaxis_title='# of followers/following')
            st.plotly_chart(plotly_chart)

    else:
        # If there was a file but it was cleared, delete the directory and reset the session state variables
        if st.session_state.data_processed:
            rmtree(st.session_state.current_file)
            st.session_state.data_processed = False
            st.session_state.current_file = ''
