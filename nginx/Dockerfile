FROM nginx:1.27-alpine

# Configuracion deliberadamente insegura del laboratorio:
# - server_tokens on (filtra version)
# - autoindex on en /files, /backup y /old
# - alias que expone directorios "internos"
RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

EXPOSE 80
