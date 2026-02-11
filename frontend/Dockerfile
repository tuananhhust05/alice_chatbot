FROM node:20-alpine

WORKDIR /app

# Set npm config for better network handling
RUN npm config set fetch-retries 5 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000

COPY package.json package-lock.json* ./
RUN npm install || npm install || npm install

COPY . .
RUN npm run build

EXPOSE 4173

CMD ["npm","run","preview"]
