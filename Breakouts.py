# ==========================================
# CPR + Breakout Strategy - Streamlit App
# ==========================================
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import numpy as np

# # Custom CSS for neon glow effects
# st.markdown(
#     """
#     <style>
#     .stApp {
#         background-color:grey;
#         color: #FAFAFA;
#     }
#     h1, h2, h3, h4, h5, h6 {
#         color: #39FF14 !important;
#         text-shadow: 0px 0px 10px #39FF14;
#     }
#     .stButton>button {
#         background-color: lightyellow;
#         color: black;
#         border-radius: 10px;
#         font-weight: bold;
#         box-shadow: 0px 0px 20px #39FF14;
#     }
#     .stButton>button:hover {
#         background-color: lightblue;
#         color: #39FF14;
#         border: 1px solid #39FF14;
#     }
#     </style>
#     """ ,
#     unsafe_allow_html=True
# )


st.set_page_config(page_title="CPR + Breakout Strategy", layout="wide")

st.title("📊Complete Breakout Strategis")

# --------------------------
# User Inputs

# todays data CPR

# Upload Nifty200 stock list

def detect_swing_points(df, left=2, right=2):
    """
    Swing High: current high > all highs in previous 'left' candles and next 'right' candles
    Swing Low : current low  < all lows  in previous 'left' candles and next 'right' candles
    """
    swing_high = []
    swing_low = []

    for i in range(len(df)):
        # bounds
        if i < left or i + right >= len(df):
            swing_high.append(np.nan)
            swing_low.append(np.nan)
            continue

        # check highs
        if df["High"].iloc[i] == max(df["High"].iloc[i-left:i+right+1]):
            swing_high.append(df["High"].iloc[i])
        else:
            swing_high.append(np.nan)

        # check lows
        if df["Low"].iloc[i] == min(df["Low"].iloc[i-left:i+right+1]):
            swing_low.append(df["Low"].iloc[i])
        else:
            swing_low.append(np.nan)

    df["Swing_High"] = swing_high
    df["Swing_Low"] = swing_low
    df["Last_Swing_High"] = df["Swing_High"].ffill()
    df["Last_Swing_Low"] = df["Swing_Low"].ffill()

    return df



# def detect_swing_points(df, window=2):
#     """
#     Detect swing highs and swing lows with rolling window.
#     """
#     highs = df["High"].rolling(window * 2 + 1, center=True)
#     lows = df["Low"].rolling(window * 2 + 1, center=True)

#     df["Swing_High"] = np.where(df["High"] == highs.max(), df["High"], np.nan)
#     df["Swing_Low"] = np.where(df["Low"] == lows.min(), df["Low"], np.nan)
#     df["Last_Swing_High"] = df["Swing_High"].ffill()
#     df["Last_Swing_Low"] = df["Swing_Low"].ffill()

#     latest_swing_high = df["Swing_High"].dropna().iloc[-1] if not df["Swing_High"].dropna().empty else np.nan
#     latest_swing_low = df["Swing_Low"].dropna().iloc[-1] if not df["Swing_Low"].dropna().empty else np.nan

#     return df, latest_swing_high, latest_swing_low

col1, col2, col3,col4= st.columns([1, 1, 1,1])

with col1:
    CPR_ASC_DESC = st.selectbox("CPR Asc or Desc?",
        ["All","Asc", "Desc"], 
        index=0)
with col2:
    yday_breakout_filter = st.selectbox("Filter Yesterday High Breakout?",
        ["All","Close > Yday High", "Close < Yday Low"], 
        index=0)
with col3:
   
     EMA_filter = st.selectbox("EMA Filter", ["None", "Close > EMA20", "Close > EMA7","Close < EMA20","Close < EMA7"], index=0)
with col4:
     Volume_filter = st.selectbox("Volume Filter", ["None", "Vol > Yday Vol", "Vol > 5d Avg","Vol > 2*Avg"], index=0)
     
uploaded_file = st.file_uploader("Upload your stock list CSV (with 'Symbol' column)", type=["csv"])

