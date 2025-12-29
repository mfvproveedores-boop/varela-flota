import os
import json
from oauth2client.service_account import ServiceAccountCredentials

def get_creds():
    # En Render, guardaremos el JSON completo en una variable de entorno
    json_creds = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if json_creds:
        creds_dict = json.loads(json_creds)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return None