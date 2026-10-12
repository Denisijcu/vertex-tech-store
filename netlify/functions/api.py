import json
import os
import csv

def handler(event, context):
    # Obtenemos la ruta absoluta del directorio actual (netlify/functions)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Subimos dos niveles para llegar a la raíz del proyecto (netlify/functions -> netlify -> raíz)
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
            'body': json.dumps({'error': f"No se pudo leer el CSV en {csv_path}: {str(e)}"})
        }

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(products)
    }