if uploaded_file is not None:
    stocks_df = pd.read_csv(uploaded_file)
    stocks = stocks_df["Symbol"].tolist()

    today = datetime.today().date()
    qualified_stocks = []

    progress_bar = st.progress(0)
    total = len(stocks)

    for idx, ticker in enumerate(stocks):
        try:
            # ---- Step 1: Daily data (15 days) ----
            daily = yf.download(ticker, period="60d", interval="1d")
            # st.write("Number of non-NaN values per column:")
            # st.write(daily.count())
            if len(daily) < 20:
                continue
                # ---- Yesterday OHLC ----
            yday_high = float(daily["High"].iloc[-2])
            yday_low = float(daily["Low"].iloc[-2])
            yday_close = float(daily["Close"].iloc[-2])
            yday_vol = float(daily["Volume"].iloc[-2])

            # ---- Day-before-yesterday OHLC ----
            dby_high = float(daily["High"].iloc[-3])
            dby_low = float(daily["Low"].iloc[-3])
            dby_close = float(daily["Close"].iloc[-3])

            # ---- Today values ----
            today_close = float(daily["Close"].iloc[-1])
            today_vol = float(daily["Volume"].iloc[-1])

            # ---- EMA20 ----
            daily["EMA20"] = daily["Close"].ewm(span=20).mean()
            ema20 = float(daily["EMA20"].iloc[-1])

            daily["EMA7"] = daily["Close"].ewm(span=7).mean()
            ema7 = float(daily["EMA7"].iloc[-1])
                        # Flatten columns first (for yfinance multi-index)
            if isinstance(daily.columns, pd.MultiIndex):
                daily.columns = [c[0] if isinstance(c, tuple) else c for c in daily.columns]

            daily["H-L"] = daily["High"] - daily["Low"]
            daily["H-PC"] = (daily["High"] - daily["Close"].shift()).abs()
            daily["L-PC"] = (daily["Low"] - daily["Close"].shift()).abs()

            # True Range
            daily["TR"] = daily[["H-L", "H-PC", "L-PC"]].max(axis=1)

            # ATR (14 period)
            daily["ATR"] = daily["TR"].rolling(14).mean()
            #daily["ATR"] = float(daily["High"].rolling(14).max()) - float(daily["Low"].rolling(14).min())
            ATR=float(daily["ATR"].iloc[-1])
            daily["ATR_Ratio"] = daily["ATR"] / daily["Close"].values
            atr_ratio = daily["ATR_Ratio"].iloc[-1]
            daily["20d_High"] = daily["High"].rolling(20).max()
            daily["20d_Low"] = daily["Low"].rolling(20).min()
            Day20_High=float( daily["20d_High"].iloc[-1])
            Day20_Low=float( daily["20d_Low"].iloc[-1])

            daily["AvgVol20"] = daily["Volume"].rolling(20).mean()
            avg_vol20 = daily["AvgVol20"].iloc[-1]

            # PreBreakout = False
            # if not daily[["20d_High", "ATR_Ratio", "AvgVol20"]].iloc[-1].isna().any():
            #     Day20_High = daily["20d_High"].iloc[-1]
            #    
            #     avg_vol20 = daily["AvgVol20"].iloc[-1]

           
           
            # CPR for yesterday
            y_pivot = (yday_high + yday_low + yday_close) / 3
            y_bc = (yday_high + yday_low) / 2
            y_tc = 2 * y_pivot - y_bc

                    
            R1 = round((2 * y_pivot) - yday_low,1)
            S1 = round((2 * y_pivot) - yday_high,1)
            R2 = round(y_pivot + (yday_high - yday_low),1)
            S2 = round(y_pivot - (yday_high - yday_low),1)

            # CPR for day-before-yesterday
            dby_pivot = (dby_high + dby_low + dby_close) / 3
            dby_bc = (dby_high + dby_low) / 2
            dby_tc = 2 * dby_pivot - dby_bc
            #---- CPR Trend ---- OLD Code
            if (y_pivot > dby_pivot and y_bc > dby_bc and y_tc > dby_tc):
                cpr_trend = "Ascending"
            elif (y_pivot < dby_pivot and y_bc < dby_bc and y_tc < dby_tc):
                cpr_trend = "Descending"
            else:
                cpr_trend = "Sideways"


            def get_latest_cpr_trend(close, bc, tc):
                if close > tc:
                    return "Ascending"
                elif close < bc:
                    return "Descending"
                else:
                    return "Neutral"
            latest_cpr_trend = get_latest_cpr_trend(today_close, y_bc, y_tc)   

            #daily, latest_swing_high, latest_swing_low = detect_swing_points(daily, window=2)

            daily = detect_swing_points(daily, left=2, right=2)
            latest_swing_high = daily["Swing_High"].dropna().iloc[-1]
            latest_swing_low = daily["Swing_Low"].dropna().iloc[-1]
           

            
            PreBreakout =(
                not np.isnan(latest_swing_high)
                and (today_close < latest_swing_high)                  # not broken yet
                and (today_close >= 0.96 * latest_swing_high)          # within 4% of swing high
                and (today_vol >= 0.6 * avg_vol20)                     # decent volume
                and (atr_ratio < 0.05)                                 # low volatility
                and (cpr_trend in ["Ascending", "Sideways"])
            ) 

            PreBreakdown =(
            
                not np.isnan(latest_swing_low)
                and (today_close > latest_swing_low)                   # not broken yet
                and (today_close <= 1.04 * latest_swing_low)           # within 4% of swing low
                and (today_vol >= 0.6 * avg_vol20)
                and (atr_ratio < 0.05)
                and (cpr_trend in ["Descending", "Sideways"])
            )

            # if (today_close>y_tc):
            #     cpr_trend = "Ascending"
            # elif(today_close<y_bc):
            #       cpr_trend = "Descending"  
            #---- CPR Type (for yesterday CPR) ----
            cpr_width = y_tc - y_bc
            cpr_pct = (cpr_width / y_pivot) * 100
            cpr_type = "Narrow" if cpr_pct < 0.25 else "Wide"

            score = 0
            sell_score=0
            conditions = {}

             # 1. Today close > yesterday high
            conditions["Close < Yday Low"] = today_close < yday_low
            if conditions["Close < Yday Low"]:
                sell_score += 1

            conditions["Close < EMA20"] = today_close < ema20
            if conditions["Close < EMA20"]:
                sell_score += 1    

            conditions["Close < EMA7"] = today_close < ema7
            if conditions["Close < EMA7"]:
                sell_score += 1         

            # 1. Today close > yesterday high
            conditions["Close > Yday High"] = today_close > yday_high
            if conditions["Close > Yday High"]:
                score += 1

            # 2. Today volume > yesterday volume
            conditions["Vol > Yday Vol"] = today_vol > yday_vol
            if conditions["Vol > Yday Vol"]:
                score += 1

            # 3. Today close > EMA20
            conditions["Close > EMA20"] = today_close > ema20
            if conditions["Close > EMA20"]:
                score += 1

             # 3. Today close > EMA7
            conditions["Close > EMA7"] = today_close > ema7
            if conditions["Close > EMA7"]:
                score += 1
            # 4. Today volume > avg volume (last 5 days)
            avg_vol_5 = float(daily["Volume"].iloc[-6:-1].mean())
            conditions["Vol > 5d Avg"] = today_vol > avg_vol_5
            if conditions["Vol > 5d Avg"]:
                score += 2   # weighted condition

            #avg_vol_Spike = float(daily["Volume"].iloc[-6:-1].mean())
            conditions["Vol > 2*Avg"] = today_vol >2* avg_vol_5
            if conditions["Vol > 2*Avg"]:
                score += 2   # weighted condition    

            # ---- Collect only if score > 0 ----
            market_cap = None
            # if ticker in stocks_df["Symbol"].values:
            #     market_cap = stocks_df.loc[stocks_df["Symbol"] == ticker, "MarketCap"].values[0]
            if score > 0 or sell_score > 0:
                qualified_stocks.append({
                    "Symbol": ticker,
                    # "MarketCap":market_cap,
                    "Today Close": today_close,
                    "Yday_High": yday_high,
                    "Yday_Low": yday_low,
                    "Today Volume": today_vol,
                    "Yesterday Volume": yday_vol,
                    "EMA20": ema20,
                    "EMA7":ema7,
                    "CPR_Trend": cpr_trend,
                    "CPR_Type": cpr_type,
                    "Latest_CPR_Trend":latest_cpr_trend,
                    "PreBreakout":PreBreakout,
                    "PreBreakdown":PreBreakdown,
                    "Latest_Swing_High": latest_swing_high,
                    "Latest_Swing_Low": latest_swing_low,
                    # "Score": score,
                    # "SellScore": sell_score,
                     "S1":S1,
                     "R1":R1,
                     "S2":S2,
                     "R2":R2,
                    **conditions
                })
            
        except Exception as e:
            print(f"⚠️ Error processing {ticker}: {e}")
            continue
        progress_bar.progress((idx + 1) / total)
            # ---- Final Result ----
    result_df = pd.DataFrame(qualified_stocks)

    # breakout_filter = st.multiselect(
    # "Select Breakout (Yes/No)",
    # options=result_df["CPR Type"].unique(),
    # default=result_df["CPR Type"].unique()
    # )

    # filtered_df =result_df["Breakout"].isin(breakout_filter)


    if not result_df.empty:
       # result_df = result_df.sort_values(by="Score", ascending=False)
        filterd_df = result_df
        #print(result_df.to_string(index=False))
         # Apply yesterday breakout filter
        if yday_breakout_filter == "Close > Yday High":
           #result_df = result_df[result_df["Close > Yday High"] == True]
           filterd_df = filterd_df[filterd_df["Close > Yday High"] == True]
        if yday_breakout_filter == "Close < Yday Low":
           filterd_df = filterd_df[filterd_df["Close < Yday Low"] == True]  
         # Apply EMA filter
          # ✅ Apply EMA filter
            # EMA filter
        if EMA_filter == "Close > EMA20":
            filterd_df = filterd_df[filterd_df["Close > EMA20"] == True]
        elif EMA_filter == "Close > EMA7":
            filterd_df = filterd_df[filterd_df["Close > EMA7"] == True]

        if EMA_filter == "Close < EMA20":
            filterd_df = filterd_df[filterd_df["Close < EMA20"] == True]   

        if EMA_filter == "Close < EMA7":
            filterd_df = filterd_df[filterd_df["Close < EMA7"] == True]       
        

        if CPR_ASC_DESC == "Asc":
           filterd_df = filterd_df[filterd_df["CPR_Trend"] == "Ascending"]

        if CPR_ASC_DESC == "Desc":
           filterd_df = filterd_df[filterd_df["CPR_Trend"] == "Descending"] 

        if CPR_ASC_DESC == "Asc":
           filterd_df = filterd_df[filterd_df["Latest_CPR_Trend"] == "Ascending"]

        if CPR_ASC_DESC == "Desc":
           filterd_df = filterd_df[filterd_df["Latest_CPR_Trend"] == "Descending"]   

        # Apply Volume filter
        if Volume_filter == "Vol > Yday Vol":
            filterd_df = filterd_df[filterd_df["Vol > Yday Vol"] == True]
        elif Volume_filter == "Vol > 5d Avg":
           filterd_df = filterd_df[filterd_df["Vol > 5d Avg"] == True]   
        elif Volume_filter == "Vol > 2*Avg":
           filterd_df = filterd_df[filterd_df["Vol > 2*Avg"] == True]    
        # ---- Save to CSV ----

        
        filterd_df.rename(columns={
             "CPR_Trend": "Swing_CPR",
            
            "Latest_CPR_Trend":"Intraday_CPR"
           
        }, inplace=True)
           
        filename = f"breakout_results_{today}.csv"
        filterd_df.to_csv(filename, index=False)
        print(f"\n✅ Results saved to {filename}")
    else:
        print("⚠️ No stocks qualified.")


                        
            # # Ascending CPR check
            # if not (y_pivot > dby_pivot and y_bc > dby_bc and y_tc > dby_tc):
            #     continue

            # # ---- Step 2: Intraday 5-min ----
            # intraday = yf.download(ticker, period="1d", interval="5m")
            # if intraday is None or intraday.empty:
            #     continue

            # intraday = intraday.reset_index()

            # # First 5-min candle
            # first_candle = intraday.iloc[0]
            # first_open = float(first_candle["Open"])
            # first_close = float(first_candle["Close"])
            # yday_high = float(daily["High"].iloc[-2])

            # # first_open = first_candle["Open"]
            # # first_close = first_candle["Close"]

            # # Breakout check (close above open + above yesterday's high)
            # #if (first_close > first_open) and (first_close > yday_high):
            # if first_close > yday_high :   
            #     qualified_stocks.append({
            #         "Symbol": ticker,
            #         "First Open": first_open,
            #         "First Close": first_close,
            #         "Yesterday High": yday_high,
            #         "CPR Trend": cpr_trend,
            #         "CPR-Type" :cpr_type
            #     })

      

        #progress_bar.progress((idx + 1) / total)

    # --------------------------
    # Step 3: Results
    # --------------------------
    if qualified_stocks:
        st.success("✅ Stocks satisfying conditions:")
        result_df = pd.DataFrame(qualified_stocks)
        st.dataframe(filterd_df)
        # result_df = pd.DataFrame(qualified_stocks, columns=["Qualified Stocks"])
        # st.dataframe(result_df)

        # Save to CSV
        csv_file = "qualified_stocks.csv"
        result_df.to_csv(csv_file, index=False)

        # # Download link
        # st.download_button(
        #     label="📥 Download Qualified Stocks CSV",
        #     data=result_df.to_csv(index=False).encode("utf-8"),
        #     file_name="qualified_stocks.csv",
        #     mime="text/csv"
        # )
    else:
        st.error("❌ No stocks satisfied the conditions today.")

   
        progress_bar.progress((idx + 1) / total)

    # # ---- Final Output ----
    # st.subheader("✅ Qualified Stocks (Ascending CPR + Breakout)")
    # if qualified_stocks:
    #     st.write(qualified_stocks)
    # else:
    #     st.write("No stocks matched the criteria today.")


