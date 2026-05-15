import plotly.express as px
import streamlit as st


def render_line_chart(dataframe, x_column: str, y_column: str, title: str) -> None:
    figure = px.line(dataframe, x=x_column, y=y_column, title=title)
    figure.update_layout(margin=dict(l=16, r=16, t=48, b=16))
    st.plotly_chart(figure, use_container_width=True)


def render_bar_chart(dataframe, x_column: str, y_column: str, title: str) -> None:
    figure = px.bar(dataframe, x=x_column, y=y_column, title=title)
    figure.update_layout(margin=dict(l=16, r=16, t=48, b=16))
    st.plotly_chart(figure, use_container_width=True)
