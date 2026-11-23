#!/usr/bin/env python3
"""Generate one static page per article (posts/<id>.html) plus sitemap.xml.

Source of truth stays in index.html (POSTS + CONTENT). After adding or editing
an article there, run:  python3 tools/build_posts.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://drweipeng.com"
DEFAULT_IMAGE = f"{SITE}/assets/wei-peng-photo.jpg"

src = (ROOT / "index.html").read_text(encoding="utf-8")


def grab(name, closer):
    i = src.index(f"const {name} = ") + len(f"const {name} = ")
    j = src.index(closer, i)
    return src[i:j + 1]


posts = json.loads(grab("POSTS", "];"))
line_end = src.index("\n", src.index("const CONTENT = "))
content = json.loads(src[src.index("const CONTENT = ") + len("const CONTENT = "):line_end].rstrip(";"))
css = src[src.index("<style>") + len("<style>"):src.index("</style>")]
core_cats = set(json.loads(re.search(r"const CORE_CATS = new Set\((\[.*?\])\)", src).group(1)))

PAGE_CSS = """
  .post{max-width:760px;margin:0 auto;padding:36px 24px 56px;}
  .post .back{display:inline-flex;gap:6px;font-size:.86rem;color:var(--accent);text-decoration:none;font-weight:600;margin-bottom:22px;}
  .post .back:hover{text-decoration:underline;}
  .post-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;box-shadow:var(--shadow);overflow:hidden;}
  .post-head{padding:26px 24px 18px;border-bottom:1px solid var(--border);}
  .post-head h1{font-family:'cwTeX Q Kai','Noto Serif TC',serif;font-weight:400;font-size:1.6rem;line-height:1.5;margin:10px 0 0;color:var(--ink-1);}
  .post .modal-body{font-size:1rem;}
  .share-bar{display:flex;flex-wrap:wrap;gap:10px;margin-top:16px;}
  .share-btn{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:999px;font-size:.88rem;font-weight:600;text-decoration:none;border:1px solid var(--border);background:var(--surface);color:var(--ink-1);cursor:pointer;font-family:inherit;line-height:1.2;}
  .share-btn:hover{border-color:var(--accent);}
  .share-btn.line{background:#06C755;border-color:#06C755;color:#fff;}
  .share-btn.line:hover{filter:brightness(.95);}
  .share-bar.bottom{margin-top:22px;padding-top:16px;border-top:1px solid var(--border);}
  .author-box{display:flex;gap:16px;align-items:flex-start;margin-top:24px;padding:18px;border:1px solid var(--border);border-radius:14px;background:var(--surface-2);}
  .author-box img{width:64px;height:64px;border-radius:50%;object-fit:cover;flex:none;}
  .author-box .name{font-weight:700;color:var(--ink-1);margin-bottom:4px;}
  .author-box p{margin:0 0 6px;font-size:.88rem;line-height:1.75;color:var(--ink-2);}
  .author-box a{color:var(--accent);font-weight:600;text-decoration:none;font-size:.88rem;}
  .author-box a:hover{text-decoration:underline;}
  .related{margin-top:28px;}
  .related h2{font-family:'cwTeX Q Kai','Noto Serif TC',serif;font-weight:400;font-size:1.15rem;margin:0 0 10px;color:var(--ink-1);}
  .related ul{margin:0;padding-left:20px;line-height:1.9;}
  .related a{color:var(--accent);text-decoration:none;}
  .related a:hover{text-decoration:underline;}
"""

AUTHOR_HTML = ('<aside class="author-box"><img src="../assets/wei-peng-photo.jpg" alt="王威鵬醫師">'
               '<div><div class="name">王威鵬 醫師</div>'
               '<p>具中、西醫雙執照，臨床著重腰椎、骨盆與膝關節等筋骨疼痛，結合超音波評估與中醫針刀、乾針及動作訓練。'
               '目前於悅衡整合醫學診所（桃園）、民生瀚威中醫診所（台北）看診。</p>'
               '<a href="/#about">關於醫師</a> · <a href="/contact.html">看診地點與門診時間</a></div></aside>')


def related_html(p):
    same = [q for q in posts if q["id"] != p["id"] and q["c"] == p["c"] and str(q["id"]) in content]
    shared = lambda q: len(set(q["tags"]) & set(p["tags"]))
    same.sort(key=lambda q: q["d"], reverse=True)
    same.sort(key=lambda q: -shared(q))
    picks = same[:4]
    if not picks:
        return ""
    items = "".join(f'<li><a href="/posts/{q["id"]}.html">{html.escape(q["t"])}</a></li>' for q in picks)
    return f'<nav class="related"><h2>延伸閱讀</h2><ul>{items}</ul></nav>'



def text_of(fragment):
    t = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def description(body):
    paras = [text_of(p) for p in re.findall(r"<p>(.*?)</p>", body, re.S)]
    text = "".join(paras[:3]) or text_of(body)
    return text[:110] + ("…" if len(text) > 110 else "")


def first_image(body):
    m = re.search(r'<img[^>]+src="([^"]+)"', body)
    if not m:
        return DEFAULT_IMAGE
    s = m.group(1)
    return s if s.startswith("http") else f"{SITE}/{s.lstrip('/')}"


DISCLAIMER_HTML = ('<hr><p class="disclaimer"><em>本文僅供醫療衛生教育參考，不能取代醫師的診斷與治療。每個人的病情、體質與治療反應不同，'
                   '文中提及的治療方式並非適用於所有人，亦不保證療效；侵入性治療可能伴隨副作用與風險。如有身體不適，請尋求合格醫療專業人員當面評估。</em></p>')


def with_disclaimer(p, body):
    if "不能取代醫師的診斷" in body or p["c"] == "關於醫師":
        return body
    return body + "\n" + DISCLAIMER_HTML


SHARE_JS = """<script>
document.querySelectorAll('.copy-link').forEach(function(btn){
  btn.addEventListener('click', function(){
    var url = btn.dataset.url, label = btn.textContent;
    function done(){ btn.textContent = '已複製 ✓'; setTimeout(function(){ btn.textContent = label; }, 1800); }
    function fallback(){
      var t = document.createElement('textarea'); t.value = url; t.setAttribute('readonly',''); t.style.position='fixed'; t.style.opacity='0';
      document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); done(); } catch(e) { window.prompt('請複製這個連結：', url); }
      document.body.removeChild(t);
    }
    if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(url).then(done, fallback); } else { fallback(); }
  });
});
</script>"""


def page(p, body):
    body = with_disclaimer(p, body)
    pid = p["id"]
    url = f"{SITE}/posts/{pid}.html"
    title = p["t"]
    desc = description(body)
    img = f"{SITE}/{p['og']}" if p.get("og") else first_image(body)
    from urllib.parse import quote
    line_url = "https://social-plugins.line.me/lineit/share?url=" + quote(url, safe="")
    share = lambda cls: (f'<div class="share-bar {cls}">'
                         f'<a class="share-btn line" href="{line_url}" target="_blank" rel="noopener">分享到 LINE</a>'
                         f'<button type="button" class="share-btn copy-link" data-url="{url}">複製連結</button></div>')
    local_body = re.sub(r'src="assets/', 'src="../assets/', body)
    local_body = re.sub(r"(<table.*?</table>)", r'<div class="table-wrap">\1</div>', local_body, flags=re.S)
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in p["tags"])
    source = ""
    ld = {
        "@context": "https://schema.org", "@type": "Article", "headline": title,
        "datePublished": p["d"], "image": img, "url": url, "inLanguage": "zh-Hant-TW",
        "author": {"@type": "Person", "name": "王威鵬醫師", "url": f"{SITE}/#about", "jobTitle": "中醫師"},
        "publisher": {"@type": "Person", "name": "王威鵬醫師", "url": f"{SITE}/"},
        "mainEntityOfPage": url, "keywords": ", ".join(p["tags"]),
    }
    e = html.escape
    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<title>{e(title)}｜王威鵬醫師 臨床筆記</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:locale" content="zh_TW">
<meta property="og:site_name" content="王威鵬醫師 臨床筆記">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="article:published_time" content="{p['d']}">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=cwTeX+Q+Kai&family=Noto+Sans+TC:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}{PAGE_CSS}</style>
</head>
<body>
<header class="site">
  <div class="wrap">
    <a class="brand" href="/" style="text-decoration:none"><span class="dot"></span><span class="kai">王威鵬醫師 臨床筆記</span></a>
    <nav class="menu">
      <ul>
        <li><a href="/">首頁</a></li>
        <li><a href="/#directory">專長分類</a></li>
        <li><a href="/#cases">個案分享</a></li>
        <li><a href="/#about">關於醫師</a></li>
        <li><a href="/contact.html">看診資訊</a></li>
      </ul>
    </nav>
    <a class="nav-info" href="/contact.html">看診資訊</a>
  </div>
</header>
<main class="post">
  <a class="back" href="/#directory">← 回到文章列表</a>
  <article class="post-card">
    <div class="post-head">
      <div class="modal-head-meta">
        <span class="badge {'core' if p['c'] in core_cats else ''}">{e(p['c'])}</span>
        <time class="date" datetime="{p['d']}">{p['d']}</time>
      </div>
      <h1>{e(title)}</h1>
      {share("")}
    </div>
    <div class="modal-body">
{local_body}
<div class="modal-tags">{tags}</div>
{source}
{AUTHOR_HTML if p["c"] != "關於醫師" else ""}
{related_html(p)}
{share("bottom")}
    </div>
  </article>
</main>
<footer class="site">
  <div class="wrap">
    <div class="kai" style="margin-bottom:6px">王威鵬醫師 臨床筆記</div>
    <a href="/">回首頁</a> · <a href="/contact.html">看診資訊</a>
  </div>
</footer>
{SHARE_JS}
</body>
</html>
"""


