import sys, time, os, datetime
from playwright.sync_api import sync_playwright

class CaptchaRestartException(Exception): pass

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
        LIGHTRED_EX = LIGHTGREEN_EX = LIGHTYELLOW_EX = LIGHTBLUE_EX = ""
        LIGHTMAGENTA_EX = LIGHTCYAN_EX = RESET = ""
    class Style:
        RESET_ALL = BRIGHT = DIM = ""

os.system("mode con: cols=170 lines=40")
os.system("title TERM FIRE ^| PAKORNSIR.P1")

BANNER = r"""                       
 ________  ________  _______   __       __        ________  ______  _______   ________ 
/        |/        |/       \ /  \     /  |      /        |/      |/       \ /        |
$$$$$$$$/ $$$$$$$$/ $$$$$$$  |$$  \   /$$ |      $$$$$$$$/ $$$$$$/ $$$$$$$  |$$$$$$$$/ 
   $$ |   $$ |__    $$ |__$$ |$$$  \ /$$$ |      $$ |__      $$ |  $$ |__$$ |$$ |__    
   $$ |   $$    |   $$    $$< $$$$  /$$$$ |      $$    |     $$ |  $$    $$< $$    |   
   $$ |   $$$$$/    $$$$$$$  |$$ $$ $$/$$ |      $$$$$/      $$ |  $$$$$$$  |$$$$$/    
   $$ |   $$ |_____ $$ |  $$ |$$ |$$$/ $$ |      $$ |       _$$ |_ $$ |  $$ |$$ |_____ 
   $$ |   $$       |$$ |  $$ |$$ | $/  $$ |      $$ |      / $$   |$$ |  $$ |$$       |
   $$/    $$$$$$$$/ $$/   $$/ $$/      $$/       $$/       $$$$$$/ $$/   $$/ $$$$$$$$/ 
"""

COLS = 170
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled", "--start-maximized",
    "--no-first-run", "--disable-infobars", "--disable-extensions", "--window-position=0,0"
]
STEALTH_JS = """() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    if (!window.chrome) { window.chrome = { runtime: {}, loadTimes: () => {}, csi: () => {}, app: {} }; }
    const oq = window.navigator.permissions.query;
    window.navigator.permissions.query = (p) => p.name === 'notifications' ? Promise.resolve({ state: 'denied' }) : oq(p);
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
    Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
}"""
CAPTCHA_SELECTORS = [
    '#captcha-verify-image', 
    '.captcha_verify_container', 
    '[id*="captcha"]', 
    'div:has-text("Verify you are human")',
    'div:has-text("Drag the slider to fit the puzzle")',
    'div:has-text("Slide to complete the puzzle")',
    'div:has-text("Drag the puzzle piece")',
    'div:has-text("Select 2 objects")',
    'div:has-text("Verify to continue")',
    '.captcha_verify_slide',
    '#captcha_container'
]
    'xpath=/html/body/div[1]/div[2]/div/div/div[3]/div[2]/button/div/div',
    'xpath=//*[@id="header-login-button"]',
    '[data-e2e="nav-login-button"]',
    'button:has-text("Log in")',
    'button:has-text("เข้าสู่ระบบ")',
    '#header-login-button',
    '#login-button'
]
RETURN_BTN_SELECTORS = [
    'xpath=/html/body/div[6]/div[2]/div[2]/div/div/div[2]/div/div/section/div/div[2]/div[2]/div[2]/button/div',
    'button:has-text("Return for now")',
    'div:has-text("Return for now")'
]


