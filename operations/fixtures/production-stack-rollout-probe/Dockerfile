FROM busybox:1.36.1

COPY entrypoint.sh /usr/local/bin/rollout-probe
COPY www /www

RUN sed -i 's/\r$//' /usr/local/bin/rollout-probe \
    && chmod 0555 /usr/local/bin/rollout-probe

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/rollout-probe"]
