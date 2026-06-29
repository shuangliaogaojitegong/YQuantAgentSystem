import json
with open('config/dsl_schema.json', 'r') as f:
    schema = json.load(f)
print("✅ DSL Schema 加载成功，算子列表:", schema['definitions']['ExpressionNode']['properties']['op']['enum'])