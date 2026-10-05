from pathlib import Path
import io
import re
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='HyperWumpus YouTube Analytics', page_icon='📊', layout='wide')

BASE = Path(__file__).parent
DATA = BASE / 'data'

PROMOTED_SIGNATURES = [
    'is marvel rivals better than overwatch',
    'warhammer titan',
    'avenging all of my fallen comrades',
    'jujutsu kaisen s2 ep 1 reaction',
    "i forgot i don’t live in texas anymore",
    "i forgot i don't live in texas anymore",
    'after missing my old stray cat',
    'i opened my roommate’s stuff',
    "i opened my roommate's stuff",
    'we were bonding',
    'denji’s heartbreak',
    "denji's heartbreak",
    'when your own brain won’t leave you alone',
    "when your own brain won't leave you alone",
    'rage baiting 101',
    'when the adhd randomly kicks in',
    'my top 5 stranger things predictions',
    'todoroki motivation',
    'no phantasmal flames',
    'feeling alone on my birthday',
    'i handed out pokémon packs',
    'i handed out pokemon packs',
    'recording a pokémon pack opening while driving',
    'recording a pokemon pack opening while driving',
    'he came back again',
    'jujutsu kaisen: execution movie trailer',
    'chainsaw man edit',
    'i opened a paradox rift',
    'we hit 100 subscribers',
    'pokeball unboxing with dante',
    'opening packs with strangers ep. 1',
    'opening packs with strangers ep. 2',
]


def read_csv_any(obj):
    try:
        return pd.read_csv(obj)
    except UnicodeDecodeError:
        if hasattr(obj, 'seek'):
            obj.seek(0)
        return pd.read_csv(obj, encoding='latin-1')


def detect_kind(df):
    c = set(df.columns)
    if {'Video title', 'Subscribers gained', 'Subscribers lost'}.issubset(c):
        return 'content'
    if 'New and Returning Viewers' in c:
        return 'new_returning'
    if 'Subscription status' in c:
        return 'subscription_status'
    if 'Subscription source' in c:
        return 'subscription_source'
    if c == {'Date', 'Views'} or {'Date', 'Views'}.issubset(c) and len(c) <= 3:
        return 'daily_views'
    if c == {'Date', 'Subscribers'} or {'Date', 'Subscribers'}.issubset(c) and len(c) <= 3:
        return 'daily_subscribers'
    return None


def load_bundled():
    mapping = {
        'content': DATA / 'content_detail.csv',
        'new_returning': DATA / 'new_returning.csv',
        'subscription_status': DATA / 'subscription_status.csv',
        'subscription_source': DATA / 'subscription_source.csv',
        'daily_views': DATA / 'daily_views.csv',
        'daily_subscribers': DATA / 'daily_subscribers.csv',
    }
    out = {}
    for kind, path in mapping.items():
        if path.exists():
            out[kind] = read_csv_any(path)
    return out


def norm_text(s):
    return re.sub(r'\s+', ' ', str(s).lower().strip())


def is_promoted(title):
    t = norm_text(title)
    return any(sig in t for sig in PROMOTED_SIGNATURES)


def category(title):
    t = norm_text(title)
    rules = [
        ('Cats / Animals', ['stray cat', 'kitty', 'cat saga', 'kitten']),
        ('Pokémon', ['pokemon', 'pokémon', 'pokeball', 'pokéball', 'paradox rift', 'mega evolution', 'phantasmal']),
        ('Stranger Things', ['stranger things', 'will’s mind', "will's mind", 'netflix intro']),
        ('Anime / Manga', ['chainsaw', 'denji', 'makima', 'jujutsu', 'jjk', 'naruto', 'todoroki', 'mha', 'attack on titan', 'aot', 'anime', 'manga']),
        ('Gaming', ['overwatch', 'genji', 'marvel rivals', 'halo', 'gaming', 'gameplay', 'stream vod', 'first stream']),
        ('Personal / Mindset', ['birthday', 'adhd', 'heartbreak', 'alone', 'brain', 'motivation', 'life', 'lonely', 'mindset']),
        ('Comedy / Meme', ['rage bait', 'smiling friends', 'pov:', 'meme', 'funny']),
    ]
    for name, words in rules:
        if any(w in t for w in words):
            return name
    return 'Other / Variety'


