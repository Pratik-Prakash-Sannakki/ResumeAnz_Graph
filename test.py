from openai import OpenAI
client = OpenAI(api_key='')



def generate_openai_embeddings(text):

    response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
            )
    return response.data[0].embedding
embed = generate_openai_embeddings("Delta Lake, Parquet, and Spark SQL")
