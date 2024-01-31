from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai 
import fitz
from Node_rel import create_nodes_from_json
from py2neo import Graph, Node, Relationship
import json
import re
from Node_rel import create_nodes_from_json, create_nodes_and_relationships

from py2neo import Graph, Node
# Button to trigger audio recording

graph = Graph("bolt://localhost:7687", auth=("neo4j", "Pratikps1$"))


global id_counter
id_counter=0 

def find_largest_id():
    query = """
    MATCH (n:Person)
    RETURN n.id AS name
    """
    result = graph.run(query).data()

    ids = [int(entry['name'].replace('person', '')) for entry in result if entry['name'].startswith('person')]

    if ids:
        max_id = max(ids)
        return  max_id
    else:
        print("No IDs found in the data.")


genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))

#func to load gemini pro vision
model = genai.GenerativeModel('gemini-pro-vision')

def gemini_get_response(input, image, prompt):
    response = model.generate_content([input, image[0], prompt])  # in gemini, it takes parameters in a list
    return response.text

def input_image_details(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        image_parts = [{'mime_type': uploaded_file.type, "data": bytes_data}]
        return image_parts
    else:
        raise FileNotFoundError("No File Uploaded")

st.set_page_config(page_title='MultiLanguage Invoice Extractor')
st.header('Neo4j Graph Creator')





input_prompt = st.text_input('Input Prompt', key='input')
uploaded_file = st.file_uploader('Choose an image or PDF of invoice...', type=["jpg", "jpeg", "png", "pdf","txt"])
image = None  # Initialize the variable outside the conditional block

if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        # If the uploaded file is a PDF, convert it to an image
        pdf_file = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        page = pdf_file.load_page(0)
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    elif uploaded_file.type == "text/plain":
        # If the uploaded file is a text file (.txt), convert it to an image
        text_content = uploaded_file.read().decode("latin-1")
        
        # Set up the image with a white background
        image = Image.new("RGB", (800, 600), "white")
        draw = ImageDraw.Draw(image)
        
        # Choose a font and size
        font = ImageFont.load_default()
        
        # Set up text position and color
        text_position = (50, 50)
        text_color = "black"
        
        # Draw the text on the image
        draw.text(text_position, text_content, font=font, fill=text_color)
    else:
        # If the uploaded file is an image, open it directly
        image = Image.open(uploaded_file)

    st.image(image, caption='Uploaded Image.', use_column_width=True)

submit1= st.button("Person")
submit2= st.button("Position")
submit3= st.button("Skill")
submit4= st.button("Education")




inputss="""you are an expert at analysing images and getting text from the images"""
input_prompt1 = """
From the Resume text for a job aspirant below, extract Entities strictly as instructed below
1. First, look for the Person Entity type in the text and extract the needed information defined below:
   `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. NEVER create new entity types that aren't mentioned below. Document must be summarized and stored inside Person entity under `description` property
    Entity Types:
    label:'Person',id:string,role:string,description:string //Person Node
2. Description property should be a crisp text summary and MUST NOT be more than 100 characters
3. If you cannot find any information on the entities & relationships above, it is okay to return empty value. DO NOT create fictious data
4. Do NOT create duplicate entities or properties 
5. Restrict yourself to extract only Person information. No Position, Company, Education or Skill information should be focussed.
6. NEVER Impute missing values
Output JSON (Strict):
{"entities": [{"label":"Person","id":"person1","role":"Prompt Developer","description":"Prompt Developer with more than 30 years of LLM experience"}]}

Question: Now, extract the Person for the text below -
$ctext

Answer:

"""

input_prompt2 = """From the Resume text for a job aspirant below, extract Entities & relationships strictly as instructed below
1. First, look for Position & Company types in the text and extract information in comma-separated format. Position Entity denotes the Person's previous or current job. Company node is the Company where they held that position.
   `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. NEVER create new entity types that aren't mentioned below. You will have to generate as many entities as needed as per the types below:
    Entity Types:
    label:'Position',id:string,title:string,location:string,startDate:string,endDate:string,url:string //Position Node
    label:'Company',id:string,name:string //Company Node
2.parent_ID: should be the id same as that of id of from Person JSON
3. Next generate each relationships as triples of head, relationship and tail. To refer the head and tail entity, use their respective `id` property. NEVER create new Relationship types that aren't mentioned below:
    Relationship definition:
    position|AT_COMPANY|company //Ensure this is a string in the generated output
4. If you cannot find any information on the entities & relationships above, it is okay to return empty value. DO NOT create fictious data
5. Do NOT create duplicate entities or properties. 
6. No Education or Skill information should be extracted.
7. DO NOT MISS out any Position or Company related information
8. NEVER Impute missing values
Output JSON (Strict):
{"entities": [{"label":"Position","id":"position1","parent_id":"person1","title":"Software Engineer","location":"Singapore","startDate":"2021-01-01","endDate":"present"},{"label":"Position","id":"position2","parent_id":"person1","title":"Senior Software Engineer","location":"Mars","startDate":"2020-01-01","endDate":"2020-12-31"},{"label":"Company","id":"company1","name":"Neo4j Singapore Pte Ltd"},{"label":"Company","id":"company2","name":"Neo4j Mars Inc"}],"relationships": ["position1|AT_COMPANY|company1","position2|AT_COMPANY|company2"]}

Question: Now, extract entities & relationships as mentioned above for the text below -
$ctext

Answer:
"""

input_prompt3 = """From the Resume text below, extract Entities strictly as instructed below
1. Look for prominent Skill Entities in the text. The`id` property of each entity must be alphanumeric and must be unique among the entities. NEVER create new entity types that aren't mentioned below:
    Entity Definition:
    label:'Skill',id:string,name:string,level:string //Skill Node
2.parent_ID: should be the id same as that of id of from Person JSON
3. NEVER Impute missing values
4. If you do not find any level information: assume it as `expert` if the experience in that skill is more than 5 years, `intermediate` for 2-5 years and `beginner` otherwise.
Output JSON (Strict):
{"entities": [{"label":"Skill","id":"skill1","parent_id":"person1","name":"Neo4j","level":"expert"},{"label":"Skill","id":"skill2","parent_id":"person1","name":"Pytorch","level":"expert"}]}

Question: Now, extract entities as mentioned above for the text below -
$ctext

Answer:
"""

input_prompt4 = """From the Resume text for a job aspirant below, extract Entities strictly as instructed below
1. Look for Education entity type and generate the information defined below:
   `id` property of each entity must be alphanumeric and must be unique among the entities. You will be referring this property to define the relationship between entities. NEVER create other entity types that aren't mentioned below. You will have to generate as many entities as needed as per the types below:
    Entity Definition:
    label:'Education',id:string,degree:string,university:string,graduationDate:string,score:string,url:string //Education Node
2.parent_ID: should be the id same as that of id of from Person JSON
3. If you cannot find any information on the entities above, it is okay to return empty value. DO NOT create fictious data
4. Do NOT create duplicate entities or properties
5. Strictly extract only Education. No Skill or other Entities should be extracted
6. DO NOT MISS out any Education related entity
7. NEVER Impute missing values
Output JSON (Strict):
{"entities": [{"label":"Education","id":"education1","parent_id":"person1","degree":"Bachelor of Science","graduationDate":"May 2022","score":"0.0"}]}

Question: Now, extract Education information as mentioned above for the text below -
$ctext

Answer:
"""
uri = "bolt://localhost:7687"
username = "neo4j"
password = "Pratikps1$"
graph = Graph(uri, auth=(username, password))






if submit1:
    if image is not None:  # Check if the image is defined
        
        image_data = input_image_details(uploaded_file)
        response = gemini_get_response(inputss, image_data, input_prompt1)
        st.subheader('The Response is')
        st.write(response)
        json_like_string =response

        # Extracting the relevant information using string manipulation
        start_index = response.find('{')
        end_index = response.rfind('}') + 1

        # Extract the JSON substring
        json_part = response[start_index:end_index]
        json_data = json.loads(json_part)
        lrg_id = find_largest_id()
        #print(lrg_id)
        id_counter= lrg_id+1
        json_data["entities"][0]["id"]="person"+str(id_counter)
        #st.write(json_data["entities"][0]["id"])
        create_nodes_from_json(json_data)
        
        

        # Convert it back to a formatted JSON string with indentation
        #formatted_json = json.dumps(response, indent=2)

        #print(formatted_json)
        #create_nodes_from_json(formatted_json)
        #st.write("Person Nodes created successfully.")
        #create_nodes_and_relationships(response, graph)
elif submit2:
    if image is not None:  # Check if the image is defined
        image_data = input_image_details(uploaded_file)
        response = gemini_get_response(inputss, image_data, input_prompt2)
        st.subheader('The Response is')
        st.write(response)
        start_index = response.find('{')
        end_index = response.rfind('}') + 1

        # Extract the JSON substring
        json_part = response[start_index:end_index]
        json_data = json.loads(json_part)
        print(id_counter)
        #create_nodes_and_relationships(json_data)
        


        # Given JSON-like string


        # Printing keys and values
        # Use regex to extract content between the first { and the last }

        

        # Now 'json_data' contains the extracted JSON object
        #print(json_data)
        
        #json_data = json.loads(json_string)

        # Convert it back to a formatted JSON string with indentation
        #formatted_json = json.dumps(json_data, indent=2)

        #print(formatted_json)
        #create_nodes_from_json(formatted_json)
        #create_nodes_and_relationships()
        #create_nodes_and_relationships(response, graph)
elif submit3:
    if image is not None:  # Check if the image is defined
        image_data = input_image_details(uploaded_file)
        response = gemini_get_response(inputss, image_data, input_prompt3)
        st.subheader('The Response is')
        st.write(response)
        #create_nodes_and_relationships(response, graph)
elif submit4:
    if image is not None:  # Check if the image is defined
        image_data = input_image_details(uploaded_file)
        response = gemini_get_response(inputss, image_data, input_prompt4)
        st.subheader('The Response is')
        st.write(response)
        
    else:
        st.warning("Please upload a valid image or PDF file.")



