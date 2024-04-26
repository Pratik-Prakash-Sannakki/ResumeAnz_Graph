import streamlit as st
from openai import OpenAI
from neo4j import GraphDatabase
import pandas as pd
import os
from dotenv import load_dotenv

# Initialize the Vertex AI with Google Cloud credentials
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USER')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
def generate_openai_embeddings(text):
    # Connect to OpenAI API
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        encoding_format="float"
    )
    return response.data[0].embedding

def find_similar_nodes(description_embedding):
    # Connect to Neo4j database
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    # Define Cypher query to find similar nodes
    query = """
    CALL db.index.vector.queryNodes('jobMatch', 6, $embedding)
    YIELD node, score
    RETURN node.id AS id, score
    ORDER BY score DESC
    """

    # Execute the query
    similar_node_ids = []
    with driver.session() as session:
        result = session.run(query, embedding=description_embedding)
        for record in result:
            similar_node_ids.append(record["id"])

    # Define Cypher query to get person descriptions and skills for similar nodes
    skill_query = """
    MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
    WHERE p.id IN $similar_node_ids
    RETURN p.id AS person_id, p.description AS person_description, collect(s.id) AS skill_ids, collect(s.description) AS skill_descriptions
    """

    # Execute the skill query and collect the results
    skill_info = []
    with driver.session() as session:
        result = session.run(skill_query, similar_node_ids=similar_node_ids)
        for record in result:
            skill_info.append({
                "person_id": record["person_id"],
                "person_description": record["person_description"],
                "skill_ids": record["skill_ids"],
                "skill_descriptions": record["skill_descriptions"]
            })

    # Close the Neo4j driver
    driver.close()

    return similar_node_ids, skill_info

def get_summary(content):
    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Summarize content Give in 1 line and max 20 words"
            },
            {
                "role": "user",
                "content": content
            }
        ],
        temperature=0,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    summary = response.choices[0].message.content.strip()
    return summary



# Streamlit app
st.title("Job Description - Candidate Matcher")

# Get job description input
job_description = st.text_area("Enter job description:")

if st.button("Best Candidate Match"):
    # Generate OpenAI embedding
    embedding = generate_openai_embeddings(job_description)

    # Find similar nodes and their skill information
    similar_node_ids, skill_info = find_similar_nodes(embedding)

    # Display similar job IDs
    st.write("Matched Candidates IDs: ", ", ".join(map(str, similar_node_ids)))

    # Display person and skill information in a dropdown table
    st.subheader("Matched Candidates :")
    with st.expander("Expand to see details associated with these candidates"):
        data = []
        for info in skill_info:
            # Use GPT-4 to summarize the person description
            summary = get_summary(info["person_description"])
            data.append({
                "Person ID": info["person_id"],
                "Person Description": summary,
                "Skills": ", ".join(map(str, info["skill_ids"]))
            })
        df = pd.DataFrame(data)
        st.table(df)