# end of today'cpr data
# comment code this
# uploaded_file = st.file_uploader("📂 Upload your stock list CSV", type=["csv"])

# if uploaded_file is not None:

#     stocks_df = pd.read_csv(uploaded_file)
#     stocks = stocks_df["Symbol"].tolist()

#     # Results list
#     qualified_stocks = []

#     # Today's date
#     today = datetime.today().date()

#     progress_bar = st.progress(0)
#     total = len(stocks)

#     for idx, ticker in enumerate(stocks):
#         try:
#             # --------------------------
#             # Step 1: Daily Data for CPR
#             # --------------------------
#             daily = yf.download(ticker, period="15d", interval="1d")
#             #daily = daily[daily.index.date < today]

#             if len(daily) == 0:
#                 continue  # not enough data

#             # Yesterday's OHLC
#             yday_high = float(daily["High"].iloc[-2])
#             #st.write("Ydayhigh",yday_high)
#             yday_low = float(daily["Low"].iloc[-2])
#             yday_close = float(daily["Close"].iloc[-2])

#             # CPR Calculation
#             P = (yday_high + yday_low + yday_close) / 3
#             BC = (yday_high + yday_low) / 2
#             TC = 2 * P - BC

#             # Check ascending CPR
#             if not (BC < P < TC):
#                 continue

