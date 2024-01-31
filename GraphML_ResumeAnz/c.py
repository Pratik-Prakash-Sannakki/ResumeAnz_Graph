
from py2neo import Graph, Node, Relationship

graph = Graph("bolt://localhost:7687", auth=("neo4j", "Pratikps1$"))

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

    
print(find_largest_id())