import json
import sys
import os

# Add parent directory to path to import app
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Try to import predict_stock
    try:
        from app import predict_stock
    except ImportError:
        # Fallback: try importing using importlib
        import importlib.util
        app_path = os.path.join(parent_dir, "app.py")
        if os.path.exists(app_path):
            spec = importlib.util.spec_from_file_location("app", app_path)
            if spec and spec.loader:
                app_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(app_module)
                predict_stock = app_module.predict_stock
            else:
                raise ImportError("Could not load app module")
        else:
            raise ImportError(f"app.py not found at {app_path}")
except Exception as e:
    # If import fails completely, we'll handle it in the handler
    print(f"Warning: Failed to import predict_stock: {e}")
    predict_stock = None

def handler(request):
    try:
        # Check if predict_stock is available
        if predict_stock is None:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Function not available: import failed"})
            }
        
        # Vercel Python runtime passes request as a dict
        # Handle both dict and object-style requests
        if request is None:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid request"})
            }
        
        # Get method
        if isinstance(request, dict):
            method = request.get('method', 'GET').upper()
            body = request.get('body', '{}')
            query = request.get('query', {})
        else:
            method = getattr(request, 'method', 'GET')
            if hasattr(request, 'body'):
                body = request.body
            else:
                body = '{}'
            if hasattr(request, 'query'):
                query = request.query
            else:
                query = {}
        
        method = str(method).upper()
        
        if method not in ("POST", "GET"):
            return {
                "statusCode": 405,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Method Not Allowed"})
            }

        symbol = None
        
        if method == "POST":
            # Parse JSON body
            if isinstance(body, str):
                try:
                    data = json.loads(body) if body else {}
                except json.JSONDecodeError:
                    data = {}
            else:
                data = body or {}
            
            symbol = data.get("stock") or data.get("symbol")
        else:
            # GET - check query string parameters
            if isinstance(query, str):
                from urllib.parse import parse_qs, unquote
                query_dict = parse_qs(unquote(query))
                symbol = (query_dict.get("stock") or query_dict.get("symbol") or [None])[0]
            elif isinstance(query, dict):
                symbol = query.get("stock") or query.get("symbol")
            else:
                symbol = None

        if not symbol:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'stock' parameter"})
            }

        # Call the prediction function
        result = predict_stock(str(symbol))
        
        # Check if result contains an error
        if isinstance(result, dict) and "error" in result:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result)
            }
        
        # Ensure all values are JSON serializable
        def make_serializable(obj):
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            elif hasattr(obj, '__float__'):
                try:
                    return float(obj)
                except (ValueError, TypeError):
                    return str(obj)
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


