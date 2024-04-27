from diagrams import Diagram, Cluster, Edge
from diagrams.gcp.compute import ComputeEngine as GCE
from diagrams.gcp.devtools import SDK
from diagrams.azure.identity import Users
from diagrams.custom import Custom
from diagrams.onprem.database import Neo4J

with Diagram("ResumeAnz Architecture", show=False, direction="LR"):
    with Cluster("Cloud Infrastructure"):
        # User interface
        with Cluster("User Interface"):
            streamlit = Custom("Streamlit Application", "./streamlit.jpeg")

        # AI Processing with VertexAI
        with Cluster("AI Processing"):
            gpt4 = Custom("LLM GPT-4", "./GPT-4.png")
            langchain = Custom("LangChain", "./langchain.jpeg")

        # Data Management
        with Cluster("Data Management"):
            graph_db = Neo4J("Graph Database (Neo4J)")

        # Setup connections
        streamlit >> Edge(label="Query Processing") >> gpt4
        streamlit >> Edge(label="Language Tasks") >> langchain
        langchain >> Edge(label="Data Retrieval") >> graph_db
        gpt4 >> Edge(label="Generate Responses") >> streamlit
        graph_db >> Edge(label="Store and Manage Data") >> langchain

    # User
    user = Users("End User")
    user >> Edge(label="Accesses") >> streamlit
