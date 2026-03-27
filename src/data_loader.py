import pandas as pd
import os
import streamlit as st


def load_user_data(user_name):
    file_mapping = {"Michi": "michell.csv", "Henning": "henning.csv", "Nils": "nils.csv"}
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, "data", file_mapping[user_name])

    if os.path.exists(file_path):
        data = pd.read_csv(file_path, sep=None, engine='python')
        data.columns = data.columns.str.strip()
        if 'person' in data.columns:
            data = data.rename(columns={'person': 'User'})
        data['date'] = pd.to_datetime(data['date'])

        rows = []
        for _, r in data.iterrows():
            for i in range(1, 4):
                app_n = r.get(f'app{i}_name')
                app_m = r.get(f'app{i}_minutes')
                if pd.notna(app_n):
                    rows.append({
                        'date': r['date'], 'User': user_name,
                        'total_minutes': r['total_minutes'],
                        'App': app_n, 'Minutes': app_m
                    })
        return pd.DataFrame(rows), data
    return pd.DataFrame(), pd.DataFrame()