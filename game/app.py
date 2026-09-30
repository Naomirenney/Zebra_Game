"""The zebra window.

Pick an account, read the rules, then run.
Jump over a rock to skip that payment. Run into it to pay it.
Run into a coin to collect money coming in.
The end screen lists what you paid, skipped, collected, and missed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

import pygame

from bank.forecast import ForecastResult
from game.logic import Create, apply_hit, build_creates, is_bankrupt, resolve_miss
from game import settings as S


@dataclass
class PlayableAccount:
    title: str
    forecast: ForecastResult


class Zebra:
    def __init__(self, image: pygame.Surface | None = None) -> None:
        self.x = S.ZEBRA_X
        self.y = S.GROUND_Y - S.ZEBRA_H
        self.vy = 0.0
        self.on_ground = True
        self.image = image
        if self.image:
            self.image = pygame.transform.scale(self.image, (S.ZEBRA_W, S.ZEBRA_H))

    def jump(self) -> None:
        self.vy = S.JUMP_VELOCITY
        self.on_ground = False
            
    def bounce(self) -> None:
        self.vy = S.BOUNCE_VELOCITY
        self.on_ground = False

    def update(self) -> None:
        self.vy += S.GRAVITY
        self.y += self.vy
        
        # Cap jump height to the top of the screen
        if self.y < 0:
            self.y = 0
            self.vy = max(0.0, self.vy)
            
        ground = S.GROUND_Y - S.ZEBRA_H
        if self.y >= ground:
            self.y = ground
            self.vy = 0
            self.on_ground = True

    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), S.ZEBRA_W, S.ZEBRA_H)

    def draw(self, surf: pygame.Surface) -> None:
        body = self.rect()
        if self.image:
            surf.blit(self.image, body)
        else:
            pygame.draw.rect(surf, S.COLOUR_ZEBRA_LIGHT, body)
            for i in range(0, S.ZEBRA_W, 4):
                pygame.draw.rect(surf, S.COLOUR_ZEBRA_DARK, pygame.Rect(body.x + i, body.y, 2, body.height))
            pygame.draw.rect(surf, S.COLOUR_ZEBRA_DARK, body, width=1)


def spawn_rect(spawn: Create, scroll: float) -> pygame.Rect:
    x = int(spawn.x - scroll)
    return pygame.Rect(x, S.GROUND_Y - spawn.size, spawn.size, spawn.size)


def draw_world(surf: pygame.Surface, danger_level: float = 0.0, bg_img: pygame.Surface | None = None) -> None:
    if bg_img:
        surf.blit(bg_img, (0, 0))
    else:
        # Pastel colors for gradient
        sky_top = (174, 217, 224)
        sky_bottom = (224, 247, 250)
        
        # Draw gradient
        for y in range(S.GROUND_Y):
            ratio = y / S.GROUND_Y
            r = int(sky_top[0] * (1 - ratio) + sky_bottom[0] * ratio)
            g = int(sky_top[1] * (1 - ratio) + sky_bottom[1] * ratio)
            b = int(sky_top[2] * (1 - ratio) + sky_bottom[2] * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (S.WORLD_WIDTH, y))
        
        # Draw some background jungle leaves
        pygame.draw.circle(surf, S.COLOUR_LEAVES, (100, 50), 60)
        pygame.draw.circle(surf, S.COLOUR_LEAVES, (300, 20), 80)
        pygame.draw.circle(surf, S.COLOUR_LEAVES, (600, 60), 70)
        pygame.draw.circle(surf, S.COLOUR_LEAVES, (800, 30), 90)

        # Draw ground
        pygame.draw.rect(surf, S.COLOUR_GROUND, pygame.Rect(0, S.GROUND_Y, S.WORLD_WIDTH, S.WORLD_HEIGHT - S.GROUND_Y))
        # Draw vibrant grass
        pygame.draw.rect(surf, S.COLOUR_GRASS, pygame.Rect(0, S.GROUND_Y, S.WORLD_WIDTH, 12))

    if danger_level > 0:
        overlay = pygame.Surface((S.WORLD_WIDTH, S.WORLD_HEIGHT), pygame.SRCALPHA)
        # 180 is max alpha for red danger
        overlay.fill((255, 0, 0, int(150 * danger_level)))
        surf.blit(overlay, (0, 0))


def draw_button(surf: pygame.Surface, font: pygame.font.Font, text: str, rect: pygame.Rect, active: bool = False) -> None:
    bg_color = S.COLOUR_BTN_BG if active else (120, 150, 120)
    pygame.draw.rect(surf, bg_color, rect, border_radius=12)
    pygame.draw.rect(surf, S.COLOUR_TEXT_OUTLINE, rect, width=3, border_radius=12)
    
    text_surf = font.render(text, True, S.COLOUR_TEXT)
    shadow_surf = font.render(text, True, S.COLOUR_TEXT_OUTLINE)
    surf.blit(shadow_surf, (rect.centerx - shadow_surf.get_width()//2 + 2, rect.centery - shadow_surf.get_height()//2 + 2))
    surf.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))


def run_game(accounts: list[PlayableAccount], today: date | None = None) -> None:
    today = today or date.today()
    pygame.init()
    window = pygame.display.set_mode((S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
    pygame.display.set_caption("Future You: Jungle Run")
    clock = pygame.time.Clock()
    
    # Initialize fun fonts
    try:
        font_title = pygame.font.SysFont(S.FONT_NAME, 56, bold=True)
        font_title_small = pygame.font.SysFont(S.FONT_NAME, 56, bold=True)
        font_big = pygame.font.SysFont(S.FONT_NAME, 26, bold=True)
        font_small = pygame.font.SysFont(S.FONT_NAME, 18, bold=True)
    except:
        font_title = pygame.font.SysFont("comicsansms", 56, bold=True)
        font_title_small = pygame.font.SysFont("comicsansms", 56, bold=True)
        font_big = pygame.font.SysFont("comicsansms", 26, bold=True)
        font_small = pygame.font.SysFont("comicsansms", 18, bold=True)

    world = pygame.Surface((S.WORLD_WIDTH, S.WORLD_HEIGHT))

    zebra_img_path = os.path.join(S.ASSETS_DIR, "Zebra.jpg")
    bug_img_path = os.path.join(S.ASSETS_DIR, "enemy_bug.jpg")
    menu_bg_path = os.path.join(S.ASSETS_DIR, "menu background.jpg")
    gameplay_bg_path = os.path.join(S.ASSETS_DIR, "gameplay_background.jpg")

    try:
        zebra_img = pygame.image.load(zebra_img_path).convert()
        zebra_img.set_colorkey((255, 255, 255))
    except Exception:
        zebra_img = None
    try:
        bug_img = pygame.image.load(bug_img_path).convert()
        bug_img.set_colorkey((255, 255, 255))
    except Exception:
        bug_img = None
        
    try:
        menu_bg = pygame.image.load(menu_bg_path).convert()
        menu_bg = pygame.transform.scale(menu_bg, (S.WINDOW_WIDTH, S.WINDOW_HEIGHT))
    except Exception:
        menu_bg = None
        
    try:
        gameplay_bg = pygame.image.load(gameplay_bg_path).convert()
        gameplay_bg = pygame.transform.scale(gameplay_bg, (S.WORLD_WIDTH, S.WORLD_HEIGHT))
    except Exception:
        gameplay_bg = None

    pick = 0
    scene = "home"
    zebra = Zebra(zebra_img)
    creates: list[Create] = []
    
    done: set[int] = set()
    hit: set[int] = set()
    stomped: set[int] = set()
    passed: set[int] = set()
    
    paid: list[str] = []
    skipped: list[str] = []
    collected: list[str] = []
    missed: list[str] = []
    scroll = 0.0
    balance = 0.0
    forecast = accounts[0].forecast

    active_tab = "Summary"
    scroll_offset = 0
    click_rects: dict[str, pygame.Rect] = {}

    def load_run() -> None:
        nonlocal zebra, creates, done, hit, stomped, passed, paid, skipped, collected, missed, scroll, balance, forecast, active_tab, scroll_offset
        forecast = accounts[pick].forecast
        zebra = Zebra(zebra_img)
        creates = build_creates(forecast, today)
        done = set()
        hit = set()
        stomped = set()
        passed = set()
        paid, skipped, collected, missed = [], [], [], []
        scroll = 0.0
        balance = forecast.starting_balance
        active_tab = "Summary"
        scroll_offset = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if scene == "over":
                    if event.button == 4: # Scroll up
                        scroll_offset = max(0, scroll_offset - 30)
                    elif event.button == 5: # Scroll down
                        scroll_offset += 30
                    elif event.button == 1:
                        mouse_pos = event.pos
                        for name, rect in click_rects.items():
                            if rect.collidepoint(mouse_pos):
                                if name == "play_again":
                                    scene = "home"
                                else:
                                    active_tab = name
                                    scroll_offset = 0
            elif event.type == pygame.KEYDOWN and scene == "home":
                if event.key == pygame.K_RETURN:
                    scene = "pick"
            elif event.type == pygame.KEYDOWN and scene == "pick":
                if event.key == pygame.K_UP:
                    pick = (pick - 1) % len(accounts)
                elif event.key == pygame.K_DOWN:
                    pick = (pick + 1) % len(accounts)
                elif event.key == pygame.K_RETURN:
                    scene = "intro"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and scene == "intro":
                load_run()
                scene = "play"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and scene == "play":
                zebra.jump()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and scene == "over":
                scene = "home"

        if scene == "play":
            zebra.update()
            scroll += S.SCROLL_SPEED
            zebra_rect = zebra.rect()
            for index, spawn in enumerate(creates):
                if index in done:
                    continue
                rect = spawn_rect(spawn, scroll)
                
                # We use flat label for end screen lists (untruncated for the list!)
                flat_label = f"{spawn.label} {spawn.amount:+.0f}"
                
                if zebra_rect.colliderect(rect):
                    # Stomp mechanic: if falling and hit the top third
                    if spawn.kind == "rock" and zebra.vy > 0 and zebra_rect.bottom <= rect.top + (rect.height / 3) + 10:
                        done.add(index)
                        stomped.add(index)
                        skipped.append(flat_label)
                        zebra.bounce()
                    else:
                        done.add(index)
                        hit.add(index)
                        balance = apply_hit(balance, spawn)
                        if spawn.kind == "rock":
                            paid.append(flat_label)
                        else:
                            collected.append(flat_label)

                elif rect.right < zebra.x:
                    done.add(index)
                    passed.add(index)
                    if resolve_miss(spawn.kind) == "skipped":
                        skipped.append(flat_label)
                    else:
                        missed.append(flat_label)
            if creates and all(index in done for index in range(len(creates))):
                scene = "over"
            elif not creates and scroll > S.WORLD_WIDTH:
                scene = "over"

        if scene == "play":
            # Calculate danger level for red sky
            danger_level = 0.0
            if forecast.starting_balance > 0:
                danger_level = max(0.0, min(1.0, 1.0 - (balance / forecast.starting_balance)))
            if is_bankrupt(balance):
                danger_level = 1.0

            draw_world(world, danger_level, gameplay_bg)
            
            for index, spawn in enumerate(creates):
                # Disappear if hit or stomped. If passed, it stays drawn and scrolls away!
                if index not in hit and index not in stomped:
                    rect = spawn_rect(spawn, scroll)
                    if rect.right > 0 and rect.left < S.WORLD_WIDTH:
                        if spawn.kind == "rock":
                            if bug_img:
                                scaled_bug = pygame.transform.scale(bug_img, (rect.width, rect.height))
                                world.blit(scaled_bug, rect)
                            else:
                                pygame.draw.rect(world, S.COLOUR_ROCK, rect)
                        else:
                            # Draw fruit (orange circle with leaf)
                            pygame.draw.ellipse(world, S.COLOUR_COIN, rect)
                            pygame.draw.ellipse(world, S.COLOUR_LEAVES, pygame.Rect(rect.centerx - 4, rect.top - 8, 12, 12))
                        
                        # Multi-line label logic (up to 17 chars, chunks of 8) for the game world
                        short_text = spawn.label[:17]
                        if len(spawn.label) > 17:
                            short_text += ".."
                            
                        chunks = [short_text[i:i+8] for i in range(0, len(short_text), 8)]
                        chunks.append(f"{spawn.amount:+.0f}")
                        
                        # Draw chunks bottom-up or top-down
                        line_height = 18
                        y_offset = rect.top - 10 - (len(chunks) * line_height)
                        
                        for chunk in chunks:
                            label_text = font_small.render(chunk, True, S.COLOUR_LABEL)
                            outline_text = font_small.render(chunk, True, S.COLOUR_LABEL_OUTLINE)
                            # Simple outline
                            for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
                                world.blit(outline_text, (rect.centerx - outline_text.get_width()//2 + dx, y_offset + dy))
                            world.blit(label_text, (rect.centerx - label_text.get_width()//2, y_offset))
                            y_offset += line_height

            zebra.draw(world)
            window.blit(pygame.transform.scale(world, (S.WINDOW_WIDTH, S.WINDOW_HEIGHT)), (0, 0))
            
            # HUD
            pygame.draw.rect(window, S.COLOUR_HUD, pygame.Rect(0, 0, S.WINDOW_WIDTH, 40))
            hud_colour = S.COLOUR_SKY_DANGER if is_bankrupt(balance) else S.COLOUR_TEXT
            flag = "  OVERDRAFT!" if is_bankrupt(balance) else ""
            window.blit(
                font_big.render(f"Balance: R{balance:,.0f}{flag}   SPACE: jump/stomp   ESC: quit", True, hud_colour),
                (12, 8),
            )
        else:
            # Menu screens
            if menu_bg:
                window.blit(menu_bg, (0, 0))
            else:
                draw_world(window, 0.0) # fallback background
                
            overlay = pygame.Surface((S.WINDOW_WIDTH, S.WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            window.blit(overlay, (0, 0))
            
            if scene != "over":
                title_surf = font_title.render("FUTURE YOU: JUNGLE RUN", True, S.COLOUR_COIN)
                shadow = font_title.render("FUTURE YOU: JUNGLE RUN", True, S.COLOUR_TEXT_OUTLINE)
                window.blit(shadow, (S.WINDOW_WIDTH//2 - shadow.get_width()//2 + 3, 23))
                window.blit(title_surf, (S.WINDOW_WIDTH//2 - title_surf.get_width()//2, 20))
            
            if scene == "home":
                prompt = font_big.render("Welcome to Future You: Jungle Run!", True, S.COLOUR_TEXT)
                shadow_p = font_big.render("Welcome to Future You: Jungle Run!", True, S.COLOUR_TEXT_OUTLINE)
                window.blit(shadow_p, (S.WINDOW_WIDTH//2 - shadow_p.get_width()//2 + 2, 182))
                window.blit(prompt, (S.WINDOW_WIDTH//2 - prompt.get_width()//2, 180))
                
                desc = font_small.render("This game runs through all your future transactions.", True, S.COLOUR_TEXT)
                shadow_d = font_small.render("This game runs through all your future transactions.", True, S.COLOUR_TEXT_OUTLINE)
                window.blit(shadow_d, (S.WINDOW_WIDTH//2 - shadow_d.get_width()//2 + 1, 241))
                window.blit(desc, (S.WINDOW_WIDTH//2 - desc.get_width()//2, 240))
                
                draw_button(window, font_big, "[ ENTER TO START ]", pygame.Rect(S.WINDOW_WIDTH//2 - 150, S.WINDOW_HEIGHT - 120, 300, 60), active=True)
                
            elif scene == "pick":
                prompt = font_big.render("Choose an account (Up/Down, then Enter):", True, S.COLOUR_TEXT)
                shadow_p = font_big.render("Choose an account (Up/Down, then Enter):", True, S.COLOUR_TEXT_OUTLINE)
                window.blit(shadow_p, (S.WINDOW_WIDTH//2 - shadow_p.get_width()//2 + 2, 92))
                window.blit(prompt, (S.WINDOW_WIDTH//2 - prompt.get_width()//2, 90))
                
                total_accounts = len(accounts)
                y = 140
                available_space = S.WINDOW_HEIGHT - 80 - y
                step = min(65, available_space // total_accounts)
                btn_height = min(55, step - 5)
                
                for index, account in enumerate(accounts):
                    # Widened from 500 to 700
                    btn_rect = pygame.Rect(S.WINDOW_WIDTH//2 - 350, y, 700, btn_height)
                    text = f"{account.title}   R{account.forecast.starting_balance:,.0f}"
                    draw_button(window, font_big, text, btn_rect, active=(index == pick))
                    y += step
                    
                draw_button(window, font_small, "[ ESC to Quit ]", pygame.Rect(S.WINDOW_WIDTH//2 - 100, S.WINDOW_HEIGHT - 60, 200, 40), active=False)

            elif scene == "intro":
                prompt = font_big.render(f"Ready to run: {accounts[pick].title}", True, S.COLOUR_COIN)
                shadow_p = font_big.render(f"Ready to run: {accounts[pick].title}", True, S.COLOUR_TEXT_OUTLINE)
                window.blit(shadow_p, (S.WINDOW_WIDTH//2 - shadow_p.get_width()//2 + 2, 122))
                window.blit(prompt, (S.WINDOW_WIDTH//2 - prompt.get_width()//2, 120))
                
                rules = [
                    "STOMP (jump on) biting insects to skip paying them.",
                    "Run into insects to pay your bills.",
                    "Collect delicious fruit for incoming cash."
                ]
                y = 200
                for rule in rules:
                    r_surf = font_big.render(rule, True, S.COLOUR_TEXT)
                    r_shad = font_big.render(rule, True, S.COLOUR_TEXT_OUTLINE)
                    window.blit(r_shad, (S.WINDOW_WIDTH//2 - r_shad.get_width()//2 + 2, y + 2))
                    window.blit(r_surf, (S.WINDOW_WIDTH//2 - r_surf.get_width()//2, y))
                    y += 50
                    
                draw_button(window, font_big, "[ ENTER TO START ]", pygame.Rect(S.WINDOW_WIDTH//2 - 150, S.WINDOW_HEIGHT - 120, 300, 60), active=True)

            else:
                title_text = (
                    "GAME OVER: Overdraft!"
                    if is_bankrupt(balance)
                    else "RUN FINISHED: Survived!"
                )
                t_surf = font_title_small.render(title_text, True, S.COLOUR_SKY_DANGER if is_bankrupt(balance) else S.COLOUR_COIN)
                t_shad = font_title_small.render(title_text, True, S.COLOUR_TEXT_OUTLINE)
                window.blit(t_shad, (S.WINDOW_WIDTH//2 - t_shad.get_width()//2 + 3, 33))
                window.blit(t_surf, (S.WINDOW_WIDTH//2 - t_surf.get_width()//2, 30))
                
                # Render White Panel like a Webpage Card
                panel_width = S.WINDOW_WIDTH - 80
                panel_height = S.WINDOW_HEIGHT - 240
                panel_rect = pygame.Rect(40, 130, panel_width, panel_height)
                
                panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
                pygame.draw.rect(panel, (255, 255, 255, 240), panel.get_rect(), border_radius=20)
                pygame.draw.rect(panel, S.COLOUR_LABEL, panel.get_rect(), width=4, border_radius=20)
                
                # Clear interactive rects for this frame
                click_rects.clear()

                # Draw tabs
                tabs = ["Summary", "Bills Paid", "Bills Dodged", "Cash Collected", "Cash Missed"]
                tab_x = 20
                for tab in tabs:
                    t_width = 120 if tab == "Summary" else 135
                    t_rect = pygame.Rect(tab_x, 20, t_width, 40)
                    
                    # Track absolute coords for mouse clicks
                    click_rects[tab] = pygame.Rect(t_rect.x + panel_rect.x, t_rect.y + panel_rect.y, t_rect.width, t_rect.height)
                    
                    color = (200, 200, 200, 255) if tab != active_tab else (100, 255, 100, 255)
                    pygame.draw.rect(panel, color, t_rect, border_radius=8)
                    pygame.draw.rect(panel, (0,0,0,255), t_rect, width=2, border_radius=8)
                    
                    lbl = font_small.render(tab, True, (0,0,0))
                    panel.blit(lbl, (t_rect.centerx - lbl.get_width()//2, t_rect.centery - lbl.get_height()//2))
                    
                    tab_x += t_width + 10
                
                # separator line
                pygame.draw.line(panel, (200, 200, 200), (20, 75), (panel_width - 20, 75), 2)
                
                # Content Area (mask for scrolling)
                content_rect = pygame.Rect(20, 85, panel_width - 40, panel_height - 100)
                panel.set_clip(content_rect)
                
                y_offset = 90 - scroll_offset
                if active_tab == "Summary":
                    bal_text = f"Started R{forecast.starting_balance:,.0f}  ->  Finished R{balance:,.0f}"
                    b_surf = font_big.render(bal_text, True, S.COLOUR_END_TEXT)
                    panel.blit(b_surf, (panel_width//2 - b_surf.get_width()//2, y_offset))
                    y_offset += 40
                    
                    danger = (
                        f"First red day if all bills paid: {forecast.danger_on}."
                        if forecast.danger_on
                        else "You stayed above zero!"
                    )
                    panel.blit(font_big.render(danger, True, S.COLOUR_END_TEXT), (30, y_offset))
                    y_offset += 40
                    
                    panel.blit(font_small.render(f"Total Bills Paid: {len(paid)}", True, S.COLOUR_END_TEXT), (30, y_offset)); y_offset += 25
                    panel.blit(font_small.render(f"Total Bills Dodged: {len(skipped)}", True, S.COLOUR_END_TEXT), (30, y_offset)); y_offset += 25
                    panel.blit(font_small.render(f"Total Cash Collected: {len(collected)}", True, S.COLOUR_END_TEXT), (30, y_offset)); y_offset += 25
                    panel.blit(font_small.render(f"Total Cash Missed: {len(missed)}", True, S.COLOUR_END_TEXT), (30, y_offset)); y_offset += 25
                    
                else:
                    items = paid if active_tab == "Bills Paid" else skipped if active_tab == "Bills Dodged" else collected if active_tab == "Cash Collected" else missed
                    if not items:
                        panel.blit(font_big.render("None!", True, S.COLOUR_END_TEXT), (30, y_offset))
                    for item in items:
                        panel.blit(font_small.render("- " + item, True, S.COLOUR_END_TEXT), (30, y_offset))
                        y_offset += 25
                
                # cap scroll
                max_scroll = max(0, y_offset + scroll_offset - 90 - content_rect.height + 20)
                if scroll_offset > max_scroll: 
                    scroll_offset = max_scroll
                
                panel.set_clip(None) # reset clip
                window.blit(panel, panel_rect)
                
                # Play again button at the very bottom
                play_btn_rect = pygame.Rect(S.WINDOW_WIDTH//2 - 180, S.WINDOW_HEIGHT - 90, 360, 70)
                draw_button(window, font_big, "[ ENTER TO PLAY AGAIN ]", play_btn_rect, active=True)
                click_rects["play_again"] = play_btn_rect

        pygame.display.flip()
        clock.tick(S.FPS)

    pygame.quit()
