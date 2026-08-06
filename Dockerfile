# 이후 소설가 홈페이지 — 정적 사이트 + 동적 문학노트/게시판 API
FROM python:3.12-alpine
WORKDIR /app
COPY index.html robots.txt sitemap.xml CNAME og-image.jpg ./
COPY google17ccaa674b8b790b.html naver7a6895689b825b13f6abd14a77c7c18a.html ./
COPY 404.html ./404.html
COPY literature ./literature
COPY author ./author
COPY content/literature-index-policy.json ./content/literature-index-policy.json
COPY server.py literature_index_policy.py ./
ENV PORT=80
ENV BOARD_POSTS_DIR=/data/board-posts
ENV LITERATURE_POSTS_DIR=/data/literature-posts
ENV LITERATURE_PUBLICATION_MODE=static
VOLUME ["/data"]
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1/', timeout=3).read(1)" || exit 1
CMD ["python", "server.py"]
