FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
ENV HOST=0.0.0.0 PORT=1234
EXPOSE 1234
CMD ["npm", "start"]
