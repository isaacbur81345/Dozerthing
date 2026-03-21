import pygame
import win32gui
import win32con
import win32api
import sys
import random
import os
from pathlib import Path
from tkinter import simpledialog, messagebox
import tkinter as tk
import threading

pygame.time.wait(2000)  

current_path = Path(__file__).resolve()
parent_path = current_path.parent

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1920, 1080
WIDTH_HALF = WIDTH // 2
HEIGHT_HALF = HEIGHT // 2
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
sprite1_flipped = pygame.transform.flip(sprites[0], True, False)


dozersfx = pygame.mixer.Sound(BASE_DIR / "dozerthing.wav")

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

clock = pygame.time.Clock()
pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2)

dozerstate = 0
phasetime = 0
moving = False
what = False

settings_open = False
settingswindow = None

rotation = 0
last_rotation = None
current_sprite = sprites[0]
rotated_sprite = current_sprite
currentflip = sprite1_flipped

lowcounter = 9
flipping = False
count = 100
chancesetting = "Default (1 in 150 per second)"
cooldownsetting = "Default (10 seconds)"
punishmentset = "Close focused window, the recommended one"

cooldown = 300
chance = 75

renderedstuff = []

running = True
global ok
ok = [-1,-1]
windowotherthandozer = None
mode = 2 #close window default
dozah = True

def settingsthing():
    root = tk.Tk()
    root.title("Dozer Panel")
    root.geometry("600x400")
    global settings_open
    global settingswindow
    global dozerstate
    global dozah
    global chancesetting
    settingswindow = root.winfo_id()
    settings_open = True
    
    root.iconphoto(True, tk.PhotoImage(file=BASE_DIR / "Dozericon.png"))

    enabled = tk.BooleanVar(value=dozah)

    value = 0
    tvalue = 0
    insidevalue = dozah

    def wow(*args):
        if selected_coption.get() == "Custom":
            print("hi")
            simple = simpledialog.askinteger("Custom chance", "Set the chance (1 in ____)")
            nonlocal value
            if simple and simple > 0 and simple < 1000000:
                value = simple
            else:
                value = 150
                messagebox.showwarning("Invalid value", "Value outside allowed range. Set to default-")

    def twow(*args):
        if selected_toption.get() == "Custom":
            print("hi")
            simple = simpledialog.askinteger("Custom Cooldown", "Set the cooldown (1-600)")
            nonlocal tvalue
            if simple and simple > 0 and simple < 601:
                tvalue = simple
            else:
                tvalue = 10
                messagebox.showwarning("Invalid value", "Value outside allowed range. Set to default")

    lbl = tk.Label(root, text="Dozer Panel", font=("Comic Sans", 20)).pack(pady=0)
    lbl3 = tk.Label(root, text="Some utilities you need to know: f5 forcibly closes the application, f6 opens settings\nhmmm i think thats all the settings below are self explanatory\nalso the x button doesn't work idk why sooo use the save and close", font=("Comic Sans", 9)).pack(pady=2)

    lbl4 = tk.Label(root, text="Chance options", font=("Comic Sans", 9)).pack(pady=2)
    coptions = ["All the time. Chaos. (Guaranteed in every check)", "Really really high chances (1 in 20 per second)", "Really high chances (1 in 50 per second)", "High chances (1 in 100 per second)", "Default (1 in 150 per second)", "Low chances (1 in 300 per second)", "Really Low chances (1 in 600 per second)", "Baby mode (1 in 1200 per second)", "Custom"]
    coption_values = {
        coptions[0]: 1,
        coptions[1]: 10,
        coptions[2]: 25,
        coptions[3]: 50,
        coptions[4]: 75,
        coptions[5]: 150,
        coptions[6]: 300,
        coptions[7]: 600,
    }

    selected_coption = tk.StringVar(value=chancesetting)
    
    chdropdown = tk.OptionMenu(root, selected_coption, *coptions)
    selected_coption.trace_add("write", wow)
    chdropdown.pack()

    lbl4 = tk.Label(root, text="Cooldown options", font=("Comic Sans", 9)).pack(pady=2)
    toptions = ["No cooldown, the original experience. (2 seconds)", "Really really low cooldown (5 seconds)", "Really low cooldown (7 seconds)", "Default (10 seconds)", "Usual (15 seconds)", "A bit high (20 seconds)", "High (30 seconds)", "Higher (45 seconds)", "Baby mode (1 minute)", "Custom"]
    toption_values = {
        toptions[0]: 2,
        toptions[1]: 5,
        toptions[2]: 7,
        toptions[3]: 10,
        toptions[4]: 15,
        toptions[5]: 20,
        toptions[6]: 30,
        toptions[7]: 45,
        toptions[8]: 60,
    }

    selected_toption = tk.StringVar(value=cooldownsetting)
    
    tdropdown = tk.OptionMenu(root, selected_toption, *toptions)
    selected_toption.trace_add("write", twow)
    tdropdown.pack()

    lbl4 = tk.Label(root, text="Punishment options", font=("Comic Sans", 9)).pack(pady=2)
    poptions = ["Shutdown, the original experience.", "Close focused window, the recommended one", "Safe"]
    poption_values = {
        poptions[0]: 1,
        poptions[1]: 2,
        poptions[2]: 3,
    }

    selected_poption = tk.StringVar(value=punishmentset)
    
    pdropdown = tk.OptionMenu(root, selected_poption, *poptions)
    pdropdown.pack()
    
    tk.Checkbutton(root, text="Dozer Active", variable=enabled).pack(pady=5)
    lbl2 = tk.Label(root, text="", font=("Comic Sans", 8))

    def saveandclose():
        if dozerstate == 0:
            global dozah
            global settings_open
            global settingswindow
            global chance
            global cooldown
            global mode
            settings_open = False
            settingswindow = None
            dozah = enabled.get()

            global cooldownsetting
            cooldownsetting = selected_toption.get()

            global chancesetting
            chancesetting = selected_coption.get()

            global punishmentset
            punishmentset = selected_poption.get()

            if selected_coption.get() == "Custom":
                chance = value
                print(value)
            else:
                chance = coption_values[selected_coption.get()]
                print(coption_values[selected_coption.get()])

            if selected_toption.get() == "Custom":
                cooldown = tvalue *20
                print(tvalue)
            else:
                print(toption_values[selected_toption.get()])
                cooldown = toption_values[selected_toption.get()] *20

            mode = poption_values[selected_poption.get()]

            root.destroy()
        else:
            lbl2.configure(text="Can't do that right now!")

    def close():
        global settings_open
        global settingswindow
        settings_open = False
        settingswindow = None

    def save():
        if dozerstate == 0:
            global settings_open
            global dozah
            global chance
            global cooldown
            global mode

            global cooldownsetting
            cooldownsetting = selected_toption.get()

            global chancesetting
            chancesetting = selected_coption.get()

            global punishmentset
            punishmentset = selected_poption.get()

            if selected_coption.get() == "Custom":
                chance = value
                print(value)
            else:
                chance = coption_values[selected_coption.get()]
                print(coption_values[selected_coption.get()])

            if selected_toption.get() == "Custom":
                cooldown = tvalue *20
                print(tvalue)
            else:
                print(toption_values[selected_toption.get()])
                cooldown = toption_values[selected_toption.get()] *20

            mode = poption_values[selected_poption.get()]

            dozah = enabled.get()
        else:
            lbl2.configure(text="Can't do that right now!")

    def term():
        global running
        running = False

    tk.Button(root, text="Save", command=save).pack(pady=5)
    tk.Button(root, text="Save and close settings", command=saveandclose).pack(pady=5)
    tk.Button(root, text="Terminate application", command=term).pack(pady=5)
    lbl2.pack(pady=5)
    root.protocol("WM_DELETE_WINDOW", close)

    root.mainloop()


def openpanel():
    threading.Thread(target=settingsthing, daemon=True).start()

openpanel()

# main loop
while running:
    if dozerstate == 0:
        dt = clock.tick(20)
    else:
        dt = clock.tick(60)

    if dozah == False:
        dt = clock.tick(10)

        if win32api.GetAsyncKeyState(win32con.VK_F6) & 0x8000:
            if not settings_open:
                openpanel()

        if win32gui.IsIconic(hwnd) and dozerstate > 0:
            previous_hwnd = win32gui.GetForegroundWindow()
            if previous_hwnd != hwnd:
                windowotherthandozer = previous_hwnd
                win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
                #win32gui.SetForegroundWindow(previous_hwnd)
            elif dozerstate == 0 and not win32gui.IsIconic(hwnd):
                n = True
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

        screen.fill(TRANSPARENT_COLOR)

        pygame.display.update()
        continue

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
                    print("pressed key", key)
                    what = False
                break

    if win32api.GetAsyncKeyState(win32con.VK_F5) & 0x8000:
        running = False

    if win32api.GetAsyncKeyState(win32con.VK_F6) & 0x8000:
        if not settings_open:
            openpanel()

    if what:
        x, y = win32api.GetCursorPos()

        if ok == [-1, -1]:
            ok = [x, y]
        elif ok != [x, y]:
            print(ok)
            print([x,y])
            ok = [-1, -1]
            what = False

    if dozerstate == 0:
        count -= 1

    if count <= 0 and dozerstate == 0:
        count = 40
        if random.randint(1,chance) == 1:
            if dozerstate == 0:
                dozerstate = 1
                phasetime = 0
                count = cooldown
                moving = True
                current_sprite = sprites[0]
                latestattack = ""
                dozersfx.play()

    if win32gui.IsIconic(hwnd) and dozerstate > 0:
        previous_hwnd = win32gui.GetForegroundWindow()
        if previous_hwnd != hwnd:
            windowotherthandozer = previous_hwnd
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
            renderedstuff.insert(len(renderedstuff)+1, pygame.Vector2(0+(18*len(renderedstuff)),(HEIGHT-200)-(24*len(renderedstuff))))

        if phasetime == 120:
            if windowotherthandozer and mode == 2:
                try:
                    win32gui.PostMessage(windowotherthandozer, win32con.WM_CLOSE, 0, 0)
                except:
                    print("damn")

        if phasetime == 140:
            if mode == 1:
                os.system("shutdown /s /t 0")
            elif mode == 2:
                renderedstuff.clear()
                dozerstate = 0 #safe dozer

                if windowotherthandozer and windowotherthandozer != settingsthing:
                    try:
                        win32gui.PostMessage(windowotherthandozer, win32con.WM_CLOSE, 0, 0)
                    except:
                        print("damn")
            else:
                renderedstuff.clear()
                dozerstate = 0 #safe dozer


    if moving:
        lowcounter -= 1
        if lowcounter <= 0:
            lowcounter = 9
            flipping = not flipping
            offset_x = random.randrange(-10, 11)
            offset_y = random.randrange(-10, 11)

            if current_sprite == sprites[0] or current_sprite == sprite1_flipped:
                if flipping == True:
                    current_sprite = sprite1_flipped

            pos.update(WIDTH_HALF + offset_x, HEIGHT_HALF + offset_y)
            rotation = random.randrange(-7, 8)

    if rotation != last_rotation or current_sprite != last_sprite:
        rotated_sprite = pygame.transform.rotate(current_sprite, rotation)
        last_rotation = rotation
        last_sprite = current_sprite

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
