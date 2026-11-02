FROM alpine:3.24 AS ffmpeg-build

RUN apk add --no-cache build-base nasm pkgconf curl xz x264-dev lame-dev dav1d-dev zlib-dev

# Minimal ffmpeg for yt-dlp: only what ytflex needs (see the feature lists below).
#   decoders: YouTube's video (h264, vp9, av1) + audio (aac, opus, vorbis) + thumbnails (webp, mjpeg, png)
#   encoders: libx264 + aac (mp4 conversion), libmp3lame (audio), mjpeg + png (thumbnail jpg/png)
#   muxers/demuxers: mp4/m4a, matroska/webm, mp3, image2 (thumbnails), ffmetadata (chapters/metadata input)
RUN curl -fsSL https://ffmpeg.org/releases/ffmpeg-8.1.3.tar.xz | tar xJ -C /tmp && \
    cd /tmp/ffmpeg-8.1.3 && \
    ./configure \
        --prefix=/opt/ffmpeg --enable-small --enable-gpl \
        --disable-everything --disable-autodetect --disable-doc --disable-debug \
        --disable-ffplay --disable-network \
        --enable-libx264 --enable-libmp3lame --enable-libdav1d --enable-zlib \
        --enable-decoder=h264,vp9,libdav1d,aac,opus,vorbis,mp3,webp,mjpeg,png \
        --enable-encoder=libx264,aac,libmp3lame,mjpeg,png \
        --enable-demuxer=mov,matroska,mp3,image2,image_webp_pipe,image_jpeg_pipe,image_png_pipe,ogg,ffmetadata \
        --enable-muxer=mp4,ipod,matroska,webm,mp3,image2,mjpeg \
        --enable-parser=h264,vp9,av1,aac,opus,vorbis,mpegaudio,mjpeg,webp,png \
        --enable-bsf=aac_adtstoasc,h264_mp4toannexb,extract_extradata \
        --enable-protocol=file,pipe \
        --enable-filter=scale,aresample,aformat,format,null,anull,setpts,asetpts,fps,trim,atrim && \
    make -j2 && make install

FROM python:3.12-alpine

WORKDIR /app

# ffmpeg is the minimal build above (shared libs from apk); deno from apk (musl-native).
RUN apk add --no-cache deno x264-libs lame-libs dav1d libstdc++
COPY --from=ffmpeg-build /opt/ffmpeg/bin/ffmpeg /opt/ffmpeg/bin/ffprobe /usr/local/bin/

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY --chown=1000:1000 . ./
RUN adduser -D -u 1000 appuser
USER appuser

CMD ["python", "./main.py"]
