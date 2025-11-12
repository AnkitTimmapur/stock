import json
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import predict_stock

def handler(request):
    try:
        # Handle Vercel request format - support both dict and object-style
        if hasattr(request, 'method'):
            method = request.method
        elif isinstance(request, dict):
            method = request.get('method', 'GET')
        else:
            method = getattr(request, 'method', 'GET')
        
        method = str(method).upper()
        
        if method not in ("POST", "GET"):
            return {
                "statusCode": 405,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Method Not Allowed"})
            }

        symbol = None
        
        if method == "POST":
            # Try to get JSON body
            if hasattr(request, 'get_json'):
                try:
                    data = request.get_json() or {}
                except:
                    data = {}
            elif hasattr(request, 'body'):
                body = request.body
                if isinstance(body, str):
                    try:
                        data = json.loads(body)
                    except:
                        data = {}
                else:
                    data = body or {}
            elif isinstance(request, dict):
                body = request.get('body', '{}')
                if isinstance(body, str):
                    try:
                        data = json.loads(body)
                    except:
                        data = {}
                else:
                    data = body or {}
            else:
                data = {}
            
            symbol = data.get("stock") or data.get("symbol")
        else:
            # GET - check query string parameters
            if hasattr(request, 'args'):
                qs = request.args or {}
                symbol = qs.get("stock") or qs.get("symbol")
            elif hasattr(request, 'query'):
                query = request.query or {}
                if isinstance(query, str):
                    from urllib.parse import parse_qs
                    query = parse_qs(query)
                    symbol = (query.get("stock") or query.get("symbol") or [None])[0]
                else:
                    symbol = query.get("stock") or query.get("symbol")
            elif isinstance(request, dict):
                query = request.get('query', {}) or {}
                if isinstance(query, str):
                    from urllib.parse import parse_qs
                    query = parse_qs(query)
                    symbol = (query.get("stock") or query.get("symbol") or [None])[0]
                else:
                    symbol = query.get("stock") or query.get("symbol")
            else:
                symbol = None

        if not symbol:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'stock' parameter"})
            }

        result = predict_stock(symbol)
        
        # Ensure all values are JSON serializable
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            elif hasattr(obj, '__float__'):
                return float(obj)
            else:
                return str(obj)
        
        result = make_serializable(result)
        
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result, default=str)
        }
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        # Log the full traceback for debugging
        print(f"Error in predict handler: {error_msg}")
        print(traceback_str)
        
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": error_msg, "type": type(e).__name__})
        }


