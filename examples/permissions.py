from sonas_client import SonasClient
import os

username = os.environ["SONAS_USERNAME"]
password = os.environ["SONAS_PASSWORD"]
host = os.environ["SONAS_HOST"]
client = SonasClient(username, password, host)


print("\n--- Data permissions ---")
data_permissions = client.get_data_permissions()
products = data_permissions["products"]
print(products)