#             # --------------------------
#             # Step 2: Intraday 5-min Data
#             # --------------------------
#             intraday = yf.download(
#                 ticker,
#                 start=daily.index[-1].date(),
#                 end=daily.index[-1].date() + timedelta(days=1),
#                 interval="5m"
#             ).reset_index()

#             if intraday.empty:
#                 continue

#             # First 5-min candle
#             first_candle = intraday.iloc[0]
#             first_open = float(first_candle["Open"])
#             first_close = float(first_candle["Close"])

#             # Check condition
#             if (first_close > first_open) and (first_close > yday_high):
#                 qualified_stocks.append(ticker)

#         except Exception as e:
#             st.warning(f"⚠️ Error processing {ticker}: {e}")
#             continue

#         progress_bar.progress((idx + 1) / total)

#     # --------------------------
#     # Step 3: Results
#     # --------------------------
#     if qualified_stocks:
#         st.success("✅ Stocks satisfying conditions:")
#         result_df = pd.DataFrame(qualified_stocks, columns=["Qualified Stocks"])
#         st.dataframe(result_df)

#         # Save to CSV
#         csv_file = "qualified_stocks.csv"
#         result_df.to_csv(csv_file, index=False)

#         # Download link
#         st.download_button(
#             label="📥 Download Qualified Stocks CSV",
#             data=result_df.to_csv(index=False).encode("utf-8"),
#             file_name="qualified_stocks.csv",
#             mime="text/csv"
#         )
#     else:
#         st.error("❌ No stocks satisfied the conditions today.")
# else:
#     st.info("👆 Please upload a stock list CSV file (with a 'Symbol' column).")    
# Put input widgets inside col1
col1, col2, col3, col4 = st.columns([1, 1, 1, 1,])
with col1:
    ticker = st.text_input("Enter Stock Symbol (e.g., ASIANPAINT.NS):", "ASIANPAINT.NS")
