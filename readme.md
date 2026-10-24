# YTFlex

YouTube downloader API written in Python, with a CDN and reverse proxy setup.

## Setup

1. Clone the repo, edit `config.yaml` (see below) and `docker-compose.yml` volumes/port.
2. Build and run:

```bash
sudo docker build -t ytflex .
sudo docker-compose up -d
```

Stop with `sudo docker-compose down`.

## Config (`config.yaml`)

| Setting | Description | Default |
| --- | --- | --- |
| `ROOT_PATH` | Reverse proxied path to the API | `/ytflex` |
| `CDN_LOCATION` | Reverse proxied path to the CDN | `ytflex` |
| `PORT` | API server port | `2002` |
| `MAX_RES` | Max download resolution | `2160` |
| `MAX_FILE_SIZE` | Max file size in MB | `2000` |
| `EXT_MAX_FILE_SIZE` | Max file size in MB for requests with `client=ext` (the userscript) | `200` |
| `MAX_CONCURRENT_DOWNLOADS` | Downloads that may run at once; extra requests get HTTP 503 | `3` |
| `IP_OR_DOMAIN` | Address used to build CDN links | `https://cdn.arda0.net` |
| `MAX_FILE_AGE` | File TTL in seconds before purge | `3600` |
| `SHOW_YT_DLP_OUTPUT` | Show yt-dlp output | `true` |
| `ALLOWED_DOMAINS` | CORS allowed origins | `[https://ytflex.vercel.app, https://arda0.net]` |
| `DOWNLOAD_RATE_LIMIT` | SlowAPI limits for `/download/*` | `1/10 seconds;5/minute` |
| `TRUSTED_PROXIES` | Peers trusted to set forwarded-IP headers | `[127.0.0.1, 172.17.0.1, ..., 172.20.0.1]` |
| `BGUTIL_PROVIDER_URL` | bgutil provider URL for yt-dlp | `http://bgutil-provider:4416` |
