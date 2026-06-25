# 이후 소설가 홈페이지 — OCI 정적 서빙 (nginx)
FROM nginx:alpine
# 정적 파일 복사
COPY index.html /usr/share/nginx/html/index.html
COPY robots.txt /usr/share/nginx/html/robots.txt
COPY sitemap.xml /usr/share/nginx/html/sitemap.xml
COPY CNAME /usr/share/nginx/html/CNAME
COPY google17ccaa674b8b790b.html /usr/share/nginx/html/
COPY naver7a6895689b825b13f6abd14a77c7c18a.html /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://127.0.0.1/ >/dev/null 2>&1 || exit 1
