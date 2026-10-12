import json
import os
import csv
import urllib.request

def handler(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "GET")
    
    # Manejar CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }

    if method == "OPTIONS":
        return {'statusCode': 200, 'headers': headers, 'body': ''}

    # Ruta de productos (/api/products o /products)
    if "products" in path:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.normpath(os.path.join(current_dir, '../../productos.csv'))
        
        products = []
        try:
            with open(csv_path, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    row['price'] = float(row['price'])
                    row['id'] = int(row['id'])
                    products.append(row)
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': f"Error leyendo CSV: {str(e)}"})
            }

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(products)
        }

    # Ruta de chat (/api/chat o /chat)
    if "chat" in path:
        try:
            body = json.loads(event.get("body", "{}"))
            user_message = body.get("message", "")
            
            anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
            
            if not anthropic_key:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'reply': "⚠️ Falta configurar la ANTHROPIC_API_KEY en las variables de entorno de Netlify."})
                }

            # Llamada segura a Anthropic API via urllib para evitar dependencias pesadas en serverless
            req_data = json.dumps({
                "model": "claude-3-haiku-20240307",
                "max_tokens": 300,
                "system": "Eres 'Vertex Core AI', el asistente virtual de Vertex Tech Store. Respondes en español, de forma breve, útil y orientada a la conversión.",
                "messages": [{"role": "user", "content": user_message}]
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=req_data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01"
                },
                method="POST"
            )

            with urllib.request.urlopen(req) as response:
                res_body = json.loads(response.read().decode('utf-8'))
                reply_text = ""
                for block in res_body.get("content", []):
                    if block.get("type") == "text":
                        reply_text += block.get("text", "")
                
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'reply': reply_text.strip()})
                }

        except Exception as exc:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'reply': f"¡Hola! 👋 Recibí tu mensaje, pero el sistema local indicó un pequeño error de procesamiento: {str(exc)}"})
            }

    return {
        'statusCode': 404,
        'headers': headers,
        'body': json.dumps({'error': 'Not found'})
    }