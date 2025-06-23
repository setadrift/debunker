FROM node:20

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

CMD ["npm", "run", "preview", "--", "--port", "5173"] 