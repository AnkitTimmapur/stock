import json
from app import predict_stock

def handler(request):
    if request.method not in ("POST", "GET"):
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method Not Allowed"})
        }

    try:
        symbol = None
        if request.method == "POST":
            try:
                data = request.get_json() or {}
            except Exception:
                data = {}
            symbol = data.get("stock") or data.get("symbol")
        else:
            # GET
            qs = request.args or {}
            symbol = qs.get("stock") or qs.get("symbol")

        if not symbol:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'stock' parameter"})
            }

        result = predict_stock(symbol)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }


