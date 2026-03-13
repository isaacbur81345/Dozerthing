import pygame
import win32gui
import win32con
import win32api
import sys
import random
import os

from pathlib import Path


pygame.time.wait(2000)  

current_path = Path(__file__).resolve()
parent_path = current_path.parent

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1920, 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
hwnd = pygame.display.get_wm_info()["window"]
pygame.display.set_caption("dozertypashii")


# --- Load sprites ---
BASE_DIR = Path(__file__).resolve().parent

icon = pygame.image.load(BASE_DIR / "Dozer1.png").convert_alpha()
pygame.display.set_icon(icon)

sprites = [
    pygame.image.load(BASE_DIR / f"Dozer{i}.png").convert_alpha()
    for i in range(1, 7)
]

wake = pygame.image.load(BASE_DIR / "wake.png").convert_alpha()
# --- Cache flipped sprites ---
sprite1_flipped = pygame.transform.flip(sprites[1], True, False)

# --- Sound ---
dozersfx = pygame.mixer.Sound(BASE_DIR / "dozerthing.wav")

# --- Window always on top + transparent ---
win32gui.SetWindowPos(
    hwnd,
    win32con.HWND_TOPMOST,
    0, 0, 0, 0,
    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
)

win32gui.SetWindowLong(
    hwnd,
    win32con.GWL_EXSTYLE,
    win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    | win32con.WS_EX_LAYERED| win32con.WS_EX_NOACTIVATE| win32con.WS_EX_TRANSPARENT
)

TRANSPARENT_COLOR = (255, 0, 255)
win32gui.SetLayeredWindowAttributes(
    hwnd,
    win32api.RGB(*TRANSPARENT_COLOR),
    0,
    win32con.LWA_COLORKEY
)

def close_window_by_title(window_title):
    """
    Finds and closes a window by its exact title.
    """
    # Find the window handle by title
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd == 0:
        print(f"Window with title '{window_title}' not found.")
        return False

    try:
        # Send WM_CLOSE message to the window
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        print(f"Sent close request to '{window_title}'.")
        return True
    except Exception as e:
        print(f"Error closing window: {e}")
        return False

# --- State ---
clock = pygame.time.Clock()
pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)

dozerstate = 0
phasetime = 0
moving = False
what = False

rotation = 0
last_rotation = None
current_sprite = sprites[0]
rotated_sprite = current_sprite

lowcounter = 9
flipping = False
count = 10

renderedstuff = []

running = True
global ok
ok = [-1,-1]

# --- Main loop ---
while running:
    dt = clock.tick(60)

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            if dozerstate == 0:
                phasetime = phasetime
                #running = False
    
    if what:
        for key in range(256):
            if win32api.GetAsyncKeyState(key) & 0x8000:
                if what:
                    what = False
                break

    if win32api.GetAsyncKeyState(win32con.VK_F5) & 0x8000:
        running = False

    if what:
        x, y = win32api.GetCursorPos()

        if ok == [-1, -1]:
            ok = [x, y]
        elif ok != [x, y]:
            print(ok)
            print([x,y])
            ok = [-1, -1]
            what = False

    count -= 1

    if count <= 0:
        count = 10
        if random.randint(1,6000000) == 1:
            if dozerstate == 0:
                dozerstate = 1
                phasetime = 0
                moving = True
                current_sprite = sprites[0]
                dozersfx.play()

    if win32gui.IsIconic(hwnd) and dozerstate > 0:
        #previous_hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
        #win32gui.SetForegroundWindow(previous_hwnd)
    elif dozerstate == 0 and not win32gui.IsIconic(hwnd):
        n = True
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

    if dozerstate == 1:
        phasetime += 1

        if phasetime == 6 * 18:
            current_sprite = sprites[1]
            what = True

        if phasetime == 6 * 22:
            if what:
                dozersfx.stop()
                dozerstate = 0
                rotation = 0
                what = False
                ok = [-1, -1]
                pos.update(WIDTH // 2, HEIGHT // 2)
            else:
                dozerstate = 2
                phasetime = 0
                moving = False
                what = False
                current_sprite = sprites[1]
                rotation = 0
                pos.update(WIDTH // 2, HEIGHT // 2)

    elif dozerstate == 2:
        phasetime += 1

        if phasetime == 5:
            current_sprite = sprites[2]
        elif phasetime == 7:
            current_sprite = sprites[3]
        elif phasetime == 10:
            current_sprite = sprites[4]
            dozerstate = 3
            phasetime = 0
            if len(renderedstuff) == 0:
                renderedstuff.insert(0, pygame.Vector2(0,HEIGHT-200))
    elif dozerstate == 3:
        phasetime += 1

        if phasetime == 10:
            current_sprite = sprites[5]

        if phasetime > 30 and phasetime % 3 == 0 and len(renderedstuff) < 20:
            renderedstuff.insert(0, pygame.Vector2(0+(18*len(renderedstuff)),(HEIGHT-200)-(24*len(renderedstuff))))

        if phasetime == 140:
            os.system("shutdown /s /t 0")


    if moving:
        lowcounter -= 1
        if lowcounter <= 0:
            lowcounter = 9
            flipping = not flipping
            rotation = random.randint(-7, 7)
            pos.update(
                WIDTH // 2 + random.randint(-10, 10),
                HEIGHT // 2 + random.randint(-10, 10)
            )

    if rotation != last_rotation or current_sprite != rotated_sprite:
        rotated_sprite = pygame.transform.rotate(current_sprite, rotation)
        last_rotation = rotation

    rect = rotated_sprite.get_rect(center=pos)

    screen.fill(TRANSPARENT_COLOR)

    if dozerstate == 3:
        screen.fill((0,0,0))

    if dozerstate > 0:
        screen.blit(rotated_sprite, rect)

    for h in renderedstuff:
        screen.blit(wake, h)

    pygame.display.update()

pygame.quit()

sys.exit()

