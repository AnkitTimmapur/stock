import json
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import predict_stock

def handler(request):
    """Vercel serverless function handler"""
    try:
        # Handle CORS
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        
        # Get method from request
        method = request.get('method', 'GET') if isinstance(request, dict) else getattr(request, 'method', 'GET')
        
        # Handle preflight OPTIONS request
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Only allow POST requests
        if method != 'POST':
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        # Parse request body
        try:
            if isinstance(request, dict):
                body_str = request.get('body', '{}')
            else:
                body_str = getattr(request, 'body', '{}')
            
            body = json.loads(body_str) if isinstance(body_str, str) else body_str
        except Exception as e:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid JSON in request body', 'details': str(e)})
            }
        
        stock = body.get('stock', '').upper() if isinstance(body, dict) else ''
        
        if not stock:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Stock symbol is required'})
            }
        
        # Call the prediction function
        result = predict_stock(stock)
        
        if 'error' in result:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps(result)
            }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e),
                'traceback': traceback.format_exc()
            })
        }

