"""Small, explicit joins between place, project and source records."""
import json
from src.presentation import ROOT

def research_catalog():
    return json.loads((ROOT/'data/reference/research.json').read_text(encoding='utf-8'))

def project_media():
    return json.loads((ROOT/'data/reference/project_media.json').read_text(encoding='utf-8'))

def place_category(place):
    if place.get('category'):return place['category']
    if place['id']=='bering':return '港口与航道'
    if place['id']=='pituffik':return '空间设施'
    if place['id'] in ['greenland','kola']:return '自然区域'
    return '城市与聚落'

def place_region(place):
    return {'bering':'阿拉斯加','rauma':'北欧','greenland':'格陵兰','kullorsuaq':'格陵兰','kiruna':'北欧','nuuk':'格陵兰','pituffik':'格陵兰','narvik':'北欧','kola':'俄罗斯北部'}.get(place['id'],place['region'])

def projects_for_place(pid):
    return [p for p in research_catalog()['projects'] if pid in p['place_ids']]

def open_place(pid):
    import streamlit as st
    st.session_state['_atlas_pending_place']=pid
    st.switch_page('pages/1_北极全景地图.py')

def open_project(pid):
    import streamlit as st
    st.session_state['_project_pending']=pid
    st.switch_page('pages/4_极地核心技术.py')

def valid_events(place,catalog,data):
    def valid(e):
        return not any(e['location']==r['location'] and (not r['url_contains'] or r['url_contains'] in (e.get('source_url') or '')) for r in catalog['excluded_matches'])
    return [e for e in data['events'] if e['location'] in place.get('aliases',[]) and valid(e)]
