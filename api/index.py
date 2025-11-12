def handler(request):
    try:
        html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Stock Predictor</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body{ background:#0e1a1a; color:#dff; font-family:Segoe UI; }
    .card{ border-radius:18px; background:#112222; border:1px solid #1dd3b0; }
    .muted{ color:#9fd; opacity:.85 }
  </style>
</head>
<body class="p-3 p-md-5">
  <div class="container" style="max-width:900px;">
    <div class="card p-4">
      <h3 class="mb-3 text-center">Stock Price Predictor</h3>
      <form id="f" class="d-flex gap-2 mb-3" onsubmit="runPredict(event)">
        <input type="text" class="form-control" id="stock" placeholder="Enter Stock Symbol (e.g., TCS or TCS.NS)" required />
        <button class="btn btn-success px-3">Predict</button>
      </form>
      <div id="error" class="alert alert-danger d-none"></div>
      <div id="meta" class="mb-3"></div>
      <div id="chart" style="height:360px;"></div>
      <hr/>
      <h5 class="mt-3">Oct 11 – Nov 09: Predictions vs Actuals</h5>
      <div id="cmp" style="height:360px;"></div>
      <div class="mt-3">
        <ul class="list-group">
          <li class="list-group-item bg-transparent d-flex justify-content-between">
            <span class="muted">Backtest RMSE</span><span id="rmse">-</span>
          </li>
          <li class="list-group-item bg-transparent d-flex justify-content-between">
            <span class="muted">Backtest MAPE</span><span id="mape">-</span>
          </li>
          <li class="list-group-item bg-transparent d-flex justify-content-between">
            <span class="muted">Directional Accuracy</span><span id="dacc">-</span>
          </li>
        </ul>
      </div>
      <div class="table-responsive mt-3">
        <table class="table table-sm table-dark table-striped align-middle">
          <thead><tr><th>Date</th><th class="text-end">Predicted</th><th class="text-end">Actual</th><th class="text-end">Correct?</th></tr></thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
    async function runPredict(e){
      e.preventDefault();
      const sym = document.getElementById('stock').value.trim();
      const err = document.getElementById('error');
      err.classList.add('d-none'); err.textContent = '';
      try{
        const res = await fetch('/api/predict', {
          method:'POST',
          headers:{ 'Content-Type':'application/json' },
          body: JSON.stringify({ stock: sym })
        });
        const data = await res.json();
        if(data.error){
          err.textContent = data.error;
          err.classList.remove('d-none');
          return;
        }
        renderAll(data);
      }catch(ex){
        err.textContent = ex.message || 'Failed';
        err.classList.remove('d-none');
      }
    }

    function renderAll(result){
      document.getElementById('meta').innerHTML = `
        <div class="row g-2">
          <div class="col-md-4"><strong>Ticker:</strong> ${result.ticker}</div>
          <div class="col-md-4"><strong>Current Price:</strong> ${result.current_price?.toFixed ? result.current_price.toFixed(2) : result.current_price}</div>
          <div class="col-md-4"><strong>As on:</strong> ${result.current_time}</div>
        </div>
      `;

      const histDates = result.hist_dates || [];
      const histClose = result.hist_close || [];
      const traceHist = { x:histDates, y:histClose, mode:'lines', name:'Historical', line:{width:3,color:'#00E5FF'} };
      Plotly.newPlot('chart', [traceHist], {
        paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
        xaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
        yaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
      });

      const d = result.month_pred_dates || [];
      const pv = result.month_pred_values || [];
      const av = result.backtest_actuals || [];
      Plotly.newPlot('cmp', [
        { x:d, y:av, mode:'lines+markers', name:'Actual', line:{width:3,color:'#00E676'}, marker:{size:6} },
        { x:d, y:pv, mode:'lines+markers', name:'Predicted', line:{width:3,color:'#FFAB40'}, marker:{size:6} }
      ], {
        paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
        xaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
        yaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
      });

      document.getElementById('rmse').textContent = result.comparison_rmse != null ? result.comparison_rmse.toFixed(4) : 'N/A';
      document.getElementById('mape').textContent = result.comparison_mape != null ? result.comparison_mape.toFixed(2) + '%' : 'N/A';
      document.getElementById('dacc').textContent = result.directional_accuracy != null ? result.directional_accuracy.toFixed(2) + '%' : 'N/A';

      const tbody = document.getElementById('rows');
      tbody.innerHTML = '';
      const flags = result.directional_flags || [];
      for(let i=0;i<d.length;i++){
        const tr = document.createElement('tr');
        const a = av[i]; const p = pv[i];
        tr.innerHTML = `
          <td>${d[i] || ''}</td>
          <td class="text-end">${p!=null ? p.toFixed(2) : 'N/A'}</td>
          <td class="text-end">${a!=null ? a.toFixed(2) : 'N/A'}</td>
          <td class="text-end">${flags[i] == null ? 'N/A' : (flags[i] ? '✅' : '❌')}</td>
        `;
        tbody.appendChild(tr);
      }
    }
  </script>
</body>
</html>
        """
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html; charset=utf-8"},
            "body": html
        }
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"Error in index handler: {error_msg}")
        print(traceback_str)
        
        # Return a simple error page
        error_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Error - Stock Predictor</title>
  <style>
    body {{ background:#0e1a1a; color:#dff; font-family:Segoe UI; padding: 20px; }}
    .error {{ background:#112222; border:1px solid #ff4444; padding: 20px; border-radius: 10px; max-width: 600px; margin: 50px auto; }}
    h1 {{ color: #ff4444; }}
  </style>
</head>
<body>
  <div class="error">
    <h1>Error Loading Page</h1>
    <p>An error occurred while loading the page. Please try again later.</p>
    <p><small>Error: {error_msg}</small></p>
  </div>
</body>
</html>
        """
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "text/html; charset=utf-8"},
            "body": error_html
        }


