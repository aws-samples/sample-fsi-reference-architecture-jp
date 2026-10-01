FROM quay.io/keycloak/keycloak:26.7.1
# --chown=1000:0 matches the UID/GID the base image runs as (see USER 1000 and the
# "keycloak:x:1000:0:..." /etc/passwd entry in the upstream Dockerfile); without it these
# files are owned by root and Keycloak fails to read them with AccessDeniedException.
COPY --chown=1000:0 ./authserver.key /opt/keycloak/conf/tls.key
COPY --chown=1000:0 ./authserver.crt ./inca.crt ./ca.crt /opt/keycloak/conf/
RUN cat /opt/keycloak/conf/authserver.crt /opt/keycloak/conf/inca.crt /opt/keycloak/conf/ca.crt > /opt/keycloak/conf/tls.crt