with col2:
     period = st.text_input("Enter Daily Data Period (e.g., 30d):", "30d")
with col3:
     intraday_interval = st.selectbox("Intraday Interval:", ["2m","5m", "15m", "30m", "60m"], index=0)
with col4:
     vol_filter = st.selectbox("Apply Volume Breakout Filter?", ["No", "Yes"], index=0)
# with col5:    
#      yday_breakout_filter = st.selectbox("Filter Yesterday High Breakout?", ["No", "Yes"], index=0) 
       

# --------------------------
# Run Analysis
# --------------------------
if st.button("Run Analysis"):

    # --------------------------
    # Step 1: Daily Data (Yesterday + Day Before Yesterday)
    # --------------------------
    daily = yf.download(ticker, period="7d", interval="1d")
    if daily.empty or len(daily) < 3:
        st.error("Not enough daily data to calculate CPR trend.")
        st.stop()

    # Remove today if market not closed
    daily = daily[daily.index.date < datetime.today().date()]

    # Yesterday and Day Before Yesterday
    yday = daily.iloc[-1]
    dby = daily.iloc[-2]

    # --------------------------
    # Step 2: Yesterday CPR
    # --------------------------
    y_high = float(yday["High"])
    y_low = float(yday["Low"])
    y_close = float(yday["Close"])

    pivot_y = (y_high + y_low + y_close) / 3
    bc_y = (y_high + y_low) / 2
    tc_y = 2 * pivot_y - bc_y

    r1 = (2 * pivot_y) - y_low
    s1 = (2 * pivot_y) - y_high
    r2 = pivot_y + (y_high - y_low)
    s2 = pivot_y - (y_high - y_low)

    # --------------------------
    # Step 3: Day Before Yesterday CPR (Trend Check)
    # --------------------------
    dby_high = float(dby["High"])
    dby_low = float(dby["Low"])
    dby_close = float(dby["Close"])

    pivot_dby = (dby_high + dby_low + dby_close) / 3
    bc_dby = (dby_high + dby_low) / 2
    tc_dby = 2 * pivot_dby - bc_dby

    # CPR Trend
    if bc_y > bc_dby and tc_y > tc_dby:
        cpr_trend_summary = "📈 Ascending CPR (Bullish)"
    elif bc_y < bc_dby and tc_y < tc_dby:
        cpr_trend_summary = "📉 Descending CPR (Bearish)"
    else:
        cpr_trend_summary = "⚖️ Sideways / Neutral"

    st.write(f"**Yesterday CPR:** Pivot={pivot_y:.2f}, BC={bc_y:.2f}, TC={tc_y:.2f}")
    st.write(f"R1={r1:.2f}, R2={r2:.2f}, S1={s1:.2f}, S2={s2:.2f}")
    st.info(f"**CPR Trend (Yesterday vs Day-Before):** {cpr_trend_summary}")
 
    # --------------------------
    # Step 4: Today's Intraday Data
    # --------------------------
    today = datetime.today().date()
    intraday = yf.download(
        ticker,
        start=today,
        end=today + timedelta(days=1),
        interval=intraday_interval
    ).reset_index()

    if intraday.empty:
        st.error("No intraday data found for today.")
        st.stop()

    # Drop MultiIndex columns if any
    if isinstance(intraday.columns, pd.MultiIndex):
        intraday.columns = intraday.columns.get_level_values(0)

    intraday = intraday.dropna(subset=["Open", "High", "Low", "Close"])

    # Convert timezone
    tz = "Asia/Kolkata" if ticker.endswith(".NS") else "America/New_York"
    intraday["Datetime"] = pd.to_datetime(intraday["Datetime"], utc=True).dt.tz_convert(tz)

    # --------------------------
    # Step 5: Intraday CPR Signals
    # --------------------------
    # Trend based on yesterday's CPR
    def get_cpr_trend(price):
        if price > tc_y:
            return "📈 Bullish"
        elif price < bc_y:
            return "📉 Bearish"
        else:
            return "⚖️ Neutral"

    intraday["Latest_CPR_Trend"] = intraday["Close"].apply(get_cpr_trend)
    # Get the latest candle's trend
    latest_trend = intraday["Latest_CPR_Trend"].iloc[-1]  # last row = most recent

