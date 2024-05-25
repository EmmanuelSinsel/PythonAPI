import json


class Swagger:


    def generate_swagger(self, api_details, host, port):
        swagger_template = {
            "swagger": "2.0",
            "info": {
                "description": "Auto-generated API documentation",
                "version": "1.0.0",
                "title": "Generated API"
            },
            "host": host+":"+str(port),
            "basePath": "/",
            "schemes": ["http"],
            "paths": {},
            "definitions": {}
        }

        for api in api_details:
            path = api['path']
            method = api['method'].lower()
            if path not in swagger_template['paths']:
                swagger_template['paths'][path] = {}
            swagger_template['paths'][path][method] = {
                "summary": api['summary'],
                "parameters": [
                    {
                        "name": param['name'],
                        "in": param['in'],
                        "required": param['required'],
                        "type": param['type'],
                        "schema": param.get('schema', {
                            "type": param['type']
                        })
                    } for param in api['parameters']
                ],
                "responses": {
                    "200": {
                        "description": "successful operation",
                        "schema": {
                            "type": "object",
                            "additionalProperties": True
                        }
                    }
                }
            }
            if 'response_model' in api and 'model_fields' in api:
                swagger_template['paths'][path][method]['responses']['200']['schema'] = {
                    "$ref": f"#/definitions/{api['response_model']}"
                }
                if api['response_model'] not in swagger_template['definitions']:
                    swagger_template['definitions'][api['response_model']] = {
                        "type": "object",
                        "properties": {
                            field['name']: {
                                "type": field['type']
                            } for field in api['model_fields']
                        }
                    }

        return json.dumps(swagger_template, indent=2)

    # Example API details
    api_details = [
        {
            "path": "/example",
            "method": "GET",
            "summary": "Example endpoint",
            "parameters": [
                {"name": "param1", "in": "query", "required": True, "type": "string"}
            ],
            "response_model": "ExampleModel",
            "model_fields": [
                {"name": "field1", "type": "string"},
                {"name": "field2", "type": "integer"}
            ]
        }
    ]

