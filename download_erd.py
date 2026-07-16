import base64
import requests
import json

graph = """erDiagram
    DIM_FACTORY ||--o{ DIM_PRODUCTION_LINE : houses
    DIM_FACTORY ||--o{ DIM_WAREHOUSE : houses
    DIM_FACTORY ||--o{ DIM_EMPLOYEE : employs
    DIM_PRODUCTION_LINE ||--o{ DIM_MACHINE : contains
    DIM_SUPPLIER ||--o{ DIM_PART : supplies
    DIM_MACHINE ||--o{ FACT_SENSOR : monitors
    DIM_MACHINE ||--o{ FACT_MAINTENANCE : repairs
    DIM_EMPLOYEE ||--o{ FACT_MAINTENANCE : performed_by
    DIM_PRODUCT ||--o{ FACT_ERP_PRODUCTION : manufactures
    DIM_EMPLOYEE ||--o{ FACT_ERP_PRODUCTION : operated_by
    DIM_PRODUCT ||--o{ FACT_QUALITY : inspects
    DIM_EMPLOYEE ||--o{ FACT_QUALITY : inspected_by
    DIM_PART ||--o{ FACT_INVENTORY : stocks
    DIM_WAREHOUSE ||--o{ FACT_INVENTORY : stored_in
    DIM_SUPPLIER ||--o{ FACT_INVENTORY : supplied_by
    DIM_MACHINE ||--o{ FACT_ENERGY : consumes
    FACT_ERP_PRODUCTION ||--o{ FACT_SHIPMENTS : fulfills
    DIM_CUSTOMER ||--o{ FACT_SHIPMENTS : delivers_to
    DIM_PRODUCT ||--o{ FACT_SHIPMENTS : contains"""

payload = json.dumps({"code": graph, "mermaid": {"theme": "dark"}})
b64 = base64.b64encode(payload.encode('utf-8')).decode('utf-8')

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
url = f"https://mermaid.ink/img/{b64}?type=png&bgColor=2b2b2b&scale=3"
response = requests.get(url, headers=headers)
with open("docs/erd.png", "wb") as f:
    f.write(response.content)
print("Downloaded high-res docs/erd.png")
