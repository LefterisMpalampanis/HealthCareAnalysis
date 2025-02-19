import streamlit as st
import openai
import json
import pandas as pd
from fpdf import FPDF

# Set up OpenAI client
client = openai.OpenAI(api_key=st.secrets["OPEN_API_KEY"])


def get_disease_info(disease_name):
    """
    Queries OpenAI for structured disease information.
    """
    medication_format = '''{
        "name": "",
        "side_effects": ["", "", ""],
        "dosage": ""
    }'''

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"Provide disease info in JSON format with these fields: "
                                          f"'name', 'statistics' {{'total_cases': int, 'recovery_rate': str (%), 'mortality_rate': str (%) }}, "
                                          f"'recovery_options': dict, "
                                          f"'medication': list of {medication_format}. Wrap the JSON in triple backticks."},
            {"role": "user", "content": disease_name}
        ]
    )

    # Extract content safely
    content = response.choices[0].message.content
    json_start = content.find("```") + 3
    json_end = content.rfind("```")
    json_text = content[json_start:json_end].strip() if json_start > 2 and json_end > 0 else content

    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        st.error("Error decoding JSON. Please check API response.")
        return None


def generate_pdf(info):
    """
    Converts the disease information into a structured PDF file.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)

    # Title
    pdf.cell(200, 10, f"{info.get('name', 'Disease Info')}", ln=True, align="C")
    pdf.ln(10)

    # Statistics
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "Statistics", ln=True)
    pdf.set_font("Arial", "", 12)
    stats = info.get("statistics", {})
    pdf.multi_cell(0, 10, f"Total Cases: {stats.get('total_cases', 'N/A')}\n"
                          f"Recovery Rate: {stats.get('recovery_rate', 'N/A')}\n"
                          f"Mortality Rate: {stats.get('mortality_rate', 'N/A')}")
    pdf.ln(5)

    # Recovery Options
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "Recovery Options", ln=True)
    pdf.set_font("Arial", "", 12)
    for option, description in info.get("recovery_options", {}).items():
        pdf.cell(0, 8, f"- {option}", ln=True)
        pdf.multi_cell(0, 8, description)
        pdf.ln(2)

    # Medication
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, "Medication", ln=True)
    pdf.set_font("Arial", "", 12)
    for idx, med in enumerate(info.get("medication", []), start=1):
        pdf.cell(0, 8, f"{idx}. {med.get('name', 'Unknown')}", ln=True)
        pdf.multi_cell(0, 8, f"Dosage: {med.get('dosage', 'N/A')}\n"
                             f"Side Effects: {', '.join(med.get('side_effects', []))}")
        pdf.ln(2)

    return pdf.output(dest="S").encode("latin1")  # Convert to bytes


def display_disease_info(info):
    """
    Displays structured disease information in Streamlit.
    """
    if not info:
        return

    st.write(f"## Statistics for {info.get('name', 'Unknown Disease')}")

    stats = info.get('statistics', {})
    try:
        recovery_rate = float(stats.get("recovery_rate", "0%").strip('%'))
        mortality_rate = float(stats.get("mortality_rate", "0%").strip('%'))

        chart_data = pd.DataFrame({"Recovery Rate": [recovery_rate], "Mortality Rate": [mortality_rate]},
                                  index=["Rate"])
        st.bar_chart(chart_data)
    except ValueError:
        st.error("Invalid percentage values in statistics.")

    st.write("## Recovery Options")
    for option, description in info.get("recovery_options", {}).items():
        st.subheader(option)
        st.write(description)

    st.write("## Medication")
    for idx, med in enumerate(info.get("medication", []), start=1):
        st.subheader(f"{idx}. {med.get('name', 'Unknown')}")
        st.write(f"**Dosage:** {med.get('dosage', 'N/A')}")
        st.write(f"**Side Effects:** {', '.join(med.get('side_effects', []))}")

    # Convert JSON to PDF
    pdf_bytes = generate_pdf(info)

    # Download Button for PDF
    st.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"{info.get('name', 'disease_info')}.pdf",
        mime="application/pdf"
    )


st.title("Disease Information Dashboard")
disease_name = st.text_input("Enter the name of the disease:")
if disease_name:
    disease_info = get_disease_info(disease_name)
    display_disease_info(disease_info)
