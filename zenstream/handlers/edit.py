import streamlit as st


class EditFile:
    @staticmethod
    def _load_text(file_name: str) -> str:
        """Load the file content into a string and return it."""
        try:
            with open(file_name, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            st.warning(f"Unable to read the file...({e})")

        return ""

    @staticmethod
    def _save_text(file_name: str, text_area: str):
        """Save the text to the file."""
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(text_area)
            st.success("File saved successfully!")
        except Exception as e:
            st.warning(f"Unable to save the file...({e})")

    @staticmethod
    def edit_file(file_name: str):
        """Display the file details."""

        text = EditFile._load_text(file_name)

        text_area = st.text_area("Notes", value=text, height=600)

        st.button("Save", on_click=lambda: EditFile._save_text(file_name, text_area))
