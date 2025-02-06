import streamlit as st
from utils import validate_email_address
import streamlit.components.v1 as components
import os

def load_css():
    with open("style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_ad(position: str):
    """Display a placeholder for advertisement"""
    st.markdown(f"""
        <div class="ad-container">
            <p style="text-align: center;">Advertisement Space ({position})</p>
        </div>
    """, unsafe_allow_html=True)

def serve_ads_txt():
    """Serve the ads.txt file content"""
    if st.query_params.get("serve") == "ads.txt":
        with open("ads.txt", "r") as f:
            st.text(f.read())
        st.stop()

def main():
    # Serve ads.txt if requested
    serve_ads_txt()

    # Load custom CSS
    load_css()

    # Header
    st.markdown(
        """
        <div class="header-container">
            <h1>✉️ Email Validator</h1>
            <p>Check if your email address is valid and deliverable</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Top ad
    display_ad("top")

    # Email input
    email = st.text_input("Enter email address:", key="email_input")

    # Validation button
    if st.button("Validate Email"):
        if email:
            is_valid, message = validate_email_address(email)

            if is_valid:
                st.markdown(
                    f"""
                    <div class="validation-result success">
                        ✅ {message}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="validation-result error">
                        ❌ {message}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.warning("Please enter an email address")

    # Middle ad
    display_ad("middle")

    # Additional information
    with st.expander("What we check"):
        st.markdown("""
        - ✓ Email format validation
        - ✓ Domain existence
        - ✓ Mail server (MX record) verification
        - ✓ Common typo detection
        - ✓ Syntax verification
        """)

    # Bottom ad
    display_ad("bottom")

if __name__ == "__main__":
    main()