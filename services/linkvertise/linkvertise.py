"""
Linkvertise automation — complete the multi-step ad flow to reach the final link.

Pages:
  Page 1  — Landing page with "Get Link" button
  Page 2A — Optional fc-dialog overlay (short ad / rewarded ad)
  Page 2  — Either membership plan selection (S2) or ads carousel (S1)
  Page 3  — Final "Open" button → destination
"""

import asyncio
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from core.browser import DEVICE_PROFILE, MobileBrowser
from core.proxy import ProxyPool
from core.proxy_chain import DirectProxyChain

# ── Selectors ────────────────────────────────────────────────────────────────

# Global — CMP consent dialog (any page)
CMP_AGREE     = "#accept-btn"
CMP_USP_CLOSE = "button.qc-usp-close-icon"

# Page 1
GET_LINK = "button.lv-lib-button--full-width.lv-lib-button--primary"

# Page 1 — fc-dialog overlay (optional)
FC_OVERLAY  = ".fc-dialog-overlay"
FC_SHORT_AD = "button.fc-list-item-button.fc-rewarded-ad-button"
AD_BOX      = "#ad_position_box"

# Page 2 S2 — membership plan selection
MEMBERSHIP_WALL   = ".membership-plan-selection"
PLAN_OPTIONS      = "lv-membership-plan-option"
PLAN_WRAPPER      = ".membership-plan-option__wrapper"
PLAN_DURATION     = ".membership-plan-option__wrapper__duration"
CONTINUE_BTN      = "[dusk='action-wall-continue-action-btn']"

# Page 2 S1 — ads carousel
PROGRESS_FILL = ".progress-fill"
SKIP_AD       = "[dusk='lv-lib-carousel-skip-btn']"
COMPLETE_STEP = "[dusk='fullsize-result-ad-cta-btn']"
CAROUSEL_CTR  = ".carousel-items-counter.ng-star-inserted"

# Page 3
OPEN_BTN = "button.lv-lib-button--primary.lv-lib-button--lg.lv-lib-button--rounded"


# ── Helpers ──────────────────────────────────────────────────────────────────

async def handle_cmp(page, timeout=12000):
    """Dismiss CMP consent dialog if present."""
    try:
        btn = await page.wait_for_selector(CMP_AGREE, timeout=timeout)
        if btn:
            await btn.click()
            print("[cmp]    consent accepted")
            await asyncio.sleep(1)
    except Exception:
        pass


# ── Phase 1: Page 1 — Get Link ───────────────────────────────────────────────

async def phase1_get_link(page):
    """
    Dismiss any CMP dialogs, then click Get Link (if needed).
    Returns True if page is ready for Phase 2 (fc-dialog showing or Get Link clicked).
    """
    await asyncio.sleep(3)  # let page settle after redirect

    for attempt in range(3):
        try:
            await page.wait_for_function("""() => {
                return !!document.getElementById("accept-btn") ||
                       !!document.querySelector("button.qc-usp-close-icon") ||
                       !!document.querySelector("button.lv-lib-button--full-width.lv-lib-button--primary") ||
                       !!document.querySelector(".fc-dialog-overlay");
            }""", timeout=35000)
        except Exception:
            print(f"[p1]     timeout on attempt {attempt+1} — aborting")
            return False

        cmp = await page.query_selector(CMP_AGREE)
        if cmp:
            await cmp.click()
            print(f"[cmp]    consent accepted (attempt {attempt+1})")
            await asyncio.sleep(2)
            continue

        usp = await page.query_selector(CMP_USP_CLOSE)
        if usp:
            await page.evaluate(f"""() => {{
                const b = document.querySelector("{CMP_USP_CLOSE}");
                if (b) b.click();
            }}""")
            print(f"[cmp]    usp-opt-out dialog closed (attempt {attempt+1})")
            await asyncio.sleep(2)
            continue

        break

    # Check what state we're in now
    fc = await page.query_selector(FC_OVERLAY)
    if fc:
        print("[p1]     fc-dialog already showing (no Get Link click needed)")
        return True

    # Get Link still needs to be clicked
    try:
        btn = await page.wait_for_selector(GET_LINK, state="attached", timeout=10000)
    except Exception:
        print("[p1]     Get Link button not found — aborting")
        return False

    await asyncio.sleep(1)  # let CMP overlay finish fading
    # JS click bypasses Playwright visibility checks
    await page.evaluate(f"""() => {{
        const btn = document.querySelector("{GET_LINK}");
        if (btn) btn.click();
    }}""")
    print("[p1]     clicked Get Link")
    return True


# ── Phase 2A: fc-dialog overlay ──────────────────────────────────────────────

async def phase2a_fc_dialog(page, ctx):
    """
    If an fc-dialog overlay appears after Get Link, handle the short ad.
    Returns True if dialog was found and handled, False if no dialog.
    """
    try:
        await page.wait_for_selector(FC_OVERLAY, timeout=6000)
    except Exception:
        print("[p2a]    no fc-dialog overlay")
        return False

    print("[p2a]    fc-dialog detected")

    # Click the short ad / rewarded ad button
    try:
        await page.wait_for_selector(FC_SHORT_AD, timeout=5000)
        await page.click(FC_SHORT_AD)
        print("[p2a]    clicked short ad button")
    except Exception as e:
        print(f"[p2a]    could not click short ad: {e}")
        return False

    # Wait for fullscreen ad to finish OR for carousel/membership to appear
    print("[p2a]    waiting for fullscreen ad to complete or page to advance...")
    try:
        await page.wait_for_function(f"""() => {{
            // Ad is done when the hash clears or S1/S2 content appears
            const noFullscreen = !window.location.hash.includes('goog_fullscreen_ad');
            const hasCarousel  = !!document.querySelector("{PROGRESS_FILL}");
            const hasMembership = !!document.querySelector("{MEMBERSHIP_WALL}");
            const hasOpen = !!document.querySelector("{OPEN_BTN}");
            return noFullscreen || hasCarousel || hasMembership || hasOpen;
        }}""", timeout=60000)
        print("[p2a]    fullscreen ad done / page advanced")
    except Exception:
        print("[p2a]    timed out waiting for fullscreen ad to complete")

    # ad_position_box fallback
    try:
        ad_box = await page.query_selector(AD_BOX)
        if ad_box:
            print("[p2a]    ad_position_box visible — trying to close")
            for close_sel in [
                f"{AD_BOX} [class*='close']",
                f"{AD_BOX} button",
                f"{AD_BOX} [aria-label*='close']",
                f"{AD_BOX} [aria-label*='Close']",
            ]:
                try:
                    close_btn = await page.query_selector(close_sel)
                    if close_btn:
                        await close_btn.click()
                        print(f"[p2a]    closed ad box via {close_sel}")
                        break
                except Exception:
                    continue
    except Exception:
        pass

    return True


# ── Phase 2: detect which flow (S1 carousel or S2 membership) ────────────────

async def phase2_detect(page):
    """
    Wait for either the membership wall (S2) or the ads carousel (S1).
    Returns 's1', 's2', or None on timeout.
    """
    try:
        await page.wait_for_function(f"""() => {{
            return !!document.querySelector("{MEMBERSHIP_WALL}") ||
                   !!document.querySelector("{PROGRESS_FILL}") ||
                   !!document.querySelector("{OPEN_BTN}");
        }}""", timeout=40000)
    except Exception:
        print(f"[p2]     timed out waiting for S1/S2 page — url: {page.url[:80]}")
        return None

    if await page.query_selector(OPEN_BTN):
        print("[p2]     Open button already visible — skipping carousel")
        return "open"

    if await page.query_selector(MEMBERSHIP_WALL):
        print("[p2]     S2 — membership plan selection")
        return "s2"
    print("[p2]     S1 — ads carousel")
    return "s1"


# ── Phase 3B: S2 membership plan wall ────────────────────────────────────────

