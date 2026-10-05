from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio

BASE=Path(__file__).parent
D=BASE/'data'
content=pd.read_csv(D/'content_detail.csv')
content=content[content['Content'].astype(str)!='Total'].copy()
for c in ['Views','Watch time (hours)','Subscribers gained','Subscribers lost','Average percentage viewed (%)','Stayed to watch (%)','Thumbnail click-through rate (%)','Likes','Comments added','Shares']:
    content[c]=pd.to_numeric(content[c],errors='coerce')
source=pd.read_csv(D/'subscription_source.csv')
newret=pd.read_csv(D/'new_returning.csv')
substat=pd.read_csv(D/'subscription_status.csv')
views=pd.read_csv(D/'daily_views.csv')
views['Date']=pd.to_datetime(views['Date'],errors='coerce'); views['Views']=pd.to_numeric(views['Views'],errors='coerce').fillna(0)
views=views.dropna().sort_values('Date'); views['30-day views']=views['Views'].rolling(30,min_periods=1).sum()
subs=pd.read_csv(D/'daily_subscribers.csv')
subs['Date']=pd.to_datetime(subs['Date'],errors='coerce'); subs['Subscribers']=pd.to_numeric(subs['Subscribers'],errors='coerce').fillna(0)
subs=subs.dropna().sort_values('Date'); subs['30-day net subs']=subs['Subscribers'].rolling(30,min_periods=1).sum()

total=pd.read_csv(D/'content_detail.csv').iloc[0]
total_views=float(total['Views']); watch=float(total['Watch time (hours)']); net=float(total['Subscribers']); gross=float(total['Subscribers gained'])
ad=float(source.loc[source['Subscription source']=='YouTube advertising','Subscribers gained'].iloc[0])
organic=gross-ad
nr=newret.set_index('New and Returning Viewers'); ret_share=float(nr.loc['Returning viewers','Views'])/float(nr.loc['Total','Views'])*100

fig1=px.line(views,x='Date',y='30-day views',title='Rolling 30-day views')
fig2=px.line(subs,x='Date',y='30-day net subs',title='Rolling 30-day net subscribers')
nr2=newret[newret['New and Returning Viewers']!='Total']
fig3=px.pie(nr2,names='New and Returning Viewers',values='Views',hole=.45,title='New vs returning views')
src=source[source['Subscription source']!='Total'].copy()
fig4=px.bar(src,x='Subscription source',y='Subscribers gained',title='Subscribers gained by source')
top=content.sort_values('Views',ascending=False).head(15)
fig5=px.bar(top,x='Views',y='Video title',orientation='h',title='Top 15 videos by views')
fig5.update_layout(yaxis={'categoryorder':'total ascending'},height=650)

def div(fig): return pio.to_html(fig,full_html=False,include_plotlyjs=False)

html=f'''<!doctype html><html><head><meta charset="utf-8"><title>HyperWumpus YouTube Analytics Snapshot</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#171717}}.wrap{{max-width:1400px;margin:auto;padding:28px}}.kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}}.card{{background:white;border-radius:14px;padding:18px;box-shadow:0 1px 5px #00000012}}.num{{font-size:28px;font-weight:700}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}}.full{{margin-top:18px}}.warn{{background:#fff4dd;border:1px solid #f4d18a;padding:14px;border-radius:12px;margin:18px 0}}@media(max-width:900px){{.kpis,.grid{{grid-template-columns:1fr}}}}</style></head><body><div class="wrap">
<h1>HyperWumpus YouTube Analytics — Snapshot</h1><p>Generated from the YouTube Studio exports currently in the audit.</p>
<div class="kpis"><div class="card"><div>Lifetime views</div><div class="num">{total_views:,.0f}</div></div><div class="card"><div>Watch time</div><div class="num">{watch:,.1f} h</div></div><div class="card"><div>Net subscribers</div><div class="num">{net:,.0f}</div></div><div class="card"><div>Non-ad subs gained</div><div class="num">{organic:,.0f}</div></div><div class="card"><div>Returning-view share</div><div class="num">{ret_share:.1f}%</div></div></div>
<div class="warn"><b>Paid acquisition context:</b> YouTube advertising accounts for {ad/gross*100:.1f}% of gross subscribers gained in the subscription-source report. Raw subscriber totals should not be treated as the active audience size.</div>
<div class="grid"><div class="card">{div(fig1)}</div><div class="card">{div(fig2)}</div></div>
<div class="grid"><div class="card">{div(fig3)}</div><div class="card">{div(fig4)}</div></div>
<div class="card full">{div(fig5)}</div>
</div></body></html>'''
(BASE/'snapshot_dashboard.html').write_text(html,encoding='utf-8')
print(BASE/'snapshot_dashboard.html')
