import urllib.parse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Properly format and encode the URI
username = urllib.parse.quote_plus("kundusagar233")
password = urllib.parse.quote_plus("q2@4GdIFqxTkGzL")
cluster = "sagar.br2ms9r.mongodb.net"
uri = f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority&appName=SAGAR"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
