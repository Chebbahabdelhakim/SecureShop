FROM node:20-bookworm-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends python3 make g++ \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# VULNERABILITY: package.json pins lodash@4.17.19 (known CVEs); run npm audit and upgrade for production.
COPY package.json ./
RUN npm install --omit=dev

COPY . .

EXPOSE 8004

CMD ["node", "index.js"]
