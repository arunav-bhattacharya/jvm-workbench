// A thin Worker in front of the static site (web/).
//
// Cloudflare's static assets answer every request with the whole file, even when the browser
// asks for one part of it with a "Range: bytes=..." header. A video player needs those partial
// answers (206 Partial Content) to jump to a point it hasn't downloaded yet, so without them
// dragging the timeline does nothing. wrangler.jsonc runs this Worker first only for the media
// folders (/video/*, /vvoice/*); every other file is served by the assets directly.

const RANGE = /^bytes=(\d*)-(\d*)$/;

export default {
  async fetch(request, env, ctx) {
    const res = await env.ASSETS.fetch(request);
    const range = request.headers.get("Range");
    if (!range || res.status !== 200 || !res.body) return withAcceptRanges(res);

    // If-Range: only answer with a part if the file is still the one the browser has
    const ifRange = request.headers.get("If-Range");
    if (ifRange && ifRange !== res.headers.get("ETag") && ifRange !== res.headers.get("Last-Modified")) return withAcceptRanges(res);

    const m = RANGE.exec(range.trim());   // one range only; anything else gets the whole file
    if (!m || (m[1] === "" && m[2] === "")) return withAcceptRanges(res);

    let body = res.body;
    let size = Number(res.headers.get("Content-Length"));
    let buffered = null;
    if (!Number.isFinite(size) || size <= 0) { buffered = await res.arrayBuffer(); size = buffered.byteLength; body = null; }

    let start, end;
    if (m[1] === "") { start = Math.max(0, size - Number(m[2])); end = size - 1; }       // bytes=-500: the last 500
    else { start = Number(m[1]); end = m[2] === "" ? size - 1 : Math.min(Number(m[2]), size - 1); }
    if (start >= size || start > end) {
      if (body) body.cancel();
      return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}`, "Accept-Ranges": "bytes" } });
    }

    const length = end - start + 1;
    const headers = new Headers(res.headers);
    headers.set("Content-Range", `bytes ${start}-${end}/${size}`);
    headers.set("Content-Length", String(length));
    headers.set("Accept-Ranges", "bytes");
    if (buffered) return new Response(buffered.slice(start, end + 1), { status: 206, headers });

    const out = new FixedLengthStream(length);
    ctx.waitUntil(copyRange(body, out.writable, start, end + 1));
    return new Response(out.readable, { status: 206, headers });
  },
};

function withAcceptRanges(res) {
  if (res.status !== 200) return res;
  const headers = new Headers(res.headers);
  headers.set("Accept-Ranges", "bytes");
  return new Response(res.body, { status: res.status, statusText: res.statusText, headers });
}

// Copy bytes [from, to) of a stream into a writable stream, then stop reading.
async function copyRange(body, writable, from, to) {
  const reader = body.getReader();
  const writer = writable.getWriter();
  let pos = 0;
  try {
    while (pos < to) {
      const { done, value } = await reader.read();
      if (done) break;
      const s = pos;
      pos += value.byteLength;
      if (pos <= from) continue;
      const a = Math.max(from - s, 0), b = Math.min(to - s, value.byteLength);
      if (b > a) await writer.write(value.subarray(a, b));
    }
    await writer.close();
  } catch (e) {
    try { await writer.abort(e); } catch (_) { /* the browser went away */ }
  } finally {
    reader.cancel().catch(() => {});
  }
}