# Show in Streamlit
    st.info(f"**Latest Intraday CPR Trend:** {latest_trend}")
    # Breakout / Breakdown detection
    intraday["Breakout"] = intraday["Close"] > y_high
    intraday["Breakdown"] = intraday["Close"] < y_low

#     # --------------------------
# # First Candle Logic
# # --------------------------
    first_candle = intraday.iloc[0]  # first intraday candle
    first_close = float(first_candle["Close"])
    first_open = float(first_candle["Open"])
# first_volume = first_candle["Volume"]

# # # First candle CPR trend
    first_candle_trend = get_cpr_trend(first_close)

# # Breakout / Breakdown for first candle
    first_breakout = False
    first_breakdown = False

    # Check breakout
    if first_close > y_high:
        first_breakout = True
    else:
        first_breakout = False

    # Check breakdown
    if first_close < y_low:
        
        first_breakdown = True
    else:
        first_breakdown = False

    # Display in Streamlit
    # st.write(f"**First Candle Close:** {first_close:.2f}")
    st.write(f"**First Candle Close:** {first_close:.2f} | **Current CPR Trend:** {latest_trend} | **Latest Price:** {intraday['Close'].iloc[-1]:.2f}")
    if first_breakout:
        st.success(f"✅ First candle breakout confirmed above yesterday's high ({y_high:.2f})")
    elif first_breakdown:
        st.warning(f"⚠️ First candle breakdown below yesterday's low ({y_low:.2f})")
    else:
        st.info("No breakout/breakdown on first candle")

    # Apply volume filter if selected
    if vol_filter == "Yes":
        avg_vol = intraday["Volume"].rolling(5).mean()
        intraday["Breakout"] = intraday["Breakout"] & (intraday["Volume"] > avg_vol)
        intraday["Breakdown"] = intraday["Breakdown"] & (intraday["Volume"] > avg_vol)

