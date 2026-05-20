import streamlit as st
import pandas as pd
import plotly.express as px

def plot_score_trend(prog_data):
    if not prog_data:
        return
    df_prog = pd.DataFrame(prog_data)
    fig_line = px.line(df_prog, x='question_number', y='score',
                       title="Score per Question",
                       labels={'question_number':'Question #','score':'Score'},
                       markers=True)
    fig_line.update_traces(line_color='#667eea', line_width=3, marker_size=8)
    fig_line.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)', 
        yaxis_range=[0,10],
        font=dict(color="#64748b")
    )
    st.plotly_chart(fig_line, use_container_width=True)

def plot_topic_performance(topic_dict):
    if not topic_dict:
        return
    topic_data = [
        {"Topic": t.title(), "Score": d['average_score'],
         "Questions": d['questions_attempted'], "Level": d['level'].title()}
        for t, d in topic_dict.items()
    ]
    df_topics = pd.DataFrame(topic_data)
    fig_bar = px.bar(df_topics, x='Topic', y='Score',
                     color='Score',
                     color_continuous_scale=['#ef4444','#f59e0b','#10b981'],
                     title="Average Score per Topic", text='Score')
    fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_bar.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis_range=[0, 10],
        font=dict(color="#64748b")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

def plot_difficulty_breakdown(diff_data):
    if not diff_data:
        return
    df_diff = pd.DataFrame([
        {"Difficulty": d.title(), "Score": v['average_score'], "Qs": v['questions_attempted']}
        for d, v in diff_data.items()
    ])
    fig_diff = px.bar(df_diff, x='Difficulty', y='Score',
                      color='Score',
                      color_continuous_scale=['#ef4444','#f59e0b','#10b981'],
                      title="Performance by Difficulty", text='Score')
    fig_diff.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_diff.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis_range=[0,10],
        font=dict(color="#64748b")
    )
    st.plotly_chart(fig_diff, use_container_width=True)
