from flask import Flask, request, render_template_string
from app import predict_stock

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Stock Predictor</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">

  <style>
    body{
      background:url('https://media.istockphoto.com/id/1399521171/video/analyzing-digital-data-blue-version-loopable-statistics-financial-chart-economy.jpg?s=640x640&k=20&c=jwtU00hvkCK1UShIzRDrmIwJpft4LkOyFagEqMKvidM=') center/cover no-repeat fixed;
      font-family:'Segoe UI';
    }
    .overlay{
      background:rgba(0,0,0,0.65);
      position:fixed;inset:0;z-index:-1;
      backdrop-filter:blur(3px);
    }
    .card{
      border-radius:25px;
      border:1px solid rgba(60,255,180,.35);
      background:rgba(0,30,30,0.55);
      backdrop-filter:blur(18px);
      box-shadow:0 0 55px rgba(0,255,160,.25);
      color:#dff;
    }
    label, span, li{ color:#dff !important; }

    .spinner-overlay{
      display:none;
      position:fixed;
      inset:0;
      background:rgba(0,0,0,0.75);
      z-index:9999;
      justify-content:center;
      align-items:center;
    }

    /* NEW STOCK LINE LOADER */
    .stock-line-loader {
      width:120px;
      height:60px;
      display:flex;
      align-items:center;
      justify-content:center;
    }

    .trendline {
      fill:none;
      stroke:#00ff00;
      stroke-width:6;
      stroke-linejoin:round;
      stroke-linecap:round;
      stroke-dasharray:300;
      stroke-dashoffset:300;
      animation:draw 1.5s linear infinite;
    }

    @keyframes draw {
      to { stroke-dashoffset:0; }
    }

  </style>
</head>
<body class="d-flex justify-content-center align-items-start p-5">
<div class="overlay"></div>

<div class="spinner-overlay" id="loading">
  <div class="stock-line-loader">
    <svg width="180" height="100" viewBox="0 0 180 100">
      <polyline points="0,90 25,70 45,75 65,55 90,60 115,35 140,45 165,20 180,5" class="trendline"/>
    </svg>
  </div>
</div>

<div class="container" style="max-width:650px;">
  <div class="card p-4">
    <h3 class="text-center mb-4 fw-bold">Stock Price Predictor</h3>

    {% if error %}
    <div style="
      border:1px solid #ff0080;
      background:rgba(255,0,128,0.15);
      box-shadow:0 0 25px rgba(255,0,150,0.45);
      color:#ffb5d9;
      padding:12px;
      border-radius:12px;
      font-weight:600;
      text-align:center;
      margin-bottom:15px;
      backdrop-filter:blur(6px);
    ">
    ⚠ {{ error }}
    </div>
    {% endif %}

    <form method="POST" class="d-flex gap-2" onsubmit="showLoader()">
      <input type="text" name="stock" placeholder="Enter Stock Symbol (ex: TCS)" required class="form-control">
      <button class="btn btn-success px-3">Predict</button>
    </form>

    {% if result %}
    <hr>
    <ul class="list-group mt-3">
      <li class="list-group-item d-flex justify-content-between bg-transparent border-light"><span>Ticker</span><span>{{ result.ticker }}</span></li>
      <li class="list-group-item d-flex justify-content-between bg-transparent border-light"><span>Current Price</span><span>{{ result.current_price }}</span></li>
      <li class="list-group-item d-flex justify-content-between bg-transparent border-light"><span>Price as on</span><span>{{ result.current_time }}</span></li>
      <li class="list-group-item d-flex justify-content-between bg-transparent border-light"><span>Predicted Next Price</span><span>{{ result.predicted_next }}</span></li>
      <li class="list-group-item d-flex justify-content-between bg-transparent border-light"><span>Accuracy</span><span>{{ result.accuracy }}%</span></li>
      <li class="list-group-item d-flex justify-content-between bg-transparent border-light"><span>RMSE</span><span>{{ result.rmse }}</span></li>
    </ul>

    <h5 class="mt-4 fw-semibold text-center">Price Graph</h5>

    <div id="chart" style="height:380px;"></div>

    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
    var dates = {{ result.hist_dates|safe }};
    var close = {{ result.hist_close|safe }};
    var predDate = "{{ result.pred_date }}";
    var predValue = {{ result.pred_value }};

    var traceHist = { 
        x:dates, y:close, 
        mode:'lines', 
        line:{width:3,color:'#00E5FF'}, 
        name:'Historical' 
    };

    var tracePred = { 
        x:[predDate], y:[predValue], 
        mode:'markers', 
        marker:{size:18,color:'#FF8A00',line:{width:4,color:'#FFD199'}}, 
        name:'Prediction' 
    };

    Plotly.newPlot('chart',[traceHist,tracePred],{
        title:{
            text:'{{ result.ticker }} Price Trend + Next Prediction',
            font:{family:"Segoe UI",size:20,color:"#CFFFFF"}
        },
        paper_bgcolor:'rgba(0,0,0,0)',
        plot_bgcolor:'rgba(0,0,0,0)',
        xaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
        yaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
        hovermode:'x',
        legend:{ orientation:'h', y:1.15, x:0.5, xanchor:'center' }
    });
    </script>

    <!-- New: Month-ahead predictions vs actuals (Oct 11 to Nov 09) -->
    <h5 class="mt-5 fw-semibold text-center">Oct 11 – Nov 09: Predictions vs Actuals</h5>
    <div class="row mt-3">
      <div class="col-12">
        <div id="comparison_chart" style="height:380px;"></div>
      </div>
    </div>

    <script>
    var cmpDates = {{ result.month_pred_dates|safe if result.month_pred_dates is defined else '[]' }};
    var cmpPred  = {{ result.month_pred_values|safe if result.month_pred_values is defined else '[]' }};
    var cmpAct   = {{ result.backtest_actuals|safe if result.backtest_actuals is defined else '[]' }};

    var traceAct = {
      x: cmpDates, y: cmpAct,
      mode: 'lines+markers',
      name: 'Actual',
      line: { width: 3, color: '#00E676' },
      marker: { size: 6 }
    };
    var traceCmp = {
      x: cmpDates, y: cmpPred,
      mode: 'lines+markers',
      name: 'Predicted',
      line: { width: 3, color: '#FFAB40' },
      marker: { size: 6 }
    };
    Plotly.newPlot('comparison_chart', [traceAct, traceCmp], {
      title: { text: 'Predicted vs Actual', font:{family:"Segoe UI",size:20,color:"#CFFFFF"} },
      paper_bgcolor:'rgba(0,0,0,0)',
      plot_bgcolor:'rgba(0,0,0,0)',
      xaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
      yaxis:{ gridcolor:'rgba(255,255,255,0.08)', color:'#CCFFFF' },
      hovermode:'x',
      legend:{ orientation:'h', y:1.15, x:0.5, xanchor:'center' }
    });
    </script>

    <div class="mt-3">
      <ul class="list-group">
        <li class="list-group-item d-flex justify-content-between bg-transparent border-light">
          <span>Backtest RMSE (Oct 11 – Nov 09)</span>
          <span>{{ ('%.4f' % result.comparison_rmse) if result.comparison_rmse is not none else 'N/A' }}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between bg-transparent border-light">
          <span>Backtest MAPE (Oct 11 – Nov 09)</span>
          <span>{{ ('%.2f' % result.comparison_mape) + '%' if result.comparison_mape is not none else 'N/A' }}</span>
        </li>
        <li class="list-group-item d-flex justify-content-between bg-transparent border-light">
          <span>Directional Accuracy (Up/Down match)</span>
          <span>{{ ('%.2f' % result.directional_accuracy) + '%' if result.directional_accuracy is not none else 'N/A' }}</span>
        </li>
      </ul>
    </div>

    <!-- Optional table for exact daily values -->
    <div class="mt-4">
      <h6 class="fw-semibold text-center">Exact Daily Values</h6>
      <div class="table-responsive">
        <table class="table table-sm table-dark table-striped align-middle">
          <thead>
            <tr>
              <th>Date</th>
              <th class="text-end">Predicted Close</th>
              <th class="text-end">Actual Close</th>
              <th class="text-end">Direction Correct?</th>
            </tr>
          </thead>
          <tbody>
            {% if result.month_pred_dates %}
              {% for i in range(result.month_pred_dates|length) %}
                <tr>
                  <td>{{ result.month_pred_dates[i] }}</td>
                  <td class="text-end">{{ '%.2f' % result.month_pred_values[i] }}</td>
                  <td class="text-end">
                    {% if result.backtest_actuals[i] is not none %}
                      {{ '%.2f' % result.backtest_actuals[i] }}
                    {% else %}
                      N/A
                    {% endif %}
                  </td>
                  <td class="text-end">
                    {% if result.directional_flags is defined and result.directional_flags[i] is not none %}
                      {% if result.directional_flags[i] %}
                        ✅
                      {% else %}
                        ❌
                      {% endif %}
                    {% else %}
                      N/A
                    {% endif %}
                  </td>
                </tr>
              {% endfor %}
            {% endif %}
          </tbody>
        </table>
      </div>
    </div>
    {% endif %}
  </div>
</div>

<script>
function showLoader(){ document.getElementById("loading").style.display="flex"; }
</script>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def index():
    result=None
    error=None

    if request.method=="POST":
        stock = request.form["stock"].upper()
        result_data = predict_stock(stock)

        if "error" in result_data:
            error = "No Stock Found! Try a valid stock."
            return render_template_string(HTML, result=None, error=error)

        class R: pass
        r=R()
        for k,v in result_data.items(): setattr(r,k,v)
        result=r
    return render_template_string(HTML, result=result, error=error)

if __name__=="__main__":
    app.run(debug=True)
