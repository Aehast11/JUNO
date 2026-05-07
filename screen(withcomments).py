import math
import random


bg_base = Color(11, 15, 25)
bg_header = Color(21, 26, 39) 
bg_card = Color(19, 26, 38)
bg_tab = Color(17, 22, 32)   
border_color = Color(39, 52, 84)
text_main = Color(255, 255, 255)
text_muted = Color(139, 149, 165)
blue_bright = Color(59, 130, 246)
green_bright = Color(34, 197, 94) 
yellow_bright = Color(245, 158, 11)
bar_bg = Color(44, 54, 74)

current_tab = 0
editing_motor = -1
touch_pressed_last = False

auto_side = 0
drive_mode = 0
auto_running = False
auto_timer = 0

batt_v = 12.6
batt_pct = 85
pneu_pressure = 75

enc_l = 1842
enc_r = 1839
enc_l_prev = 1842
enc_r_prev = 1839
heading = 0

path_x = 0
path_y = 0
wheelbase = 35  # cm
ticks_per_cm = 10

timer_secs = 15
timer_running = False

motors = [
    {'name': 'Drive FL', 'port': 1, 'limit': 11.0, 'load': 0.38},
    {'name': 'Drive FR', 'port': 2, 'limit': 11.0, 'load': 0.41},
    {'name': 'Drive BL', 'port': 10, 'limit': 11.0, 'load': 0.36},
    {'name': 'Drive BR', 'port': 11, 'limit': 11.0, 'load': 0.39},
    {'name': 'Lift', 'port': 5, 'limit': 11.0, 'load': 0.65},
    {'name': 'Intake', 'port': 6, 'limit': 5.5, 'load': 0.18},
]


def format_time(seconds):
    mins = math.floor(seconds / 60)
    secs = seconds % 60
    return '{:02d}:{:02d}'.format(mins, secs)

def draw_panel(x, y, w, h, fill_color, border_color=border_color):
    brain.screen.set_fill_color(fill_color)
    brain.screen.draw_rectangle(x, y, w, h)

    brain.screen.set_fill_color(border_color)
    brain.screen.draw_rectangle(x, y, w, 1)
    brain.screen.draw_rectangle(x, y + h - 1, w, 1)
    brain.screen.draw_rectangle(x, y, 1, h)
    brain.screen.draw_rectangle(x + w - 1, y, 1, h)

def is_in_bounds(tx, ty, x, y, w, h):
    return (x <= tx <= x + w) and (y <= ty <= y + h)



def draw_header():

    brain.screen.set_fill_color(bg_header)
    brain.screen.draw_rectangle(0, 0, 480, 50)


    brain.screen.set_fill_color(border_color)
    brain.screen.draw_rectangle(0, 49, 480, 1)


    brain.screen.set_pen_color(text_main)
    brain.screen.print_at('JUNO - by 9494a', x=44, y=29)

    brain.screen.set_pen_color(blue_bright)
    brain.screen.print_at(format_time(timer_secs), x=420, y=29)

    batt_color = green_bright if batt_v > 12.0 else (yellow_bright if batt_v > 10.5 else Color(239, 68, 68))
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('', x=260, y=18)
    brain.screen.set_pen_color(batt_color)
    brain.screen.print_at('{:.1f}V'.format(batt_v), x=260, y=33)

    pneu_color = green_bright if pneu_pressure > 50 else Color(239, 68, 68)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('', x=340, y=18)
    brain.screen.set_pen_color(pneu_color)
    brain.screen.print_at('{} PSI'.format(int(pneu_pressure)), x=340, y=33)

