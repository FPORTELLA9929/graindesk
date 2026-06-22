import requests
from zeep import Client
from zeep.transports import Transport

session = requests.Session()
session.verify = False

transport = Transport(session=session)

url = "https://mdfe-homologacao.svrs.rs.gov.br/ws/mdferecepcao/MDFeRecepcao.asmx?wsdl"

client = Client(url, transport=transport)

print("Conectado")
print(client.wsdl.services.keys())