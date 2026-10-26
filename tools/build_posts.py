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
"""


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


def page(p, body):
    body = with_disclaimer(p, body)
    pid = p["id"]
    url = f"{SITE}/posts/{pid}.html"
    title = p["t"]
    desc = description(body)
    img = first_image(body)
    local_body = re.sub(r'src="assets/', 'src="../assets/', body)
    local_body = re.sub(r"(<table.*?</table>)", r'<div class="table-wrap">\1</div>', local_body, flags=re.S)
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in p["tags"])
    source = (f'<a class="modal-source" href="{html.escape(p["u"])}" target="_blank" rel="noopener">在原始部落格開啟原文 →</a>'
              if p.get("u") else "")
    ld = {
        "@context": "https://schema.org", "@type": "Article", "headline": title,
        "datePublished": p["d"], "image": img, "url": url, "inLanguage": "zh-Hant-TW",
        "author": {"@type": "Person", "name": "王威鵬醫師"}, "keywords": ", ".join(p["tags"]),
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
    </div>
    <div class="modal-body">
{local_body}
<div class="modal-tags">{tags}</div>
{source}
    </div>
  </article>
</main>
<footer class="site">
  <div class="wrap">
    <div class="kai" style="margin-bottom:6px">王威鵬醫師 臨床筆記</div>
    <a href="/">回首頁</a> · <a href="/contact.html">看診資訊</a>
  </div>
</footer>
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

urls = [f"  <url><loc>{SITE}/</loc></url>", f"  <url><loc>{SITE}/contact.html</loc></url>"]
urls += [f"  <url><loc>{SITE}/posts/{p['id']}.html</loc><lastmod>{p['d']}</lastmod></url>" for p in built]
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
print(f"built {len(built)} article pages + sitemap.xml")
