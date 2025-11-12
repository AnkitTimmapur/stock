import { useState, useEffect } from 'react';
import Head from 'next/head';
import Script from 'next/script';

export default function Home() {
  const [stock, setStock] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stock }),
      });

      const data = await response.json();

      if (data.error) {
        setError('No Stock Found! Try a valid stock.');
      } else {
        setResult(data);
      }
    } catch (err) {
      setError('An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Stock Predictor</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" />
      </Head>

      <style jsx global>{`
        body {
          background: url('https://media.istockphoto.com/id/1399521171/video/analyzing-digital-data-blue-version-loopable-statistics-financial-chart-economy.jpg?s=640x640&k=20&c=jwtU00hvkCK1UShIzRDrmIwJpft4LkOyFagEqMKvidM=') center/cover no-repeat fixed;
          font-family: 'Segoe UI';
        }
        .overlay {
          background: rgba(0,0,0,0.65);
          position: fixed;
          inset: 0;
          z-index: -1;
          backdrop-filter: blur(3px);
        }
        .card {
          border-radius: 25px;
          border: 1px solid rgba(60,255,180,.35);
          background: rgba(0,30,30,0.55);
          backdrop-filter: blur(18px);
          box-shadow: 0 0 55px rgba(0,255,160,.25);
          color: #dff;
        }
        label, span, li {
          color: #dff !important;
        }
        .spinner-overlay {
          display: ${loading ? 'flex' : 'none'};
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.75);
          z-index: 9999;
          justify-content: center;
          align-items: center;
        }
        .stock-line-loader {
          width: 120px;
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .trendline {
          fill: none;
          stroke: #00ff00;
          stroke-width: 6;
          stroke-linejoin: round;
          stroke-linecap: round;
          stroke-dasharray: 300;
          stroke-dashoffset: 300;
          animation: draw 1.5s linear infinite;
        }
        @keyframes draw {
          to { stroke-dashoffset: 0; }
        }
        .error-box {
          border: 1px solid #ff0080;
          background: rgba(255,0,128,0.15);
          box-shadow: 0 0 25px rgba(255,0,150,0.45);
          color: #ffb5d9;
          padding: 12px;
          border-radius: 12px;
          font-weight: 600;
          text-align: center;
          margin-bottom: 15px;
          backdrop-filter: blur(6px);
        }
      `}</style>

      <div className="overlay"></div>

      <div className="spinner-overlay">
        <div className="stock-line-loader">
          <svg width="180" height="100" viewBox="0 0 180 100">
            <polyline points="0,90 25,70 45,75 65,55 90,60 115,35 140,45 165,20 180,5" className="trendline" />
          </svg>
        </div>
      </div>

      <div className="d-flex justify-content-center align-items-start p-5">
        <div className="container" style={{ maxWidth: '650px' }}>
          <div className="card p-4">
            <h3 className="text-center mb-4 fw-bold">Stock Price Predictor</h3>

            {error && (
              <div className="error-box">
                ⚠ {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="d-flex gap-2">
              <input
                type="text"
                name="stock"
                placeholder="Enter Stock Symbol (ex: TCS)"
                required
                className="form-control"
                value={stock}
                onChange={(e) => setStock(e.target.value)}
              />
              <button type="submit" className="btn btn-success px-3">Predict</button>
            </form>

            {result && (
              <>
                <hr />
                <ul className="list-group mt-3">
                  <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                    <span>Ticker</span>
                    <span>{result.ticker}</span>
                  </li>
                  <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                    <span>Current Price</span>
                    <span>{result.current_price}</span>
                  </li>
                  <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                    <span>Price as on</span>
                    <span>{result.current_time}</span>
                  </li>
                  <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                    <span>Predicted Next Price</span>
                    <span>{result.predicted_next}</span>
                  </li>
                  <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                    <span>Accuracy</span>
                    <span>{result.accuracy}%</span>
                  </li>
                  <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                    <span>RMSE</span>
                    <span>{result.rmse}</span>
                  </li>
                </ul>

                <h5 className="mt-4 fw-semibold text-center">Price Graph</h5>
                <div id="chart" style={{ height: '380px' }}></div>

                <h5 className="mt-5 fw-semibold text-center">Oct 11 – Nov 09: Predictions vs Actuals</h5>
                <div className="row mt-3">
                  <div className="col-12">
                    <div id="comparison_chart" style={{ height: '380px' }}></div>
                  </div>
                </div>

                <div className="mt-3">
                  <ul className="list-group">
                    <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                      <span>Backtest RMSE (Oct 11 – Nov 09)</span>
                      <span>{result.comparison_rmse !== null ? result.comparison_rmse.toFixed(4) : 'N/A'}</span>
                    </li>
                    <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                      <span>Backtest MAPE (Oct 11 – Nov 09)</span>
                      <span>{result.comparison_mape !== null ? result.comparison_mape.toFixed(2) + '%' : 'N/A'}</span>
                    </li>
                    <li className="list-group-item d-flex justify-content-between bg-transparent border-light">
                      <span>Directional Accuracy (Up/Down match)</span>
                      <span>{result.directional_accuracy !== null ? result.directional_accuracy.toFixed(2) + '%' : 'N/A'}</span>
                    </li>
                  </ul>
                </div>

                <div className="mt-4">
                  <h6 className="fw-semibold text-center">Exact Daily Values</h6>
                  <div className="table-responsive">
                    <table className="table table-sm table-dark table-striped align-middle">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th className="text-end">Predicted Close</th>
                          <th className="text-end">Actual Close</th>
                          <th className="text-end">Direction Correct?</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.month_pred_dates && result.month_pred_dates.map((date, i) => (
                          <tr key={i}>
                            <td>{date}</td>
                            <td className="text-end">{result.month_pred_values[i].toFixed(2)}</td>
                            <td className="text-end">
                              {result.backtest_actuals[i] !== null ? result.backtest_actuals[i].toFixed(2) : 'N/A'}
                            </td>
                            <td className="text-end">
                              {result.directional_flags && result.directional_flags[i] !== null ? (
                                result.directional_flags[i] ? '✅' : '❌'
                              ) : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <ChartComponent result={result} />
              </>
            )}
          </div>
        </div>
      </div>

      <Script src="https://cdn.plot.ly/plotly-latest.min.js" strategy="afterInteractive" />
    </>
  );
}

function ChartComponent({ result }) {
  useEffect(() => {
    if (typeof window === 'undefined' || !window.Plotly || !result) return;

    // Main price chart
    const traceHist = {
      x: result.hist_dates,
      y: result.hist_close,
      mode: 'lines',
      line: { width: 3, color: '#00E5FF' },
      name: 'Historical'
    };

    const tracePred = {
      x: [result.pred_date],
      y: [result.pred_value],
      mode: 'markers',
      marker: { size: 18, color: '#FF8A00', line: { width: 4, color: '#FFD199' } },
      name: 'Prediction'
    };

    window.Plotly.newPlot('chart', [traceHist, tracePred], {
      title: {
        text: `${result.ticker} Price Trend + Next Prediction`,
        font: { family: "Segoe UI", size: 20, color: "#CFFFFF" }
      },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      xaxis: { gridcolor: 'rgba(255,255,255,0.08)', color: '#CCFFFF' },
      yaxis: { gridcolor: 'rgba(255,255,255,0.08)', color: '#CCFFFF' },
      hovermode: 'x',
      legend: { orientation: 'h', y: 1.15, x: 0.5, xanchor: 'center' }
    });

    // Comparison chart
    if (result.month_pred_dates && result.month_pred_dates.length > 0) {
      const traceAct = {
        x: result.month_pred_dates,
        y: result.backtest_actuals,
        mode: 'lines+markers',
        name: 'Actual',
        line: { width: 3, color: '#00E676' },
        marker: { size: 6 }
      };

      const traceCmp = {
        x: result.month_pred_dates,
        y: result.month_pred_values,
        mode: 'lines+markers',
        name: 'Predicted',
        line: { width: 3, color: '#FFAB40' },
        marker: { size: 6 }
      };

      window.Plotly.newPlot('comparison_chart', [traceAct, traceCmp], {
        title: {
          text: 'Predicted vs Actual',
          font: { family: "Segoe UI", size: 20, color: "#CFFFFF" }
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { gridcolor: 'rgba(255,255,255,0.08)', color: '#CCFFFF' },
        yaxis: { gridcolor: 'rgba(255,255,255,0.08)', color: '#CCFFFF' },
        hovermode: 'x',
        legend: { orientation: 'h', y: 1.15, x: 0.5, xanchor: 'center' }
      });
    }
  }, [result]);

  return null;
}

