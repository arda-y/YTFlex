# YTFlex

YouTube downloader API (FastAPI and yt-dlp) with a web page and a userscript. Send a video link, get back a download link. Files are deleted after 1 hour.

## Before you start

YouTube blocks many datacenter IPs. If yt-dlp fails with a sign-in or bot error on your server, run YTFlex on a machine with a home or business connection instead. You can keep the public nginx on another server and reach YTFlex over a VPN (see the second `/_ytflex_files/` block below).

## Setup

1. Edit `config.yaml`. Every setting is explained inside it.
2. Check the volume and port in `docker-compose.yml`. The host folder behind `/app/mountpoint/` must be writable by uid 1000 (the container does not run as root).
3. Build and run:

```bash
sudo docker compose up -d --build
```

The config is baked into the image. After a change to `config.yaml`, run the command again. The compose file also starts `bgutil-provider`, which makes the proof-of-origin tokens yt-dlp needs for YouTube.

4. Add the nginx blocks below to your TLS server block, and reload nginx.

## nginx

```nginx
location /ytflex/ {
    proxy_pass http://127.0.0.1:2002/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s; # a download holds the request open
    proxy_connect_timeout 300s;
    proxy_send_timeout 300s;
}

# Where the app tells nginx to read the files from. Not reachable from outside.
location /_ytflex_files/ {
    internal;
    alias /app/ytflex/downloads/; # the HOST folder behind mountpoint/downloads
}
```

If the files are on another machine than your public nginx, replace the second block with a proxy to a file server on that machine:

```nginx
location /_ytflex_files/ {
    internal;
    proxy_pass http://100.64.0.2:8090/; # a plain nginx there, with alias to the downloads folder
    proxy_hide_header Content-Disposition; # keep only the app's header, with the real filename
    proxy_buffering off;
}
```

`TRUSTED_PROXIES` in `config.yaml` must contain the IP that nginx appears as to the container (for Docker: the network gateway, see `docker network inspect <network>`). If it does not, every visitor looks like the proxy and the per-IP rate limit stops working.

## How it works

`/download/audio` and `/download/video` run yt-dlp, store the file in `mountpoint/downloads/<slug>/<filename>`, and return a JSON list of results, each with a `link`, a `message` and `metadata`. The link is `<IP_OR_DOMAIN>/<CDN_LOCATION>/<slug>`. The slug is 20 random characters and the filename is not in the URL.

`GET /<slug>` looks the slug up and answers with an `X-Accel-Redirect` header and the real filename in `Content-Disposition`. nginx then streams the file, so ranges and resume work. Unknown, expired and never-existing slugs return `gone.html` (HTTP 404).

A request that arrives when all download slots are busy gets 503. A request over the rate limit gets 429.

## Endpoints

| Route | What it does |
| --- | --- |
| `GET /` | The web page: download progress and a download history kept in the browser. |
| `GET /download/audio?link=<url>` | Download the audio as mp3 with tags and cover art. |
| `GET /download/video?link=<url>&res=<n>` | Download the video. `res` is the highest resolution to try. Add `mp4=true` to convert to mp4 (H.264 and AAC). |
| `GET /progress/<id>` | Progress of a running download: `{"stage": ..., "percent": 0-100}`. 404 if unknown or expired. |
| `GET /<slug>` | Download a finished file. |
| `GET /gone` | The "no longer here" page (HTTP 404). |
| `GET /faq` | The FAQ page. |
| `GET /ytflex.user.js` | The userscript. |

Both download routes accept `client=ext` (the userscript sets it and gets the lower size limit) and `progress_id=<id>` (8 to 32 letters and digits that you choose, to poll `/progress/<id>` while the request runs).

## Userscript

`userscript/ytflex-send.user.js` adds download buttons to YouTube. It talks to `https://arda0.net/ytflex` by default. To use your own instance, click the userscript manager's icon, choose **YTFlex: set server address** and enter your instance's address (leave it empty to go back to the default).