def duration_to_seconds(v):
    if pd.isna(v):
        return np.nan
    if isinstance(v, (int, float, np.number)):
        return float(v)
    try:
        parts = [float(x) for x in str(v).split(':')]
        if len(parts) == 3:
            return parts[0]*3600 + parts[1]*60 + parts[2]
        if len(parts) == 2:
            return parts[0]*60 + parts[1]
        return float(parts[0])
    except Exception:
        return np.nan


def content_type(row):
    title = norm_text(row.get('Video title', ''))
    hours_streamed = pd.to_numeric(pd.Series([row.get('Hours streamed', 0)]), errors='coerce').fillna(0).iloc[0]
    dur = pd.to_numeric(pd.Series([row.get('Duration', np.nan)]), errors='coerce').iloc[0]
    if hours_streamed > 0 or 'livestream' in title or 'stream vod' in title or title.endswith(' stream'):
        return 'Live / VOD'
    if pd.notna(dur) and dur <= 60:
        return 'Short'
    return 'Long-form'


def enrich_content(df):
    df = df.copy()
    df = df[df['Content'].astype(str) != 'Total'].copy()
    if 'Video publish time' in df:
        df['Publish date'] = pd.to_datetime(df['Video publish time'], errors='coerce')
    else:
        df['Publish date'] = pd.NaT
    numeric_cols = [
        'Views','Watch time (hours)','Subscribers','Subscribers gained','Subscribers lost','Likes','Dislikes',
        'Comments added','Shares','Thumbnail impressions','Thumbnail click-through rate (%)','Engaged views',
        'Stayed to watch (%)','Average percentage viewed (%)','Unique viewers','Unique reach','Returning viewers','New viewers',
        'Hours streamed'
    ]
    for c in numeric_cols:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        else:
            df[c] = np.nan
    df['Category'] = df['Video title'].map(category)
    df['Content type'] = df.apply(content_type, axis=1)
    df['Known promoted'] = df['Video title'].map(is_promoted)
    v = df['Views'].replace(0, np.nan)
    df['Subs gained / 1K views'] = df['Subscribers gained'] / v * 1000
    df['Net subs / 1K views'] = df['Subscribers'] / v * 1000
    df['Engagement rate (%)'] = (df['Likes'].fillna(0) + df['Comments added'].fillna(0) + df['Shares'].fillna(0)) / v * 100
    df['Watch hrs / 1K views'] = df['Watch time (hours)'] / v * 1000
    # Organic-ish score excludes known promoted videos from leaderboard comparisons.
    base = df[~df['Known promoted'] & (df['Views'] >= 50)].copy()
    if len(base):
        for col, new in [
            ('Views','_reach'),('Average percentage viewed (%)','_ret'),
            ('Engagement rate (%)','_eng'),('Subs gained / 1K views','_conv')]:
            ranks = base[col].rank(pct=True, method='average')
            df.loc[base.index, new] = ranks
        df['Organic opportunity score'] = 100*(0.20*df['_reach'] + 0.30*df['_ret'] + 0.25*df['_eng'] + 0.25*df['_conv'])
    else:
        df['Organic opportunity score'] = np.nan
    return df


def money_or_num(x, digits=0):
    if pd.isna(x): return '—'
    return f'{x:,.{digits}f}'


def pct(x, digits=1):
    if pd.isna(x): return '—'
    return f'{x:.{digits}f}%'


def compact_int(x):
    if pd.isna(x): return '—'
    x = float(x)
    if abs(x) >= 1_000_000: return f'{x/1_000_000:.1f}M'
    if abs(x) >= 1_000: return f'{x/1_000:.1f}K'
    return f'{x:.0f}'


