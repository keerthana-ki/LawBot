import streamlit as st
from model_utils import classify_case, get_similar_ipc_sections, generate_summary
import fitz  # PyMuPDF

st.set_page_config(page_title="Legal Chatbot", layout="centered")
st.title("Lawbot")

# PDF/Text input
uploaded_file = st.file_uploader("Upload a PDF (optional)", type=["pdf"])
text_input = st.text_area("Or enter the legal case description", height=200)

def extract_text_from_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Handle input
description = ""
if uploaded_file:
    try:
        description = extract_text_from_pdf(uploaded_file)
        st.success("PDF text extracted successfully!")
        with st.expander("Preview extracted text"):
            st.write(description[:1000] + "...")
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
else:
    description = text_input

# Analysis section
if st.button("Analyze Case") and description.strip():
    with st.spinner("Analyzing case..."):
        case_type, scores = classify_case(description)
        ipc_matches = get_similar_ipc_sections(description)
        summary = generate_summary(description)

    st.success("Analysis Complete!")
    
    st.markdown("### Case Summary")
    st.write(summary)
    
    st.markdown(f"### Predicted Case Type: {case_type.capitalize()}")
    
    st.markdown("#### Confidence Scores")
    st.bar_chart(scores)
    
    st.markdown("#### Relevant IPC Sections")
    for match in ipc_matches:
        st.markdown(f"- {match}")
    
    # Download results
    results = f"Case Summary:\n{summary}\n\nPredicted Case Type: {case_type}\n\nIPC Sections:\n" + "\n".join(ipc_matches)
    st.download_button(
        "Download Full Report",
        data=results,
        file_name="legal_analysis_report.txt",
        mime="text/plain"
    )