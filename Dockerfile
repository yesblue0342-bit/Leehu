# 이후 소설가 홈페이지 — 정적 사이트 + SQLite 게시판 API
FROM python:3.12-alpine
WORKDIR /app
COPY index.html robots.txt sitemap.xml CNAME og-image.jpg ./
COPY google17ccaa674b8b790b.html naver7a6895689b825b13f6abd14a77c7c18a.html ./
COPY server.py ./
ENV PORT=80
ENV BOARD_POSTS_DIR=/data/board-posts
VOLUME ["/data"]
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1/', timeout=3).read(1)" || exit 1
CMD ["python", "server.py"]
