// Hard access wall: every page requires the access key.
// Enter via https://chargebotic.com/?key=THEKEY (sets a 30-day cookie),
// or type the key on the lock screen. Change ACCESS_KEY below to rotate it.

const ACCESS_KEY = 'KESTREL26';
const COOKIE = 'cb_key';

const LOCK_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>Chargebotic</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0a0a0b; color: #f5f5f3; font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
         min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 30px; padding: 40px; }
  .logo { display: flex; align-items: center; gap: 14px; }
  .mark { width: 34px; height: 34px; border-radius: 7px; background: #e8490a; color: #fff; font-weight: 700;
          font-size: 1.15rem; display: flex; align-items: center; justify-content: center; }
  .name { font-weight: 700; letter-spacing: 0.16em; font-size: 1.05rem; text-transform: uppercase; }
  form { display: flex; gap: 10px; }
  input { background: #131316; border: 1px solid rgba(255,255,255,0.16); color: #f5f5f3; padding: 14px 18px;
          font-size: 0.95rem; width: 240px; outline: none; letter-spacing: 0.08em; }
  input:focus { border-color: #e8490a; }
  button { background: #f5f5f3; color: #0a0a0b; border: none; padding: 14px 24px; font-size: 0.92rem; font-weight: 600; cursor: pointer; }
  button:hover { opacity: 0.86; }
  .err { color: #e8490a; font-size: 0.85rem; min-height: 1.2em; }
  .contact { position: fixed; bottom: 36px; font-size: 0.82rem; color: #6a6a67; }
  .contact a { color: #6a6a67; text-decoration: none; }
  .contact a:hover { color: #f5f5f3; }
</style>
</head>
<body>
  <div class="logo"><div class="mark">C</div><span class="name">Chargebotic</span></div>
  <form onsubmit="event.preventDefault(); location.href='/?key=' + encodeURIComponent(document.getElementById('k').value.trim());">
    <input id="k" type="password" placeholder="Access key" autofocus autocomplete="off">
    <button type="submit">Enter</button>
  </form>
  <div class="err">__ERR__</div>
  <div class="contact"><a href="mailto:anis@chargebotic.com">anis@chargebotic.com</a></div>
</body>
</html>`;

export const config = {
    matcher: '/((?!og-image\\.png).*)',
};

export default function middleware(request) {
    const url = new URL(request.url);
    const provided = url.searchParams.get('key');
    const cookies = request.headers.get('cookie') || '';

    // Correct key in the URL: set the cookie and clean the address bar
    if (provided === ACCESS_KEY) {
        url.searchParams.delete('key');
        return new Response(null, {
            status: 302,
            headers: {
                'Location': url.pathname + url.search,
                'Set-Cookie': `${COOKIE}=${ACCESS_KEY}; Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax`,
            },
        });
    }

    // Valid cookie: let the request through
    if (cookies.split(/;\s*/).includes(`${COOKIE}=${ACCESS_KEY}`)) {
        return;
    }

    // Everything else hits the wall
    const err = provided ? 'Invalid key.' : '';
    return new Response(LOCK_HTML.replace('__ERR__', err), {
        status: 401,
        headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' },
    });
}