def kpi(label, value, help_text=None):
    st.metric(label, value, help=help_text)


# ---------- Load data ----------
datasets = load_bundled()

st.sidebar.title('📁 Data')
st.sidebar.caption('Upload YouTube Studio CSV exports in any order. The app auto-detects the report type and replaces the bundled snapshot for that report.')
uploads = st.sidebar.file_uploader('Drop CSV exports here', type=['csv'], accept_multiple_files=True)
detected = []
for f in uploads or []:
    try:
        dfu = read_csv_any(f)
        kind = detect_kind(dfu)
        if kind:
            datasets[kind] = dfu
            detected.append(f'{f.name} → {kind}')
        else:
            detected.append(f'{f.name} → unrecognized')
    except Exception as e:
        detected.append(f'{f.name} → error: {e}')
if detected:
    st.sidebar.success('Detected uploads')
    for d in detected:
        st.sidebar.caption(d)
else:
    st.sidebar.info('Using your bundled current snapshot.')

content = enrich_content(datasets['content']) if 'content' in datasets else pd.DataFrame()

st.sidebar.divider()
st.sidebar.title('🔎 Filters')
exclude_promoted = st.sidebar.checkbox('Exclude known promoted videos from organic analysis', value=True)
search = st.sidebar.text_input('Title contains', '')
category_opts = sorted(content['Category'].dropna().unique()) if len(content) else []
chosen_categories = st.sidebar.multiselect('Categories', category_opts, default=category_opts)
type_opts = sorted(content['Content type'].dropna().unique()) if len(content) else []
chosen_types = st.sidebar.multiselect('Content types', type_opts, default=type_opts)

filtered = content.copy()
if search:
    filtered = filtered[filtered['Video title'].str.contains(search, case=False, na=False)]
if chosen_categories:
    filtered = filtered[filtered['Category'].isin(chosen_categories)]
if chosen_types:
    filtered = filtered[filtered['Content type'].isin(chosen_types)]
organic_filtered = filtered[~filtered['Known promoted']] if exclude_promoted else filtered

# ---------- Header ----------
st.title('📊 HyperWumpus YouTube Analytics')
st.caption('A local-first dashboard built around your YouTube Studio exports. It is designed to separate reach, loyalty, conversion, and paid-acquisition effects.')

# exact summary data
source = datasets.get('subscription_source', pd.DataFrame())
newret = datasets.get('new_returning', pd.DataFrame())
substat = datasets.get('subscription_status', pd.DataFrame())

# ---------- tabs ----------
tabs = st.tabs(['Overview','Content Lab','Audience','Subscriber Sources','Compare','Strategy'])