def draw_tabs():
    brain.screen.set_fill_color(bg_tab)
    brain.screen.draw_rectangle(400, 50, 80, 190)  # 190px height (240-50)

    tab_labels = ['', 'Pneumatics', 'Auto', 'Driver', 'Field', 'Calibrate']

    for i, label in enumerate(tab_labels):
        y_start = 50 + (i * 30)  # 30px per tab button

        if current_tab == i:
            # Active tab styling
            brain.screen.set_fill_color(bg_card)
            brain.screen.draw_rectangle(400, y_start, 80, 30)
            brain.screen.set_fill_color(text_muted)
            brain.screen.draw_rectangle(400, y_start + 29, 80, 1)  # bottom border
            brain.screen.set_pen_color(blue_bright)
        else:
            brain.screen.set_fill_color(bg_tab)
            brain.screen.set_pen_color(text_main)

        # Center text in tab button
        brain.screen.print_at(label, x=400 + (80 - len(label) * 6) // 2, y=y_start + 18)

def draw_status_tab():
    # Battery section (top of content area)
    draw_panel(8, 55, 384, 30, bg_card)  # 384px width (480-80-8)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('BATTERY', x=16, y=72)

    # Battery bar
    brain.screen.set_fill_color(bar_bg)
    brain.screen.draw_rectangle(120, 62, 250, 12)  # 12px height like HTML

    fill_w = int(250 * (batt_pct / 100.0))
    if batt_v > 12.0:
        batt_fill_color = green_bright
    elif batt_v > 10.5:
        batt_fill_color = yellow_bright
    else:
        batt_fill_color = Color(239, 68, 68)

    brain.screen.set_fill_color(batt_fill_color)
    brain.screen.draw_rectangle(120, 62, fill_w, 12)

    # Battery text
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(batt_fill_color)
    brain.screen.print_at('{:.1f} / 13'.format(batt_v), x=380, y=72)
    brain.screen.print_at('{}%'.format(int(batt_pct)), x=120, y=72)

    # Motor grid (2x3 grid like HTML)
    for i, m in enumerate(motors):
        row, col = i // 3, i % 3
        cx = 8 + (col * 126)  # 126px per card (384/3)
        cy = 98 + (row * 55)  # Dropped down a few pixels

        if m['load'] > 0.8:
            card_bg = Color(80, 40, 40)
            load_color = Color(239, 68, 68)
        elif m['load'] > 0.6:
            card_bg = Color(80, 60, 30)
            load_color = yellow_bright
        else:
            card_bg = bg_card
            load_color = blue_bright

        draw_panel(cx, cy, 120, 50, card_bg)

        brain.screen.set_fill_color(card_bg)
        brain.screen.set_pen_color(blue_bright)
        brain.screen.print_at(m['name'], x=cx + 6, y=cy + 16)
        brain.screen.set_pen_color(text_muted)
        brain.screen.print_at('P{}'.format(m["port"]), x=cx + 90, y=cy + 16)

        # Load bar (4px height like HTML)
        brain.screen.set_fill_color(bar_bg)
        brain.screen.draw_rectangle(cx + 6, cy + 26, 108, 4)

        load_w = int(108 * m['load'])
        brain.screen.set_fill_color(load_color)
        brain.screen.draw_rectangle(cx + 6, cy + 26, load_w, 4)

        # Load text
        brain.screen.set_fill_color(card_bg)
        brain.screen.set_pen_color(load_color)
        brain.screen.print_at('{}%'.format(int(m["load"] * 100)), x=cx + 6, y=cy + 44)
        brain.screen.set_pen_color(Color(128, 128, 128))
        brain.screen.print_at('{:.1f}W'.format(m["load"] * m["limit"]), x=cx + 50, y=cy + 44)

def draw_pneumatics_tab():
    # Gauge container (centered)
    draw_panel(8, 55, 384, 120, bg_card)

    # Pressure gauge (circular representation)
    center_x, center_y = 200, 115
    radius = 35

    # Gauge background
    brain.screen.set_fill_color(bar_bg)
    # Draw circle approximation with rectangles
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        x = center_x + int(radius * math.cos(rad))
        y = center_y + int(radius * math.sin(rad))
        brain.screen.draw_rectangle(x, y, 2, 2)

    # Pressure arc (green fill)
    pressure_angle = (pneu_pressure / 100.0) * 180 - 90
    brain.screen.set_fill_color(green_bright)
    # Simplified arc representation

    # Needle
    needle_angle = math.radians(pressure_angle)
    needle_x = center_x + int(radius * 0.8 * math.cos(needle_angle))
    needle_y = center_y + int(radius * 0.8 * math.sin(needle_angle))
    brain.screen.set_pen_color(text_main)
    brain.screen.draw_line(center_x, center_y, needle_x, needle_y)

    # Pressure text (centered in gauge)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(blue_bright)
    brain.screen.print_at('{}'.format(int(pneu_pressure)), x=center_x - 15, y=center_y - 5)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('PSI / 100', x=center_x - 25, y=center_y + 10)

    # Pressure bar (below gauge)
    draw_panel(8, 185, 384, 25, bg_card)
    brain.screen.set_fill_color(bar_bg)
    brain.screen.draw_rectangle(50, 190, 320, 10)

    bar_width = int(320 * (pneu_pressure / 100.0))
    brain.screen.set_fill_color(green_bright)
    brain.screen.draw_rectangle(50, 190, bar_width, 10)

    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(green_bright)
    brain.screen.print_at('{}%'.format(int(pneu_pressure)), x=380, y=197)

def draw_auto_tab():
    # Auto side selection buttons (top)
    if auto_side == 0:
        draw_panel(8, 55, 188, 50, Color(22, 67, 110), border_color=blue_bright)  # cyan background
        brain.screen.set_pen_color(Color(20, 200, 200))  # cyan text
        brain.screen.print_at('LEFT', x=70, y=75)
    else:
        draw_panel(8, 55, 188, 50, bg_card)
        brain.screen.set_pen_color(text_muted)
        brain.screen.print_at('Left', x=80, y=75)

    if auto_side == 1:
        draw_panel(204, 55, 188, 50, Color(22, 67, 110), border_color=blue_bright)
        brain.screen.set_pen_color(Color(20, 200, 200))
        brain.screen.print_at('RIGHT', x=270, y=75)
    else:
        draw_panel(204, 55, 188, 50, bg_card)
        brain.screen.set_pen_color(text_muted)
        brain.screen.print_at('Right', x=280, y=75)

    # Expected score box
    draw_panel(8, 115, 384, 40, bg_card)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('Expected Score', x=140, y=125)
    brain.screen.set_pen_color(yellow_bright)
    brain.screen.print_at('{} PTS'.format(50 if auto_side == 0 else 55), x=170, y=140)

    # Start autonomous button (large, styled like HTML)
    if auto_running:
        draw_panel(8, 165, 384, 40, Color(31, 122, 80), border_color=green_bright)
        brain.screen.set_pen_color(green_bright)
        brain.screen.print_at('Autonomous Running...', x=120, y=185)
        brain.screen.print_at('{}'.format(format_time(auto_timer)), x=180, y=200)
    else:
        draw_panel(8, 165, 384, 40, Color(22, 45, 33), border_color=green_bright)
        brain.screen.set_pen_color(green_bright)
        brain.screen.print_at('▶ Start Autonomous', x=130, y=185)
        brain.screen.print_at('0:15', x=190, y=200)

def draw_driver_tab():
    # Drive mode buttons
    if drive_mode == 0:
        draw_panel(8, 55, 188, 50, Color(31, 55, 92), border_color=blue_bright)
        brain.screen.set_pen_color(blue_bright)
        brain.screen.print_at('Tank', x=70, y=75)
    else:
        draw_panel(8, 55, 188, 50, bg_card)
        brain.screen.set_pen_color(text_muted)
        brain.screen.print_at('Tank', x=80, y=75)

    if drive_mode == 1:
        draw_panel(204, 55, 188, 50, Color(31, 55, 92), border_color=blue_bright)
        brain.screen.set_pen_color(blue_bright)
        brain.screen.print_at('Default', x=260, y=75)
    else:
        draw_panel(204, 55, 188, 50, bg_card)
        brain.screen.set_pen_color(text_muted)
        brain.screen.print_at('Default', x=270, y=75)

    # Drive status box
    draw_panel(8, 115, 384, 30, bg_card)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('Mode', x=160, y=125)
    brain.screen.set_pen_color(blue_bright)
    brain.screen.print_at('Tank' if drive_mode == 0 else 'Default', x=150, y=140)

def draw_field_tab():
    # Field container
    draw_panel(8, 55, 384, 160, bg_card)

    # Field visualization (simplified representation)
    brain.screen.set_fill_color(Color(10, 14, 26))  # Dark field background
    brain.screen.draw_rectangle(40, 75, 320, 120)

    # Alliance zones
    brain.screen.set_fill_color(Color(59, 130, 246, 0.2))  # Blue zone
    brain.screen.draw_rectangle(40, 75, 144, 120)

    brain.screen.set_fill_color(Color(239, 68, 68, 0.2))  # Red zone
    brain.screen.draw_rectangle(216, 75, 144, 120)

    # Central tower
    brain.screen.set_fill_color(Color(75, 85, 95))
    brain.screen.draw_rectangle(190, 95, 20, 60)

    # Robot position
    scale = 1.0
    robot_x = 200 + int(path_x * scale)
    robot_y = 135 - int(path_y * scale)
    robot_x = max(50, min(350, robot_x))
    robot_y = max(85, min(185, robot_y))

    # Robot color based on position
    if path_x < -50:
        robot_color = Color(239, 68, 68)
    elif path_x > 50:
        robot_color = blue_bright
    else:
        robot_color = green_bright

    brain.screen.set_fill_color(robot_color)
    brain.screen.draw_rectangle(robot_x - 8, robot_y - 6, 16, 12)

    # Heading indicator
    heading_rad = math.radians(heading)
    arrow_len = 12
    arrow_x = robot_x + int(arrow_len * math.cos(heading_rad))
    arrow_y = robot_y - int(arrow_len * math.sin(heading_rad))
    brain.screen.set_pen_color(text_main)
    brain.screen.draw_line(robot_x, robot_y, arrow_x, arrow_y)

    # Field stats
    draw_panel(8, 225, 384, 25, bg_card)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(Color(20, 200, 200))
    brain.screen.print_at('X={:.1f} Y={:.1f} H={:.0f}°'.format(path_x, path_y, heading), x=60, y=240)

def draw_calibrate_tab():
    # Reset systems title
    brain.screen.set_fill_color(bg_base)
    brain.screen.set_pen_color(blue_bright)
    brain.screen.print_at('RESET SYSTEMS', x=16, y=60)

    # Reset buttons
    draw_panel(8, 75, 120, 30, bg_card)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('Reset Enc', x=25, y=90)

    draw_panel(136, 75, 120, 30, bg_card)
    brain.screen.print_at('Reset Head', x=145, y=90)

    draw_panel(264, 75, 128, 30, Color(80, 40, 40), border_color=Color(239, 68, 68))
    brain.screen.set_pen_color(Color(239, 68, 68))
    brain.screen.print_at('Reset All', x=290, y=90)

    # Motor test button
    draw_panel(8, 115, 384, 30, bg_card)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('Test Motors', x=150, y=130)

    # Sensor status
    brain.screen.set_fill_color(bg_base)
    brain.screen.set_pen_color(blue_bright)
    brain.screen.print_at('SENSOR STATUS', x=16, y=160)
    brain.screen.set_pen_color(green_bright)
    brain.screen.print_at('✓ Encoders: Ready', x=20, y=180)
    brain.screen.print_at('✓ Distance: Ready', x=20, y=195)
    brain.screen.print_at('✓ Odometry: Active', x=200, y=180)
    brain.screen.print_at('✓ Pneumatics: Ready', x=200, y=195)

def draw_modal():
    if editing_motor == -1:
        return

    m = motors[editing_motor]

    # Modal background (semi-transparent overlay)
    brain.screen.set_fill_color(Color(0, 0, 0, 0.7))
    brain.screen.draw_rectangle(0, 0, 480, 240)

    # Modal content
    draw_panel(60, 60, 360, 120, bg_header, border_color=Color(96, 112, 144))
    brain.screen.set_fill_color(bg_header)
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('PORT {}'.format(m["port"]), x=70, y=75)
    brain.screen.set_pen_color(text_main)
    brain.screen.print_at(m['name'], x=70, y=90)

    # Current load and power limit
    brain.screen.set_pen_color(text_muted)
    brain.screen.print_at('Current Load: {}%'.format(int(m["load"] * 100)), x=70, y=105)
    brain.screen.print_at('Power Limit: {}W'.format(m["limit"]), x=70, y=120)

    # Power limit buttons
    draw_panel(70, 135, 80, 25, bg_card)
    brain.screen.set_fill_color(bg_card)
    brain.screen.set_pen_color(text_main)
    brain.screen.print_at('2.75W', x=80, y=150)

    draw_panel(160, 135, 80, 25, bg_card)
    brain.screen.print_at('5.5W', x=175, y=150)

    draw_panel(250, 135, 80, 25, bg_card)
    brain.screen.print_at('11W', x=268, y=150)

    # Close button
    draw_panel(70, 170, 280, 20, Color(31, 67, 120))
    brain.screen.set_fill_color(Color(31, 67, 120))
    brain.screen.set_pen_color(blue_bright)
    brain.screen.print_at('CLOSE', x=180, y=180)

def draw_all():
    # Clear screen with background
    brain.screen.set_fill_color(bg_base)
    brain.screen.draw_rectangle(0, 0, 480, 240)

    # Draw app window border
    brain.screen.set_fill_color(border_color)
    brain.screen.draw_rectangle(0, 0, 480, 1)
    brain.screen.draw_rectangle(0, 239, 480, 1)
    brain.screen.draw_rectangle(0, 0, 1, 240)
    brain.screen.draw_rectangle(479, 0, 1, 240)

    draw_header()
    draw_tabs()

    # Draw current tab content
    if current_tab == 0:
        draw_status_tab()
    elif current_tab == 1:
        draw_pneumatics_tab()
    elif current_tab == 2:
        draw_auto_tab()
    elif current_tab == 3:
        draw_driver_tab()
    elif current_tab == 4:
        draw_field_tab()
    elif current_tab == 5:
        draw_calibrate_tab()

    draw_modal()

# ============================================================================
# TOUCH HANDLING - Exact conversion from HTML onclick handlers
# ============================================================================

def handle_touch():
    global current_tab, editing_motor, auto_side, drive_mode, auto_running, auto_timer
    global touch_pressed_last, enc_l, enc_r, heading, path_x, path_y

    pressing = brain.screen.pressing()

    if pressing and not touch_pressed_last:
        tx, ty = brain.screen.x_position(), brain.screen.y_position()

        if editing_motor != -1:
            if is_in_bounds(tx, ty, 70, 135, 80, 25):
                motors[editing_motor]['limit'] = 2.75
            elif is_in_bounds(tx, ty, 160, 135, 80, 25):
                motors[editing_motor]['limit'] = 5.5
            elif is_in_bounds(tx, ty, 250, 135, 80, 25):
                motors[editing_motor]['limit'] = 11.0
            elif is_in_bounds(tx, ty, 70, 170, 280, 20):
                editing_motor = -1
        else:
            # Tab selection (sidebar)
            if is_in_bounds(tx, ty, 400, 50, 80, 190):
                tab_idx = (ty - 50) // 30
                if 0 <= tab_idx < 6:
                    current_tab = tab_idx

            # Tab-specific touch handling
            elif current_tab == 0:
                # Motor cards in status tab
                for i in range(6):
                    row, col = i // 3, i % 3
                    cx = 8 + (col * 126)
                    cy = 95 + (row * 45)
                    if is_in_bounds(tx, ty, cx, cy, 120, 40):
                        editing_motor = i
                        break

            elif current_tab == 2:
                # Auto side selection
                if is_in_bounds(tx, ty, 8, 55, 188, 50):
                    auto_side = 0
                elif is_in_bounds(tx, ty, 204, 55, 188, 50):
                    auto_side = 1
                # Start autonomous button
                elif is_in_bounds(tx, ty, 8, 165, 384, 40):
                    auto_running = not auto_running
                    if auto_running:
                        auto_timer = 15

            elif current_tab == 3:
                # Drive mode selection
                if is_in_bounds(tx, ty, 8, 55, 188, 50):
                    drive_mode = 0
                elif is_in_bounds(tx, ty, 204, 55, 188, 50):
                    drive_mode = 1

            elif current_tab == 5:
                # Calibration buttons
                if is_in_bounds(tx, ty, 8, 75, 120, 30):
                    enc_l, enc_r, path_x, path_y = 0, 0, 0, 0
                elif is_in_bounds(tx, ty, 136, 75, 120, 30):
                    heading = 0
                elif is_in_bounds(tx, ty, 264, 75, 128, 30):
                    enc_l, enc_r, heading, path_x, path_y = 0, 0, 0, 0, 0
                elif is_in_bounds(tx, ty, 8, 115, 384, 30):
                    # Test all motors
                    for m in motors:
                        m['load'] = 0.5

    touch_pressed_last = pressing

# ============================================================================
# SIMULATION - Exact conversion from HTML JavaScript
# ============================================================================

def update_simulation():
    global batt_v, batt_pct, pneu_pressure, enc_l, enc_r, enc_l_prev, enc_r_prev
    global heading, path_x, path_y, auto_running, auto_timer, timer_secs

    batt_v = max(9.0, min(13.0, batt_v + random.uniform(-0.02, 0.02)))
    batt_pct = ((batt_v - 9.0) / 4.0) * 100.0

    for m in motors:
        m['load'] = max(0.0, min(1.0, m['load'] + random.uniform(-0.05, 0.05)))

    enc_l += random.randint(0, 8)
    enc_r += random.randint(0, 8)

    dl, dr = enc_l - enc_l_prev, enc_r - enc_r_prev

    if dl != 0 or dr != 0:
        dist_l = dl / ticks_per_cm
        dist_r = dr / ticks_per_cm
        dist_avg = (dist_l + dist_r) / 2.0
        dtheta = (dist_r - dist_l) / wheelbase
        heading = (heading + math.degrees(dtheta)) % 360
        theta_rad = math.radians(heading)
        path_x += dist_avg * math.cos(theta_rad)
        path_y += dist_avg * math.sin(theta_rad)

    enc_l_prev, enc_r_prev = enc_l, enc_r

    pneu_pressure = max(40, min(100, pneu_pressure + random.uniform(-2, 1)))

    if timer_running or auto_running:
        timer_secs = max(0, timer_secs - 1)
        if auto_running:
            auto_timer -= 1
            if auto_timer <= 0:
                auto_running = False

# ============================================================================
# MAIN LOOP - Exact conversion from HTML setInterval
# ============================================================================

counter = 0

while True:
    handle_touch()
    counter += 1
    if counter % 10 == 0:
        update_simulation()
    draw_all()
    wait(50, MSEC)
