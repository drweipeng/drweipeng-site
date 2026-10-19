# 網站維護

文章資料都在 index.html 的 POSTS 與 CONTENT。新增或修改文章後執行：

    python3 tools/build_posts.py

會重新產生 posts/<id>.html（每篇文章的獨立頁面，含 FB 分享預覽用的 og 標籤）與 sitemap.xml。
單篇網址：https://drweipeng.com/posts/<id>.html
