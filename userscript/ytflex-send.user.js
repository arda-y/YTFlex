// ==UserScript==
// @name         Send to YTFlex
// @namespace    https://arda0.net/ytflex/
// @version      1.6
// @description  Video/Audio toggle, quality and Download buttons next to the title of a YouTube watch page, and a Download button (video, best quality) in the Shorts action bar. Sends the video to YTFlex and starts the download.
// @updateURL    https://arda0.net/ytflex.user.js
// @downloadURL  https://arda0.net/ytflex.user.js
// @match        https://www.youtube.com/*
// @match        https://m.youtube.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_openInTab
// @grant        GM_getValue
// @grant        GM_setValue
// @connect      arda0.net
// @run-at       document-idle
// ==/UserScript==

(function () {
    "use strict";

    const API = "https://arda0.net/ytflex";
    const RES = ["1080", "720", "480"]; // 1080p is the maximum
    const BOX_ID = "ytflexBox";
    const SHORTS_ID = "ytflexShortsBtn";
    const SHORTS_OPTS = { type: "video", res: RES[0] }; // Shorts: always video, best quality

    let busy = false; // true while a download request is running
    const refreshers = new Set(); // one per button group on the page; return false once detached

    function refreshAll() {
        for (const f of [...refreshers]) if (f() === false) refreshers.delete(f);
    }

    // The mode and quality are shared by every button group.
    const getType = () => (GM_getValue("type", "video") === "audio" ? "audio" : "video");
    const getRes = () => {
        const r = GM_getValue("res", "1080");
        return RES.includes(r) ? r : "1080";
    };

    // Watch ID only: drops playlist and timestamp parameters. Shorts work as normal videos.
    function videoLink() {
        const u = new URL(location.href);
        const v = u.searchParams.get("v");
        if (u.pathname === "/watch" && v) return `https://www.youtube.com/watch?v=${v}`;
        const m = u.pathname.match(/^\/shorts\/([\w-]{11})/);
        return m ? `https://www.youtube.com/watch?v=${m[1]}` : null;
    }

    // say(message, ms, state): state is "working", "ok" or "error"; ms = 0 keeps the message.
    // opts.type and opts.res replace the saved mode and quality.
    function download(say, opts = {}) {
        const link = videoLink();
        if (!link) return say("Open a video first.", 6000, "error");
        if (busy) return;
        busy = true;
        refreshAll();

        const type = opts.type || getType();
        const params = new URLSearchParams({ link, client: "ext" });
        if (type === "video") {
            params.set("res", opts.res || getRes());
            params.set("mp4", "false");
        }
        say("Working... (large files take a while)", 0, "working");

        const finish = () => {
            busy = false;
            refreshAll();
        };
        GM_xmlhttpRequest({
            method: "GET",
            url: `${API}/download/${type}?${params}`,
            timeout: 300000, // the server downloads first; nginx waits up to 300 s
            onload(r) {
                finish();
                try {
                    const data = JSON.parse(r.responseText);
                    // Error replies are {"message": ...} (busy, too big, bad link, ...)
                    if (!Array.isArray(data) && data.message) return say(data.message, 10000, "error");
                    const info = data[0][0];
                    if (!info || !info.link) throw new Error("no link in reply");
                    say(`Ready: ${info.metadata.title}`, 6000, "ok");
                    GM_openInTab(info.link, { active: false, insert: true });
                } catch (e) {
                    // A Cloudflare challenge or a server error returns HTML or an error body.
                    say(`Failed (HTTP ${r.status}). Open arda0.net/ytflex once in this browser, then retry.`, 10000, "error");
                    console.error("[YTFlex]", e, r.responseText.slice(0, 300));
                }
            },
            onerror() { finish(); say("YTFlex unreachable.", 6000, "error"); },
            ontimeout() { finish(); say("YTFlex timed out.", 6000, "error"); },
        });
    }

    // ---------------------------------------------------------------- watch page

    function makeButton(label, title) {
        const b = document.createElement("button");
        b.textContent = label;
        b.title = title;
        Object.assign(b.style, {
            padding: "0 12px", height: "28px", border: "0", borderRadius: "14px",
            background: "var(--yt-spec-badge-chip-background, rgba(255,255,255,.1))",
            color: "var(--yt-spec-text-primary, #fff)",
            font: "500 13px Roboto, Arial, sans-serif", cursor: "pointer", whiteSpace: "nowrap",
        });
        return b;
    }

    function buildBox() {
        const box = document.createElement("div");
        box.id = BOX_ID;
        Object.assign(box.style, {
            display: "flex", alignItems: "center", gap: "6px",
            marginLeft: "12px", flexShrink: "0", height: "28px",
        });

        const tag = document.createElement("span");
        tag.textContent = "YTFlex:";
        Object.assign(tag.style, {
            font: "500 13px Roboto, Arial, sans-serif",
            color: "var(--yt-spec-text-secondary, #aaa)",
        });

        const toggle = makeButton("", "Switch between video and audio");
        const resBtn = makeButton("", "Video quality (click to change)");
        const dl = makeButton("Download", "Send this video to YTFlex");
        dl.style.background = "#2563eb";
        dl.style.color = "#fff";

        const status = document.createElement("span");
        Object.assign(status.style, {
            font: "12px Roboto, Arial, sans-serif",
            color: "var(--yt-spec-text-secondary, #aaa)",
            maxWidth: "220px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
        });

        function refresh() {
            if (!box.isConnected) return false;
            const type = getType();
            toggle.textContent = type === "video" ? "Video" : "Audio";
            resBtn.textContent = `${getRes()}p`;
            toggle.disabled = busy;
            resBtn.disabled = busy || type === "audio";
            dl.disabled = busy;
            for (const b of [toggle, resBtn, dl]) {
                b.style.opacity = b.disabled ? "0.4" : "1";
                b.style.cursor = b.disabled ? "default" : "pointer";
            }
        }

        let timer;
        const say = (msg, ms = 6000) => {
            status.textContent = msg;
            status.title = msg;
            clearTimeout(timer);
            if (ms) timer = setTimeout(() => (status.textContent = ""), ms);
        };

        toggle.addEventListener("click", () => {
            GM_setValue("type", getType() === "video" ? "audio" : "video");
            refreshAll();
        });
        resBtn.addEventListener("click", () => {
            GM_setValue("res", RES[(RES.indexOf(getRes()) + 1) % RES.length]);
            refreshAll();
        });
        dl.addEventListener("click", () => download(say));

        box.append(tag, toggle, resBtn, dl, status);
        refreshers.add(refresh);
        refresh();
        return box;
    }

    // ------------------------------------------------------------------- shorts

    function el(tag, className, attrs = {}) {
        const n = document.createElement(tag);
        if (className) n.className = className;
        for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
        return n;
    }

    // Built element by element, not with innerHTML: YouTube blocks plain-string HTML (Trusted Types).
    // It uses the same markup and classes as the other buttons in the action bar, so YouTube styles it.
    function buildShortsButton() {
        const host = el("button-view-model", "ytSpecButtonViewModelHost ytwReelActionBarViewModelHostDesktopActionButton");
        host.id = SHORTS_ID;
        const wrap = el("label", "ytSpecButtonShapeWithLabelHost");
        const btn = el(
            "button",
            "ytSpecButtonShapeNextHost ytSpecButtonShapeNextTonal ytSpecButtonShapeNextMono " +
                "ytSpecButtonShapeNextSizeL ytSpecButtonShapeNextIconButton " +
                "ytSpecButtonShapeNextMainstageIconSize ytSpecButtonShapeNextMainstagePadding",
            { "aria-label": "Download with YTFlex", "aria-disabled": "false" }
        );
        const iconBox = el("div", "ytSpecButtonShapeNextIcon ytSpecButtonShapeNextElevatedContent", { "aria-hidden": "true" });
        const NS = "http://www.w3.org/2000/svg";
        const svg = document.createElementNS(NS, "svg");
        for (const [k, v] of Object.entries({ height: "24", width: "24", viewBox: "0 0 24 24", focusable: "false" }))
            svg.setAttribute(k, v);
        svg.style.cssText = "pointer-events:none;display:block;fill:currentColor";
        const path = document.createElementNS(NS, "path");
        path.setAttribute("d", "M17 18v1H6v-1h11Zm-.5-6.6-.7-.7-3.8 3.7V4h-1v10.4l-3.8-3.8-.7.7 5 5 5-5Z");
        svg.appendChild(path);
        iconBox.appendChild(svg);
        btn.appendChild(iconBox);

        const labelBox = el("div", "ytSpecButtonShapeWithLabelLabel");
        const label = el(
            "span",
            "ytAttributedStringHost ytAttributedStringWhiteSpacePreWrap ytAttributedStringTextAlignmentCenter ytAttributedStringWordWrapping",
            { role: "text" }
        );
        labelBox.appendChild(label);
        wrap.append(btn, labelBox);
        host.appendChild(wrap);

        // The label shows the quality, "..." while a download runs, then Done or Failed.
        let hold = null;
        function refresh() {
            if (!host.isConnected) return false;
            btn.disabled = busy;
            btn.style.opacity = busy ? "0.4" : "1";
            if (!hold) {
                label.textContent = busy ? "..." : `${SHORTS_OPTS.res}p`;
                btn.title = `Download with YTFlex (video, ${SHORTS_OPTS.res}p)`;
            }
        }
        let timer;
        const say = (msg, ms, state) => {
            btn.title = msg;
            clearTimeout(timer);
            if (state === "working") return;
            hold = state === "ok" ? "Done" : "Failed";
            label.textContent = hold;
            timer = setTimeout(() => {
                hold = null;
                refresh();
            }, ms || 6000);
        };
        btn.addEventListener("click", () => {
            hold = null;
            download(say, SHORTS_OPTS);
        });

        refreshers.add(refresh);
        refresh();
        return host;
    }

    // ------------------------------------------------------------------- wiring

    // YouTube is a single-page app and re-renders these parts, so check on every change.
    function ensure() {
        const title = document.querySelector("#title-row #title");
        if (title && !title.querySelector(`#${BOX_ID}`)) {
            document.querySelectorAll(`#${BOX_ID}`).forEach((n) => n.remove());
            title.appendChild(buildBox());
        }
        if (location.pathname.startsWith("/shorts/")) {
            // Shorts keeps several players in the page, each with its own action bar.
            for (const bar of document.querySelectorAll("reel-action-bar-view-model")) {
                if (bar.querySelector(`#${SHORTS_ID}`)) continue;
                bar.insertBefore(buildShortsButton(), bar.querySelector("pivot-button-view-model"));
            }
        }
    }
    window.addEventListener("yt-navigate-finish", ensure);
    new MutationObserver(ensure).observe(document.body, { childList: true, subtree: true });
    ensure();
})();
