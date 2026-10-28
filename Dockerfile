FROM python:3-alpine

WORKDIR /app
COPY start-system.sh /app/start-system.sh
COPY data/ /app/data/
COPY api/ /app/api/

RUN chmod +x /app/start-system.sh

EXPOSE 3000
CMD ["/app/start-system.sh"]