#     # st.dataframe(intraday[["Datetime", "Close", "CPR_Trend", "Breakout", "Breakdown"]].tail(20))
#     st.dataframe(
#     intraday[["Datetime", "Close", "Latest_CPR_Trend", "Breakout", "Breakdown"]]
#     .sort_values(by="Datetime", ascending=False)  # latest first
#     .head(5)
# )

    # --------------------------
    # Step 6: Plot Intraday Candles + CPR
    # --------------------------
    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=intraday["Datetime"],
        open=intraday["Open"],
        high=intraday["High"],
        low=intraday["Low"],
        close=intraday["Close"],
        name="Candles"
    ))

    # CPR Zone
    fig.add_shape(
        type="rect",
        x0=intraday["Datetime"].iloc[0],
        x1=intraday["Datetime"].iloc[-1],
        y0=bc_y,
        y1=tc_y,
        fillcolor="green",
        opacity=0.2,
        layer="below",
        line_width=0
    )

    # R1, R2, S1, S2 Lines
    fig.add_hline(y=r1, line=dict(color="purple", dash="dot"), annotation_text=f"R1 {r1:.2f}")
    fig.add_hline(y=r2, line=dict(color="purple", dash="dot"), annotation_text=f"R2 {r2:.2f}")
    fig.add_hline(y=s1, line=dict(color="red", dash="dot"), annotation_text=f"S1 {s1:.2f}")
    fig.add_hline(y=s2, line=dict(color="red", dash="dot"), annotation_text=f"S2 {s2:.2f}")

    # Highlight Breakouts / Breakdowns
    fig.add_trace(go.Scatter(
        x=intraday.loc[intraday["Breakout"], "Datetime"],
        y=intraday.loc[intraday["Breakout"], "Close"],
        mode="markers",
        marker=dict(color="orange", size=12, symbol="star"),
        name="Breakout"
    ))

    fig.add_trace(go.Scatter(
        x=intraday.loc[intraday["Breakdown"], "Datetime"],
        y=intraday.loc[intraday["Breakdown"], "Close"],
        mode="markers",
        marker=dict(color="red", size=12, symbol="x"),
        name="Breakdown"
    ))

    fig.update_layout(
        title=f"{ticker} - Intraday CPR Analysis ({intraday_interval})",
        xaxis_title=f"Time ({tz})",
        yaxis_title="Price",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600,
        xaxis=dict(type="date", tickformat="%H:%M")
    )

    st.plotly_chart(fig, use_container_width=True)