import streamlit as st

# Set page config to use the custom logo and set a title
st.set_page_config(
    page_title="ResumeAnz",
    page_icon="resumeanz.png",  # Update this to the path where the logo is saved
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    st.title("Welcome to ResumeAnz")
    st.header("Revolutionizing the Recruitment Process")
    
    st.image("resumeanz.png", width=200)  # Show the logo on the page
    
    st.markdown("""
    ## Features
    - **Advanced Candidate Matching**: Automatically match candidates to job descriptions.
    - **Interactive Recruitment Assistant**: Get answers to your recruitment questions instantly.
    
    ## Benefits
    - **Efficiency**: Streamline your hiring process.
    - **Accuracy**: Find the best candidates for the job.
    
    ## Contact Us
    For more information, please [visit our website](#) or contact us at info@resumeanz.com.
    """)
    
    st.sidebar.info("Explore the functionalities using the sidebar options.")
    st.sidebar.success("Start by inputting your job description or candidate inquiry.")

if __name__ == "__main__":
    main()
