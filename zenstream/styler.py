from uuid import uuid4

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

NUM_COLUMNS = 5


class Styler:
    @staticmethod
    def show_dict(subheader: str, data: dict):
        formatted_data = {f":blue[{k.title()}]": v for k, v in data.items()}
        final_data = {
            f":yellow[{subheader}]": list(formatted_data.keys()),
            "🟢": list(formatted_data.values()),
        }

        st.table(final_data, border="horizontal")

    @staticmethod
    def add_button(
        container: DeltaGenerator,
        text: str,
        icon: str,
        on_click: callable,
        **kwargs,
    ):
        width = kwargs.pop("width", "stretch")
        with container:
            st.button(
                text,
                icon=icon,
                on_click=on_click,
                width=width,
                key=str(uuid4()),
                **kwargs,
            )

    @staticmethod
    def add_link_button(
        container: DeltaGenerator,
        text: str,
        icon: str,
        link: str,
    ):
        with container:
            st.link_button(text, link, icon=icon, width="stretch", key=str(uuid4()))

    @staticmethod
    def show_dataframe(text: str, df: pd.DataFrame):
        st.subheader(text)
        st.data_editor(df, num_rows="dynamic", key=f"pdf_dataframe_{uuid4()}")
        with st.expander(text + " - analysis"):
            col1, col2 = st.columns(2)
            try:
                with col1:
                    st.markdown("**Area Chart**")
                    st.area_chart(df)
                    st.markdown("**Bar Chart**")
                    st.bar_chart(df)
                with col2:
                    st.markdown("**Line Chart**")
                    st.line_chart(df)
            except Exception as e:
                with col1:
                    st.error(f"The DataFrame could not be graphed. Error: {e}")