async def phase3b_membership(page):
    """Click 'Watch Ads' option and Continue. If absent, abort the instance."""
    try:
        await page.wait_for_selector(PLAN_WRAPPER, timeout=10000)
    except Exception:
        print("[p3b]    plan wrappers not found")
        return False

    # Find the plan whose text contains "watch ads" (case-insensitive)
    plans = await page.query_selector_all(PLAN_WRAPPER)
    watch_ads_idx = None
    for i, plan in enumerate(plans):
        text = (await plan.inner_text()).strip().lower()
        if "watch ads" in text or "watch ad" in text:
            watch_ads_idx = i
            break

    if watch_ads_idx is None:
        print("[p3b]    'Watch Ads' option not found — aborting instance")
        return False

    print(f"[p3b]    clicking 'Watch Ads' (plan #{watch_ads_idx})")
    await page.evaluate(f"""() => {{
        const plans = document.querySelectorAll("{PLAN_WRAPPER}");
        if (plans[{watch_ads_idx}]) plans[{watch_ads_idx}].click();
    }}""")
    await asyncio.sleep(1)

    try:
        btn = await page.wait_for_selector(CONTINUE_BTN, state="attached", timeout=8000)
        await btn.click()
        print("[p3b]    clicked Continue")
        return True
    except Exception as e:
        print(f"[p3b]    Continue button not found: {e}")
        return False


# ── Phase 3A: S1 ads carousel ─────────────────────────────────────────────────

async def phase3a_carousel(page):
    """
    Iterate through carousel ads.
    For each step: wait for Skip (500ms debounce), click Skip.
    If Skip not available, click Complete Step.
    Stop when counter shows we're on the last ad and it completes.
    """
    await asyncio.sleep(3)  # let page settle after fc-dialog / membership flow

    step = 0
    max_steps = 10

    while step < max_steps:
        step += 1
        print(f"[p3a]    carousel step {step}")

        # Wait for either Skip or Complete Step to appear
        try:
            await page.wait_for_function(f"""() => {{
                return !!document.querySelector("{SKIP_AD}") ||
                       !!document.querySelector("{COMPLETE_STEP}");
            }}""", timeout=30000)
        except Exception:
            # Debug: print what's visible
            url_now = page.url
            print(f"[p3a]    step {step}: timed out — current url: {url_now[:80]}")
            # Check if Open button is already there
            open_btn = await page.query_selector(OPEN_BTN)
            if open_btn:
                print("[p3a]    Open button visible — carousel may be done")
                return True
            break

        await asyncio.sleep(1)

        # Read counter to check if this is the last step
        ctr_el = await page.query_selector(CAROUSEL_CTR)
        ctr_text = ""
        if ctr_el:
            ctr_text = (await ctr_el.inner_text()).strip()
            print(f"[p3a]    counter: {ctr_text!r}")

        # Wait for the progress bar to fully fill (timer-gated skip)
        print(f"[p3a]    waiting for progress to complete...")
        try:
            await page.wait_for_function("""() => {
                const bar = document.querySelector('.progress-fill');
                if (!bar) return true;  // no bar = not timer-gated
                const w = parseFloat(bar.style.width || '0');
                return w >= 99;
            }""", timeout=30000)
            print(f"[p3a]    progress complete")
        except Exception:
            print(f"[p3a]    progress wait timed out — trying skip anyway")

        await asyncio.sleep(0.5)

        # Try Playwright native click on Skip first (most reliable for Angular)
        clicked = False
        try:
            skip_el = await page.query_selector(SKIP_AD)
            if skip_el:
                await skip_el.click()
                print(f"[p3a]    step {step}: skipped")
                clicked = True
        except Exception:
            pass

        if not clicked:
            try:
                cta_el = await page.query_selector(f"{COMPLETE_STEP} button")
                if not cta_el:
                    cta_el = await page.query_selector(COMPLETE_STEP)
                if cta_el:
                    await cta_el.click()
                    print(f"[p3a]    step {step}: completed (CTA)")
                    clicked = True
            except Exception:
                pass

        if not clicked:
            print(f"[p3a]    step {step}: no action button found — stopping")
            break

        await asyncio.sleep(2)  # let carousel advance

        # Check if we've reached the Open button (carousel done)
        open_btn = await page.query_selector(OPEN_BTN)
        if open_btn:
            print("[p3a]    carousel complete — Open button visible")
            return True

        # If counter shows last item completed, we're done
        if ctr_text:
            parts = ctr_text.replace("/", " ").split()
            if len(parts) == 2:
                try:
                    if int(parts[0]) >= int(parts[1]):
                        print("[p3a]    counter reached end")
                        return True
                except ValueError:
                    pass

    print(f"[p3a]    carousel loop ended after {step} step(s)")
    return True