with tabs[0]:
    if content.empty:
        st.warning('Upload a detailed Content report to use this tab.')
    else:
        total_row = datasets['content'][datasets['content']['Content'].astype(str) == 'Total']
        if len(total_row):
            tr = total_row.iloc[0]
            total_views = float(tr.get('Views', np.nan))
            watch = float(tr.get('Watch time (hours)', np.nan))
            net_subs = float(tr.get('Subscribers', np.nan))
            gross = float(tr.get('Subscribers gained', np.nan))
        else:
            total_views = content['Views'].sum()
            watch = content['Watch time (hours)'].sum()
            net_subs = content['Subscribers'].sum()
            gross = content['Subscribers gained'].sum()

        ad_gained = np.nan
        if not source.empty and 'YouTube advertising' in set(source['Subscription source']):
            ad_gained = float(source.loc[source['Subscription source']=='YouTube advertising','Subscribers gained'].iloc[0])
        organic_gained = gross - ad_gained if pd.notna(ad_gained) else np.nan

        returning_share = np.nan
        if not newret.empty:
            nrv = newret.set_index('New and Returning Viewers')
            if 'Returning viewers' in nrv.index and 'Total' in nrv.index:
                returning_share = float(nrv.loc['Returning viewers','Views']) / float(nrv.loc['Total','Views']) * 100

        cols = st.columns(5)
        with cols[0]: kpi('Lifetime views', compact_int(total_views))
        with cols[1]: kpi('Watch time', f'{watch:,.1f} h')
        with cols[2]: kpi('Net subscribers', compact_int(net_subs))
        with cols[3]: kpi('Non-ad subs gained', compact_int(organic_gained), 'Gross subscribers gained minus YouTube advertising subscribers. This is channel-level, not per-video attribution.')
        with cols[4]: kpi('Returning-view share', pct(returning_share), 'Share of lifetime views from returning viewers in the New vs Returning report.')

        if pd.notna(ad_gained) and gross:
            ad_share = ad_gained/gross*100
            st.warning(f'Paid-acquisition context: {ad_share:.1f}% of gross subscribers gained in your subscription-source report came from YouTube advertising. Treat raw subscriber conversion on promoted videos cautiously.')

        c1, c2 = st.columns(2)
        with c1:
            dv = datasets.get('daily_views', pd.DataFrame()).copy()
            if len(dv):
                dv['Date'] = pd.to_datetime(dv['Date'], errors='coerce')
                dv['Views'] = pd.to_numeric(dv['Views'], errors='coerce').fillna(0)
                dv = dv.dropna(subset=['Date']).sort_values('Date')
                dv['30-day views'] = dv['Views'].rolling(30, min_periods=1).sum()
                fig = px.line(dv, x='Date', y='30-day views', title='Rolling 30-day views')
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            ds = datasets.get('daily_subscribers', pd.DataFrame()).copy()
            if len(ds):
                ds['Date'] = pd.to_datetime(ds['Date'], errors='coerce')
                ds['Subscribers'] = pd.to_numeric(ds['Subscribers'], errors='coerce').fillna(0)
                ds = ds.dropna(subset=['Date']).sort_values('Date')
                ds['30-day net subs'] = ds['Subscribers'].rolling(30, min_periods=1).sum()
                fig = px.line(ds, x='Date', y='30-day net subs', title='Rolling 30-day net subscribers')
                st.plotly_chart(fig, use_container_width=True)

        st.subheader('Top content by views')
        cols_show = ['Video title','Category','Content type','Known promoted','Views','Watch time (hours)','Subscribers gained','Average percentage viewed (%)','Stayed to watch (%)']
        top = filtered.sort_values('Views', ascending=False).head(15)[cols_show]
        st.dataframe(top, use_container_width=True, hide_index=True)

with tabs[1]:
    st.subheader('Content Lab')
    st.caption('By default, organic opportunity analysis excludes videos we know you promoted. You can change that in the sidebar.')
    if filtered.empty:
        st.info('No videos match the current filters.')
    else:
        xcol = st.selectbox('X axis', ['Views','Thumbnail click-through rate (%)','Average percentage viewed (%)','Stayed to watch (%)','Engagement rate (%)'])
        ycol = st.selectbox('Y axis', ['Subs gained / 1K views','Average percentage viewed (%)','Engagement rate (%)','Watch hrs / 1K views'], index=0)
        plotdf = organic_filtered.dropna(subset=[xcol,ycol]).copy()
        if len(plotdf):
            fig = px.scatter(plotdf, x=xcol, y=ycol, size='Views', hover_name='Video title', color='Category',
                             symbol='Content type', title=f'{ycol} vs {xcol}')
            st.plotly_chart(fig, use_container_width=True)

        st.subheader('Organic opportunity leaderboard')
        leader = organic_filtered.dropna(subset=['Organic opportunity score']).sort_values('Organic opportunity score', ascending=False)
        leader_cols = ['Video title','Category','Content type','Views','Average percentage viewed (%)','Engagement rate (%)','Subs gained / 1K views','Organic opportunity score']
        st.dataframe(leader[leader_cols].head(20), use_container_width=True, hide_index=True)

        st.subheader('All content')
        table_cols = ['Video title','Publish date','Category','Content type','Known promoted','Views','Watch time (hours)','Average percentage viewed (%)','Stayed to watch (%)','Thumbnail click-through rate (%)','Likes','Comments added','Shares','Subscribers gained','Subscribers lost','Subs gained / 1K views','Engagement rate (%)']
        st.dataframe(filtered[table_cols].sort_values('Views', ascending=False), use_container_width=True, hide_index=True)
        csv = filtered[table_cols].to_csv(index=False).encode('utf-8')
        st.download_button('Download analyzed content CSV', csv, 'hyperwumpus_analyzed_content.csv', 'text/csv')