def cprint(text, color=Fore.WHITE, centered=True):
    for line in text.split('\n'):
        pad = ' ' * max(0, (COLS - len(line)) // 2) if centered else ''
        print(f"{pad}{color}{line}{Style.RESET_ALL}")


def gradient_banner(text):
    colors = [Fore.LIGHTRED_EX, Fore.RED, Fore.YELLOW, Fore.LIGHTYELLOW_EX]
    for i, line in enumerate(text.split('\n')):
        pad = ' ' * max(0, (COLS - len(line)) // 2)
        print(f"{pad}{colors[i % len(colors)]}{line}{Style.RESET_ALL}")


def detect_captcha(page):
    for sel in CAPTCHA_SELECTORS:
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                for i in range(loc.count()):
                    if loc.nth(i).is_visible():
                        cprint(f"[DEBUG] Captcha detected", Fore.YELLOW)
                        return True
        except:
            pass
    return False


def wait_for_captcha(page):
    if detect_captcha(page):
        cprint("\n⚠️ CAPTCHA DETECTED!", Fore.LIGHTYELLOW_EX)
        cprint("Attempting to close captcha...", Fore.CYAN)
        try:
            close_btn_xpath = 'xpath=/html/body/div[6]/div/div/div/div[1]/div[1]/button'
            close_btn = page.locator(close_btn_xpath)
            if close_btn.count() > 0 and close_btn.is_visible():
                close_btn.click(timeout=3000)
                page.wait_for_timeout(2000)
                
                if not detect_captcha(page):
                    cprint("✅ Captcha closed successfully.", Fore.GREEN)
                    return
        except:
            pass
            
        cprint("Hard-resetting Chrome to clear captcha...", Fore.CYAN)
        raise CaptchaRestartException()


def check_is_logged_in(page):
    try:
        if page.locator('[data-e2e="nav-profile-self-link"]').count() > 0:
            return True
        if page.locator('[data-e2e="inbox-icon"]').count() > 0:
            return True
        if page.locator('[data-e2e="profile-icon"]').count() > 0:
            if page.locator('[data-e2e="nav-login-button"]').count() == 0 and page.locator('button:has-text("Log in")').count() == 0:
                return True
        return False
    except:
        return False


def click_login_button(page):
    cprint("Attempting to click Log in button...", Fore.CYAN)
    try:
        for selector in LOGIN_BTN_SELECTORS:
            btns = page.locator(selector)
            for i in range(btns.count()):
                btn = btns.nth(i)
                if btn.is_visible():
                    try:
                        btn.click(timeout=5000, force=True)
                        return True
                    except:
                        continue

        btns = page.locator('button')
        for i in range(btns.count()):
            btn = btns.nth(i)
            try:
                btn_text = btn.inner_text().lower()
                if ('log in' in btn_text or 'เข้าสู่ระบบ' in btn_text) and btn.is_visible():
                    btn.click(timeout=5000, force=True)
                    return True
            except:
                continue
        return False
    except:
        return False


def handle_return_for_now(page):
    try:
        for sel in RETURN_BTN_SELECTORS:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                cprint("⚠️ 'Return for now' detected. Clicking...", Fore.YELLOW)
                try:
                    btn.click(timeout=5000, force=True)
                    page.wait_for_timeout(2000)
                    cprint("Refreshing page...", Fore.CYAN)
                    page.reload()
                    page.wait_for_timeout(5000)
                    return True
                except:
                    pass
    except:
        pass
    return False


def extract_handle(page):
    xpath = '//*[@id="main-content-messages"]/div/div[1]/div/a[2]/div/p[2]'
    try:
        if page.locator(xpath).count() > 0:
            return page.locator(xpath).first.inner_text().strip().lower()
    except:
        pass

    try:
        header = page.locator('[data-e2e="chat-room-title"] a, [data-e2e="chat-room-title"]').first
        if header.count() > 0:
            href = header.get_attribute("href")
            if href and "/@" in href:
                return href.split("/@")[1].split("?")[0].lower()
            return header.inner_text().strip().lower()
    except:
        pass

    try:
        h = page.locator('h2, h1, [data-e2e="chat-header-title"]').first
        if h.count() > 0:
            return h.inner_text().lower()
    except:
        pass

    return ""


def match_user(handle, targets):
    if not handle:
        return False
    if handle in targets:
        return True
    return any(t in handle or handle in t for t in targets)


def remove_matched(handle, targets):
    if handle in targets:
        targets.remove(handle)
    else:
        for t in list(targets):
            if t in handle or handle in t:
                targets.remove(t)
                break


def simulate_human(page):
    try:
        for _ in range(3):
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(2000)
            page.mouse.wheel(0, -200)
            page.wait_for_timeout(1000)
    except:
        pass


def resolve_username(page):
    username = get_username(page)
    if username == "Unknown":
        cprint("⚠️ Username is Unknown. Refreshing...", Fore.YELLOW)
        page.reload()
        page.wait_for_timeout(5000)
        username = get_username(page)
    return username


def send_fire_to_list(page):
    simulate_human(page)
    cprint("\n--- Starting TERM FIRE Automation ---", Fore.LIGHTMAGENTA_EX)
    try:
        with open('list.txt', 'r', encoding='utf-8') as f:
            targets = {line.strip().lower() for line in f if line.strip()}
        if not targets:
            cprint("list.txt is empty.", Fore.LIGHTRED_EX)
            return
        cprint(f"Loaded {len(targets)} users from list.txt", Fore.LIGHTGREEN_EX)
    except Exception as e:
        cprint(f"Error reading list.txt: {e}", Fore.RED)
        return

    try:
        cprint("Navigating to Messages...", Fore.LIGHTCYAN_EX)
        page.goto("https://www.tiktok.com/messages", timeout=60000)
        try:
            page.wait_for_selector('[data-e2e="chat-list-item"], div[class*="ChatList"]', timeout=15000)
        except:
            pass

        page.wait_for_timeout(3000)
        chat_items = page.locator('[data-e2e="chat-list-item"]')
        if chat_items.count() == 0:
            chat_items = page.locator('div[role="button"][class*="Chat"]')

        count = chat_items.count()
        cprint(f"Found {count} recent chats.", Fore.LIGHTYELLOW_EX)
        sent = 0

        for i in range(min(count, 50)):
            try:
                item = chat_items.nth(i)
                if not item.is_visible():
                    continue
                item.click()
                page.wait_for_timeout(1000)

                handle = extract_handle(page)
                cprint(f"   [{i+1}] Chat: '{handle}'", Fore.CYAN)

                if match_user(handle, targets):
                    cprint("      -> MATCH! Sending 🔥...", Fore.LIGHTRED_EX)
                    sel = '[contenteditable="true"][role="textbox"]'
                    if page.locator(sel).count() == 0:
                        sel = '.public-DraftEditor-content'
                    editor = page.locator(sel).first
                    if editor.count() > 0:
                        editor.click()
                        page.wait_for_timeout(500)
                        page.keyboard.type("🔥", delay=150)
                        page.wait_for_timeout(600)
                        page.keyboard.press("Enter")
                        sent += 1
                        cprint("      -> Sent.", Fore.LIGHTRED_EX)
                        remove_matched(handle, targets)
                        cprint(f"      Remaining: {len(targets)}", Fore.LIGHTGREEN_EX)
                        if not targets:
                            cprint("\n>>> ALL TARGET USERS MESSAGED. Stopping. <<<", Fore.LIGHTMAGENTA_EX)
                            return
                        page.wait_for_timeout(1500)
                else:
                    cprint("      -> Skip.", Style.DIM)
            except Exception as e:
                cprint(f"[DEBUG] Chat {i+1} error: {e}", Fore.YELLOW)
        cprint(f"--- Messaging Complete. Sent: {sent} ---", Fore.LIGHTMAGENTA_EX)
    except Exception as e:
        cprint(f"Error in send_fire: {e}", Fore.RED)


def get_username(page):
    cprint("Getting username...", Fore.LIGHTCYAN_EX)
    try:
        tux = page.locator('.TUXButton-label')
        for idx in range(tux.count()):
            if 'profile' in tux.nth(idx).inner_text().lower():
                tux.nth(idx).click()
                try:
                    page.wait_for_url("**/@*", timeout=5000)
                except:
                    page.wait_for_timeout(2000)
                if '/@' in page.url:
                    return page.url.split('/@')[1].split('?')[0].split('/')[0]

        for sel in ['[data-e2e="nav-profile-self-link"]', '[data-e2e="profile-icon"]']:
            el = page.locator(sel)
            if el.count() > 0 and el.first.is_visible():
                el.first.click()
                try:
                    page.wait_for_url("**/@*", timeout=5000)
                except:
                    page.wait_for_timeout(2000)
                if '/@' in page.url:
                    return page.url.split('/@')[1].split('?')[0].split('/')[0]

        title = page.locator('[data-e2e="user-title"]')
        if title.count() > 0:
            return title.first.text_content()
    except:
        pass
    return "Unknown"


def main():
    gradient_banner(BANNER)
    prompt = "Press Enter to start TERM FIRE message..."
    input("\n" + " " * ((COLS - len(prompt)) // 2) + f"{Fore.CYAN}{Style.BRIGHT}{prompt}{Style.RESET_ALL}")

    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except:
            pass

    cprint("Initializing TERM FIRE...", Fore.LIGHTMAGENTA_EX)
    with sync_playwright() as p:
        while True:
            try:
                cprint("Launching browser...", Fore.LIGHTCYAN_EX)
                try:
                    browser = p.chromium.launch_persistent_context(
                        user_data_dir='./tiktok_session_data', channel="chrome", headless=False,
                        viewport={"width": 1280, "height": 720}, args=BROWSER_ARGS,
                        ignore_default_args=["--enable-automation"], user_agent=UA
                    )
                except:
                    browser = p.chromium.launch_persistent_context(
                        user_data_dir='./tiktok_session_data', headless=False,
                        viewport={"width": 1280, "height": 720}, args=BROWSER_ARGS,
                        ignore_default_args=["--enable-automation"], user_agent=UA
                    )

                page = browser.pages[0]
                page.add_init_script(STEALTH_JS)

                cprint("Navigating to TikTok...", Fore.LIGHTBLUE_EX)
                try:
                    page.mouse.move(150, 150)
                    page.goto("https://www.tiktok.com", wait_until="domcontentloaded", timeout=60000)
                except:
                    pass

                page.wait_for_timeout(5000)
                handle_return_for_now(page)
                wait_for_captcha(page)

                if check_is_logged_in(page):
                    username = resolve_username(page)
                    cprint(f"\n✅ LOGGED IN as: {username}", Fore.LIGHTGREEN_EX)
                    send_fire_to_list(page)
                else:
                    cprint("\n❌ NOT logged in.", Fore.LIGHTRED_EX)
                    click_login_button(page)
                    cprint("\n>> PLEASE LOG IN MANUALLY in the opened window <<", Fore.LIGHTMAGENTA_EX)
                    while True:
                        if check_is_logged_in(page):
                            cprint("\nSuccess! Login detected.", Fore.LIGHTGREEN_EX)
                            page.wait_for_timeout(2000)
                            username = resolve_username(page)
                            cprint(f"✅ LOGGED IN as: {username}", Fore.LIGHTGREEN_EX)
                            send_fire_to_list(page)
                            break
                        handle_return_for_now(page)
                        time.sleep(1)

                cprint("\n[SCHEDULE] Scheduler Active. Press Ctrl+C to stop.", Fore.LIGHTCYAN_EX)
                while True:
                    now = datetime.datetime.now()
                    target = now.replace(hour=0, minute=1, second=0, microsecond=0)
                    if now >= target:
                        target += datetime.timedelta(days=1)

                    delta = (target - now).total_seconds()
                    cprint(f"[WAIT] Waiting {int(delta//3600)}h {int((delta%3600)//60)}m until {target.strftime('%H:%M:%S')}...", Fore.LIGHTBLUE_EX)

                    while datetime.datetime.now() < target:
                        time.sleep(1)

                    cprint("\n[SCHEDULE] Refreshing TikTok...", Fore.LIGHTCYAN_EX)
                    page.goto("https://www.tiktok.com", timeout=60000)
                    page.wait_for_timeout(5000)
                    handle_return_for_now(page)
                    wait_for_captcha(page)

                    cprint("[SCHEDULE] Executing daily task...", Fore.LIGHTGREEN_EX)
                    if check_is_logged_in(page):
                        username = resolve_username(page)
                        cprint(f"✅ Active as: {username}", Fore.LIGHTGREEN_EX)
                        send_fire_to_list(page)
                    else:
                        cprint("Session expired or NOT logged in.", Fore.RED)
                        click_login_button(page)
                        cprint("Waiting for manual login...", Fore.LIGHTMAGENTA_EX)

            except CaptchaRestartException:
                cprint("Restarting in 5 seconds...", Fore.CYAN)
                browser.close()
                time.sleep(5)
                continue
            except KeyboardInterrupt:
                cprint("\nExiting...", Fore.RED)
                try: browser.close()
                except: pass
                sys.exit(0)
            except Exception as e:
                cprint(f"\nFatal error: {e}", Fore.RED)
                try: browser.close()
                except: pass
                time.sleep(5)
                continue


if __name__ == "__main__":
    main()