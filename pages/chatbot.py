import streamlit as st
import vertexai
from langchain.chains import GraphCypherQAChain
from langchain.chat_models import ChatOpenAI
from langchain.graphs import Neo4jGraph
from langchain.prompts import PromptTemplate
import os
from google.oauth2 import service_account
from dotenv import load_dotenv

# Initialize the Vertex AI with Google Cloud credentials
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

credentials = service_account.Credentials.from_service_account_file("resumeanz-db0c67277823.json")
vertexai.init(project='resumeanz', credentials=credentials)

# Define the Cypher generation prompt
CYPHER_GENERATION_TEMPLATE = """You are an expert Neo4j Cypher translator who understands the question in english and convert to Cypher strictly based on the Neo4j Schema provided and following the instructions below:
1. Generate Cypher query compatible ONLY for Neo4j Version 5
2. Do not use EXISTS, SIZE keywords in the cypher. Use alias when using the WITH keyword
3. Use only Nodes and relationships mentioned in the schema
4. Always enclose the Cypher output inside 3 backticks
5. Always do a case-insensitive and fuzzy search for any properties related search. Eg: to search for a Company name use `toLower(c.name) contains 'neo4j'`
6. Candidate node is synonymous to Person
7. Always use aliases to refer the node in the query
8. Cypher is NOT SQL. So, do not mix and match the syntaxes

Schema:
{schema}
Samples:
Question: How many expert java developers attend more than one universities?
Answer: MATCH (p:Person)-[:HAS_SKILL]->(s:Skill), (p)-[:HAS_EDUCATION]->(e1:Education), (p)-[:HAS_EDUCATION]->(e2:Education) WHERE toLower(s.name) CONTAINS 'java' AND toLower(s.level) CONTAINS 'expert' AND e1.university <> e2.university RETURN COUNT(DISTINCT p)
Question: Where do most candidates get educated?
Answer: MATCH (p:Person)-[:HAS_EDUCATION]->(e:Education) RETURN e.university, count(e.university) as alumni ORDER BY alumni DESC LIMIT 1
Question: How many people have worked as a Data Scientist in San Francisco?
Answer: MATCH (p:Person)-[:HAS_POSITION]->(pos:Position) WHERE toLower(pos.title) CONTAINS 'data scientist' AND toLower(pos.location) CONTAINS 'san francisco' RETURN COUNT(p)
Question: {question}
Answer:
"""
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)
chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0, model_name='gpt-4'),
    graph=graph, 
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
    return_intermediate_steps=True
)

# Streamlit page setup
st.title('Chatbot for Neo4j Query Generation')

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for message in st.session_state.messages:
    with st.expander(f"{message['role']} says:",expanded=True):
        st.write(message['content'])

# React to user input
user_query = st.text_input("Enter your question:", placeholder="Which people have held a position in London with a start date in 2019?")
if st.button("Generate Cypher Query"):
    if user_query:
        st.session_state.messages.append({"role": "User", "content": user_query})
        result = chain.run(user_query)
        st.session_state.messages.append({"role": "Bot", "content": f"ResumeAnz : {result}"})
        st.experimental_rerun()
    else:
        st.error("Please enter a question to generate the Cypher query.")