with tabs[2]:
    st.subheader('Audience Quality')
    c1, c2 = st.columns(2)
    with c1:
        if not newret.empty:
            nr = newret[newret['New and Returning Viewers'] != 'Total'].copy()
            fig = px.pie(nr, names='New and Returning Viewers', values='Views', hole=.45, title='Views: new vs returning')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(nr, use_container_width=True, hide_index=True)
        else:
            st.info('Upload New and Returning Viewers report.')
    with c2:
        if not substat.empty:
            ss = substat[substat['Subscription status'] != 'Total'].copy()
            fig = px.pie(ss, names='Subscription status', values='Views', hole=.45, title='Views: subscribed vs not subscribed')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(ss[['Subscription status','Views','Watch time (hours)','Average view duration','Average percentage viewed (%)']], use_container_width=True, hide_index=True)
        else:
            st.info('Upload Subscription Status report.')

    if not newret.empty:
        nrv = newret.set_index('New and Returning Viewers')
        if 'Returning viewers' in nrv.index and 'New viewers' in nrv.index:
            ret = nrv.loc['Returning viewers']
            new = nrv.loc['New viewers']
            st.markdown('### What this means')
            st.write(f"Returning viewers account for **{ret['Views']/(ret['Views']+new['Views'])*100:.1f}%** of these views, but their average percentage viewed is **{ret['Average percentage viewed (%)']:.1f}%** versus **{new['Average percentage viewed (%)']:.1f}%** for new viewers. That points to a conversion-to-repeat-viewing problem more than a 'returning viewers dislike the content' problem.")

with tabs[3]:
    st.subheader('Subscriber Sources')
    if source.empty:
        st.info('Upload Subscription Source report.')
    else:
        src = source[source['Subscription source'] != 'Total'].copy()
        src['Net'] = pd.to_numeric(src['Subscribers'], errors='coerce')
        melted = src.melt(id_vars='Subscription source', value_vars=['Subscribers gained','Subscribers lost'], var_name='Metric', value_name='Count')
        fig = px.bar(melted, x='Subscription source', y='Count', color='Metric', barmode='group', title='Subscribers gained and lost by source')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(src[['Subscription source','Subscribers gained','Subscribers lost','Net']].sort_values('Subscribers gained', ascending=False), use_container_width=True, hide_index=True)
        total = source[source['Subscription source']=='Total']
        ads = source[source['Subscription source']=='YouTube advertising']
        if len(total) and len(ads):
            gross = float(total['Subscribers gained'].iloc[0]); adg = float(ads['Subscribers gained'].iloc[0])
            st.warning(f'YouTube advertising produced **{adg:,.0f} of {gross:,.0f} gross subscribers gained ({adg/gross*100:.1f}%)** in this report. For strategy decisions, track organic subscribers and returning viewers separately from the headline subscriber total.')

