FROM rabbitmq:management-alpine

ARG RABBITMQ_MANAGEMENT_PORT
ARG RABBITMQ_PORT

COPY rabbitmq.conf /etc/rabbitmq/rabbitmq.conf

RUN echo "listeners.tcp.default = $RABBITMQ_PORT" >> /etc/rabbitmq/rabbitmq.conf
RUN echo "management.tcp.port = ${RABBITMQ_MANAGEMENT_PORT}" >> /etc/rabbitmq/rabbitmq.conf