out = ROOT / "posts"
out.mkdir(exist_ok=True)
built = []
for p in posts:
    body = content.get(str(p["id"]))
    if body is None:
        continue
    (out / f"{p['id']}.html").write_text(page(p, body), encoding="utf-8")
    built.append(p)

# crawlable plain-link article index on the homepage (between markers)
links = "".join(f'<li><a href="posts/{p["id"]}.html">{html.escape(p["t"])}</a></li>' for p in sorted(built, key=lambda q: q["d"], reverse=True))
index_block = ('<!--ARTICLE-INDEX-START--><section class="wrap" id="all-posts"><details><summary>全部文章索引（' + str(len(built)) +
               ' 篇）</summary><ul class="all-posts-list">' + links + '</ul></details></section><!--ARTICLE-INDEX-END-->')
idx = (ROOT / "index.html").read_text(encoding="utf-8")
idx = re.sub(r"<!--ARTICLE-INDEX-START-->.*?<!--ARTICLE-INDEX-END-->", lambda m: index_block, idx, flags=re.S)
(ROOT / "index.html").write_text(idx, encoding="utf-8")

urls = [f"  <url><loc>{SITE}/</loc></url>", f"  <url><loc>{SITE}/contact.html</loc></url>"]
urls += [f"  <url><loc>{SITE}/posts/{p['id']}.html</loc><lastmod>{p['d']}</lastmod></url>" for p in built]
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
print(f"built {len(built)} article pages + sitemap.xml")
