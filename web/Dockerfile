# Next.js standalone build — small runtime image, no dev deps shipped.
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

# Dev stage: source copied here on build, then kept live via docker watch sync.
FROM deps AS dev
COPY . .
ENV PORT=8000 HOSTNAME=0.0.0.0
CMD ["npm", "run", "dev"]

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=8000 HOSTNAME=0.0.0.0
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
EXPOSE 8000
CMD ["node", "server.js"]
