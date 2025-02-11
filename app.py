import streamlit as st
from utils import validate_email_address
import streamlit.components.v1 as components
import os
import time  # Import time module to track execution time

def load_css():
    """Load custom CSS for styling"""
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
            <p>Check if an email address is active before sending a message.</p>
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
            start_time = time.time()  # Start time tracking

            results = validate_email_address(email)

            end_time = time.time()  # End time tracking
            elapsed_time = round(end_time - start_time, 2)  # Calculate execution time

            st.subheader("Validation Results:")

            # **1️⃣ Format Check**
            if results["format"]["status"] == "Success":
                st.success("✅ The email address is correctly formatted.")
            else:
                st.error("❌ The email address format is incorrect. Please check for typos.")
                st.stop()  # **Exit early—no need to check MX or SMTP.**

            # **2️⃣ DNS Check (MX Records)**
            if results["dns"]["status"] == "Success":
                st.success("✅ This domain can receive emails.")
            elif results["dns"]["status"] == "Timeout":
                st.warning("⏳ We couldn't verify the domain at this time. Please try again later.")
            else:
                st.error("⚠️ The domain may not be able to receive emails.")
                st.stop()  # **Exit early—no need to check SMTP.**

            # **3️⃣ SMTP Check (Mailbox Exists)**
            if results["smtp"]["status"] == "Success":
                st.success(f"✅ {results['smtp']['message']}")
            elif results["smtp"]["status"] == "Warning":
                st.warning(f"⚠️ {results['smtp']['message']}")
            elif results["smtp"]["status"] == "Timeout":
                st.warning("⏳ We couldn't verify if the email is active. Please try again later.")
            else:
                st.error(f"⚠️ {results['smtp']['message']}")

            # **4️⃣ Display time taken for validation**
            st.markdown(f"⏱ **Time Taken:** {elapsed_time} seconds")

        else:
            st.warning("⚠️ Please enter an email address.")

    # Middle ad
    display_ad("middle")

    # Additional information
    with st.expander("What we check"):
        st.markdown("""
        - ✅ Email format validation
        - ✅ Domain existence
        - ✅ Mail server (MX record) verification
        - ✅ Common typo detection
        - ✅ SMTP verification (checking if the email is active)
        """)

    # Bottom ad
    display_ad("bottom")

if __name__ == "__main__":
    main()
