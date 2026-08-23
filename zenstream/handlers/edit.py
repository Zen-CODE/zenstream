import streamlit as st


class EditFile:
    @staticmethod
    def edit_file(file_name: str):
        """Display the file details."""

        st.write(f"Editing file: {file_name}")
