

# Your Neo4j connection details
from py2neo import Graph, Node, Relationship
# JSON data
import os
import json

uri = "bolt://localhost:7687"
username = "neo4j"
password = "Pratikps1$"
graph = Graph(uri, auth=(username, password))


# Create a Neo4j graph instance
def create_nodes_from_json(json_data):
    for entity in json_data["entities"]:
        label = entity["label"]
        node_id = entity["id"]
        properties = {k: v for k, v in entity.items() if k not in ["label", "id"]}
        
        # Using Graph.create to create nodes
        node = Node(label, id=node_id, **properties)
        graph.create(node)
        print("Person node was created ")








def create_nodes_and_relationships(json_data):
    # Connect to your Neo4j database
    graph = Graph("bolt://your_neo4j_server:7687", auth=("your_username", "your_password"))

    # Cypher queries to create nodes
    for entity in json_data["entities"]:
        label = entity["label"]
        node_id = entity["id"]
        properties = {k: v for k, v in entity.items() if k not in ["label", "id"]}

        # Using Graph.create to create nodes
        node = Node(label, id=node_id, **properties)
        graph.create(node)

    # Cypher queries to create relationships
    for relationship in json_data["relationships"]:
        start_node, _, end_node = relationship.split("|")

        # Using Relationship.create to create relationships
        rel_type = relationship.split("|")[1]
        graph.create(Relationship(graph.nodes.match(id=start_node).first(), rel_type, graph.nodes.match(id=end_node).first()))

    print("Nodes and relationships created successfully.")
