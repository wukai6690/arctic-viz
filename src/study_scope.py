"""Cross-page research choices live independently of ephemeral widget state."""
import streamlit as st
from src.study_data import region_definitions

DEFAULTS={'region':'all','years':(2016,2025),'month':9}

def scope():
    return {key:st.session_state.get('_study_'+key,value) for key,value in DEFAULTS.items()}

def set_scope(**values):
    for key,value in values.items():
        if key in DEFAULTS:st.session_state['_study_'+key]=value
    st.session_state['_study_active']=True

def copy_choice(key,widget):set_scope(**{key:st.session_state[widget]})

def clear_scope():
    for key,value in DEFAULTS.items():st.session_state['_study_'+key]=value
    st.session_state['_study_active']=False
    st.session_state['_study_indicator']='extent'

def indicator():return st.session_state.get('_study_indicator','extent')

def copy_indicator():
    st.session_state['_study_indicator']=st.session_state['study-metric']
    st.session_state['_study_active']=True

def scope_label():
    s=scope();names={'all':'三个试点海区',**{k:v['name'] for k,v in region_definitions().items()}}
    return f"{names[s['region']]} · {s['years'][0]}—{s['years'][1]} · {s['month']} 月"

def controls(prefix='study'):
    current=scope();names={'all':'三个海区对照',**{k:v['name'] for k,v in region_definitions().items()}}
    cols=st.columns([1.1,2,1])
    keys={k:prefix+'-'+k for k in DEFAULTS}
    for k,w in keys.items():st.session_state[w]=current[k]
    cols[0].selectbox('研究海区',list(names),format_func=names.get,key=keys['region'],on_change=copy_choice,args=('region',keys['region']))
    cols[1].slider('比较年份',1979,2026,key=keys['years'],on_change=copy_choice,args=('years',keys['years']))
    cols[2].selectbox('比较月份',list(range(1,13)),format_func=lambda m:f'{m} 月',key=keys['month'],on_change=copy_choice,args=('month',keys['month']))
    return scope()

def open_study(region=None):
    if region:set_scope(region=region)
    st.switch_page('pages/8_区域联动研究.py')

def sidebar_scope():
    if st.session_state.get('_study_active'):
        st.caption('当前研究范围')
        st.write(scope_label())
        st.button('恢复默认研究范围',key='reset-study',on_click=clear_scope)