with tabs[4]:
    st.subheader('Compare Videos')
    if content.empty:
        st.info('Upload a detailed content report.')
    else:
        names = content.sort_values('Views', ascending=False)['Video title'].dropna().tolist()
        default = names[:2]
        picks = st.multiselect('Choose 2–5 videos', names, default=default, max_selections=5)
        comp = content[content['Video title'].isin(picks)].copy()
        if len(comp):
            metrics = ['Views','Watch time (hours)','Average percentage viewed (%)','Stayed to watch (%)','Thumbnail click-through rate (%)','Engagement rate (%)','Subs gained / 1K views']
            st.dataframe(comp[['Video title','Known promoted','Category','Content type']+metrics], use_container_width=True, hide_index=True)
            metric = st.selectbox('Compare metric', metrics, index=2)
            fig = px.bar(comp, x='Video title', y=metric, color='Known promoted', title=metric)
            st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.subheader('Strategy Engine')
    st.caption('This is a decision aid, not an oracle. It surfaces patterns worth testing, especially among videos not known to have been promoted.')

    if not content.empty:
        org = content[~content['Known promoted']].copy()
        viable = org[org['Views'] >= 100].copy()

        c1, c2 = st.columns(2)
        with c1:
            st.markdown('### 🟢 Repeat / expand')
            st.write('Unpromoted videos with the strongest combined reach, retention, engagement and subscriber conversion.')
            rep = viable.dropna(subset=['Organic opportunity score']).sort_values('Organic opportunity score', ascending=False).head(8)
            st.dataframe(rep[['Video title','Category','Views','Average percentage viewed (%)','Subs gained / 1K views','Organic opportunity score']], use_container_width=True, hide_index=True)
        with c2:
            st.markdown('### 🟡 Reach without conversion')
            if len(viable):
                qv = viable['Views'].quantile(.75)
                qc = viable['Subs gained / 1K views'].median()
                onehit = viable[(viable['Views'] >= qv) & (viable['Subs gained / 1K views'] <= qc)].sort_values('Views', ascending=False).head(8)
                st.write('These got attention but converted relatively few subscribers per 1K views. Consider adding a stronger recurring premise or identity hook.')
                st.dataframe(onehit[['Video title','Views','Subs gained / 1K views','Average percentage viewed (%)']], use_container_width=True, hide_index=True)

        st.markdown('### 🔧 Packaging opportunities')
        longish = viable[(viable['Thumbnail impressions'] >= 100) & viable['Thumbnail click-through rate (%)'].notna() & viable['Average percentage viewed (%)'].notna()].copy()
        if len(longish):
            ctr_med = longish['Thumbnail click-through rate (%)'].median()
            ret_q = longish['Average percentage viewed (%)'].quantile(.60)
            pack = longish[(longish['Thumbnail click-through rate (%)'] < ctr_med) & (longish['Average percentage viewed (%)'] >= ret_q)].sort_values('Average percentage viewed (%)', ascending=False).head(8)
            st.write('Good relative retention but weaker click-through can mean the content is better than the title/thumbnail packaging.')
            st.dataframe(pack[['Video title','Thumbnail impressions','Thumbnail click-through rate (%)','Average percentage viewed (%)','Views']], use_container_width=True, hide_index=True)

        st.markdown('### 📚 Category snapshot — unpromoted videos')
        if len(org):
            cat = org.groupby('Category', as_index=False).agg(
                Videos=('Content','count'), Views=('Views','sum'), Watch_hours=('Watch time (hours)','sum'),
                Median_retention=('Average percentage viewed (%)','median'), Median_engagement=('Engagement rate (%)','median'),
                Subs_gained=('Subscribers gained','sum')
            )
            cat['Subs / 1K views'] = cat['Subs_gained'] / cat['Views'].replace(0,np.nan)*1000
            cat = cat.sort_values('Views', ascending=False)
            st.dataframe(cat, use_container_width=True, hide_index=True)

        st.markdown('### 🎯 30-day scoreboard')
        st.write('For the reboot, I would track **returning-view share, organic subscribers gained, repeat commenters, average percentage viewed, stayed-to-watch for Shorts, and long-form watch time**. The displayed subscriber total is a secondary metric because paid acquisition dominates its history.')
        st.info('Suggested experiment rule: run a format 3–5 times before killing it. If one version works, improve the recurring premise instead of immediately creating a new channel.')

st.divider()
st.caption('HyperWumpus YouTube Analytics v1 • Runs locally • No YouTube API key required • Built for YouTube Studio CSV exports')