# ── Phase 4: Open button ──────────────────────────────────────────────────────

async def phase4_open(page):
    """Click the final Open button and confirm success."""
    for attempt in range(5):
        try:
            btn = await page.wait_for_selector(OPEN_BTN, state="attached", timeout=20000)
        except Exception:
            print(f"[p4]     Open button not found (attempt {attempt+1})")
            return False

        await asyncio.sleep(random.uniform(3, 5))
        await page.evaluate(f"""() => {{
            const b = document.querySelector("{OPEN_BTN}");
            if (b) b.click();
        }}""")
        print(f"[p4]     clicked Open (attempt {attempt+1})")

        # Check for success title
        try:
            await page.wait_for_selector("[dusk='success-title']", timeout=60000)
            print("[p4]     success!")
            return True
        except Exception:
            pass

        # Or check page navigated away from linkvertise
        try:
            await page.wait_for_function(
                "() => !window.location.hostname.includes('linkvertise.com')",
                timeout=8000
            )
            print("[p4]     redirected to destination")
            return True
        except Exception:
            pass

    return False


# ── Main runner ───────────────────────────────────────────────────────────────

async def _run(url, chosen, proxy, headless):
    result = {"device": chosen, "ip": None, "success": False, "skipped": False}

    async with MobileBrowser(chosen, headless=headless, proxy=proxy) as mb:
        ctx  = mb.context
        page = mb.page

        # Close any unexpected new tabs instantly
        ctx.on("page", lambda p: asyncio.ensure_future(p.close()))

        print(f"[open]   {url}")
        print(f"[device] {chosen}")

        try:
            await page.goto(url, wait_until="commit", timeout=60000)
        except Exception as e:
            print(f"[nav]    failed: {str(e)[:80]}")
            return result

        # Wait for redirect to linkvertise.com to finish loading
        try:
            await page.wait_for_url("*linkvertise.com*", timeout=15000)
        except Exception:
            pass  # already on linkvertise.com or no redirect
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=15000)
        except Exception:
            pass

        print(f"[nav]    {page.url[:70]}")

        # ── Phase 1 ──
        if not await phase1_get_link(page):
            return result

        # ── Phase 2A ──
        await phase2a_fc_dialog(page, ctx)
        await asyncio.sleep(3)  # let page transition after fc-dialog

        # ── Phase 2: detect flow ──
        flow = await phase2_detect(page)
        if flow is None:
            return result

        # ── Phase 3A / 3B ──
        if flow == "open":
            pass  # skip straight to phase 4
        elif flow == "s2":
            if not await phase3b_membership(page):
                return result
            # After membership selection, carousel may follow
            flow2 = await phase2_detect(page)
            if flow2 == "s1":
                await phase3a_carousel(page)
        else:
            await phase3a_carousel(page)

        # ── Phase 4 ──
        result["success"] = await phase4_open(page)

        try:
            result["ip"] = await mb.exit_ip()
        except Exception:
            pass

    return result


async def run(url, device=None, headless=False, proxy_pool=None):
    chosen = device or random.choice(list(DEVICE_PROFILE.keys()))
    proxy  = proxy_pool.pick() if proxy_pool else None

    if proxy and "iPhone" in chosen:
        async with DirectProxyChain(proxy) as chain:
            return await _run(url, chosen, chain.local_url, headless)
    else:
        return await _run(url, chosen, proxy, headless)
