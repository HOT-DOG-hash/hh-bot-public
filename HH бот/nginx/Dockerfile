FROM nginx:1.25-alpine

RUN apk add --no-cache apache2-utils bash

COPY nginx.conf.tpl /etc/nginx/templates/nginx.conf.tpl
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV NGINX_ENVSUBST_OUTPUT_DIR=/etc/nginx/conf.d

CMD ["/entrypoint.sh"]
