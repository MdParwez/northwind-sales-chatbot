from typing import List, Dict, Any
import pandas as pd

def maybe_forecast(data: List[Dict[str, Any]], x_field: str, y_field: str, periods: int = 3):
    df = pd.DataFrame(data)
    if x_field not in df or y_field not in df:
        return data
    try:
        df["ds"] = pd.to_datetime(df[x_field])
    except Exception:
        return data
    df = df.sort_values("ds").rename(columns={y_field: "y"})
    if len(df) < 6:
        return data
    try:
        try:
            from prophet import Prophet
        except Exception:
            from fbprophet import Prophet
        freq = pd.infer_freq(df["ds"]) or "MS"
        m = Prophet()
        m.fit(df[["ds","y"]])
        future = m.make_future_dataframe(periods=periods, freq=freq)
        fcst = m.predict(future).tail(periods)
        for _, row in fcst.iterrows():
            data.append({x_field: row["ds"].strftime("%Y-%m"), y_field: float(row["yhat"]), "forecast": True})
        return data
    except Exception:
        recent = df["y"].tail(6).mean()
        last_ts = df["ds"].max()
        freq = pd.infer_freq(df["ds"]) or "MS"
        future_idx = pd.date_range(last_ts, periods=periods+1, freq=freq)[1:]
        for ts in future_idx:
            data.append({x_field: ts.strftime("%Y-%m"), y_field: float(recent), "forecast": True})
        return data