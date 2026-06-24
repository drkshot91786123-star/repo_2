"""
Run one locker instance (no proxy) and measure total bytes transferred.
Usage: python3 measure_bw.py <locker_url>
"""
import asyncio
import sys
from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else None
if not URL:
    print("Usage: python3 measure_bw.py <locker_url>")
    sys.exit(1)

bytes_sent = 0
bytes_recv = 0
req_count = 0

async def main():
    global bytes_sent, bytes_recv, req_count

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            proxy={
                "server": "http://core-residential.evomi.com:1000",
                "username": "wakiurrahm2",
                "password": "WG7oFPWXhvXVRUcPGA5x",
            },
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
            viewport={"width": 390, "height": 844},
        )

        def on_request(req):
            global bytes_sent, req_count
            req_count += 1
            # estimate: headers + post body
            headers_size = sum(len(k) + len(v) + 4 for k, v in req.headers.items())
            body_size = len(req.post_data_buffer or b"")
            bytes_sent += headers_size + body_size

        async def on_response(resp):
            global bytes_recv
            try:
                body = await resp.body()
                headers_size = sum(len(k) + len(v) + 4 for k, v in resp.headers.items())
                bytes_recv += headers_size + len(body)
            except Exception:
                pass

        BLOCK_TYPES = {"image", "media", "font", "stylesheet"}

        async def block_heavy(route):
            if route.request.resource_type in BLOCK_TYPES:
                await route.abort()
            else:
                await route.continue_()

        page = await context.new_page()
        page.on("request", on_request)
        page.on("response", lambda r: asyncio.ensure_future(on_response(r)))

        print(f"[open] {URL}")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # Wait for tasks to appear
        try:
            await page.wait_for_selector("[data-d30task], [data-task]", timeout=30000)
            task_rows = await page.query_selector_all("[data-d30task], [data-task]")
            print(f"[tasks] found {len(task_rows)}")

            for i, row in enumerate(task_rows):
                try:
                    async with context.expect_page(timeout=10000) as new_page_info:
                        await row.click()
                    new_tab = await new_page_info.value
                    # Close task tabs instantly — don't load them at all
                    await new_tab.close()
                except Exception as e:
                    print(f"  tab {i+1} error: {e}")
                await asyncio.sleep(1.5)

            # Wait for done state
            for _ in range(20):
                done, total = await page.evaluate("""() => {
                    const rows = [...document.querySelectorAll('[data-d30task], [data-task]')];
                    return [rows.filter(r => r.classList.contains('done')).length, rows.length];
                }""")
                print(f"  {done}/{total} done")
                if total > 0 and done >= total:
                    break
                await asyncio.sleep(3)

            # Click unlock — block heavy assets on bunkr redirect page
            try:
                await page.route("**/*", block_heavy)
                btn = await page.wait_for_selector("#d30unlockBtn, .d31-unlock-btn", timeout=10000)
                await btn.click()
                await page.wait_for_load_state("domcontentloaded", timeout=15000)
                print(f"[redirect] {page.url}")
            except Exception as e:
                print(f"[unlock] {e}")

        except Exception as e:
            print(f"[error] {e}")

        await browser.close()

        total_mb = (bytes_sent + bytes_recv) / 1024 / 1024
        print(f"\n{'='*40}")
        print(f"Requests:  {req_count}")
        print(f"Sent:      {bytes_sent/1024:.1f} KB")
        print(f"Received:  {bytes_recv/1024:.1f} KB")
        print(f"TOTAL:     {total_mb:.2f} MB")
        print(f"{'='*40}")
        print(f"\nAt 1500 runs/day: {total_mb * 1500:.0f} MB/day  |  {total_mb * 1500 * 30 / 1024:.1f} GB/month")

asyncio.run(main())
