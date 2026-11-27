import pygame, os, math, time, sys, asyncio
import functions as fn

# True when running in the browser (Pyodide reports "emscripten")
WEB = sys.platform == "emscripten"

# If 1: is used in several places to allow for closing of code blocks to keep it neat
if 1:  # Initiable variables
    pygame.init()

    grid_size = 15

    # Get the device's screen resolution
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h

    # Fallback in case the display dimensions aren't available
    if screen_width <= 0 or screen_height <= 0:
        screen_width, screen_height = 960, 640

    # In the browser the "monitor" size is meaningless, so use a fixed canvas size
    if WEB:
        screen_width, screen_height = 960, 640

    screen = pygame.display.set_mode((screen_width, screen_height), pygame.SCALED | pygame.RESIZABLE)

    tile_size = screen.get_width() // grid_size
    grid, grid_2 = {}, {} # grid 1 and grid 2, grid 2 is meant for non visible tiles 
    layer = 1 # Current layer, 1 being the default layer
    cam = [0, 0, 0, 0] # Initial camera position (x, y, target_x, target_y) (Target being where the camera should go to)
    mouse = [0, 0, 0] # Defines mouse variables, X, Y, GRID_ID
    mouse_action_repeat = [False, False, False] # Defines mouse action repeat variables, Left click, Right click, Middle click
    key_action_repeat = {"space": False, "l": False}
    device_button_interaction = 0
    pygame.display.set_caption("Game") # Sets the window name
    clock = pygame.time.Clock()
    # File path for the current file, used to load images from the correct directory
    try:
        file_path = os.path.dirname(os.path.abspath(__file__))
    except NameError:  # __file__ may not exist depending on how the web runner starts the script
        file_path = os.getcwd()
    gui_state = None
    currently_placing, placement_queue = None, None
    tile_layer_data = [] # Defined in tile loading
    checkpoint = None # Checkpoint for player respawn
    moveable_objects = []
    font = pygame.font.Font(None, 32) # None = pygame's built-in default font (works on desktop and web)
    tick = 0
    particles = [] # List to hold particle objects
    checkpoint_progression = [[], 0] # Checkpoint coordinates, counter
    collectables = {"gem": {"collected": 0, "total": 0}} # Collected / Total
    death_counter = 0

    # To be used for data collection
    gamestate_data_log = {"elements": [], "variables": [], "theme": []}
    gameplay_data_log = {"deaths": [], "playtime": 0, "progressionstall": []}

# Load tiles (Map tiles and assets)
if 1:
    raw_tile = [ # Loads tile textures (file, scale_x, scale_y, render_offset_y, render_offset_x)
    ["eraser.png", 1, 1, 0, 0], # 0, Not a tile, used to erase tiles
    ["Closed.png", 1, 1, 0, 0], # 1, No collision
    ["Open.png", 1, 1, 0, 0], # 2, Has collision
    ["flag1.png", 1, 1, 0, 0], # 3, Grid 2, invisible tile
    ["spike.png", 1, 1, 0, 0], # 4, Has collision
    ["lava1.png", 1, 1, 0, 0], # 5, Has collision
    ["flag2.png", 1, 2, -0.9, 0], # 6, Has no collision
    ["flag3.png", 1, 2, -0.9, 0], # 7, Has no collision
    ["gem1.png", 0.8, 0.8, 0.15, 0.15], # 8, Collectable
    ]

    raw_assets = [
        ["phone_icon.png", 3, 3, 0, 0], # 0, Loading asset
        ["desktop_icon.png", 3, 3, 0, 0], # 1, Loading asset 
    ]

    has_collision = [2, 4, 5, 8] # Defines which tiles have collision
    tile_layer_data = [(), (1, 2, 4, 5, 6, 7, 8), (3, 999)] # First entry is empty because of zero indexing, 
    raw_player_tiles = [ # Loads player textures
    "idle1.png", # 0
    "idle2.png", # 1
    "idle3.png", # 2
    "idle4.png", # 3
    "idle5.png", # 4
    "walking1.png", # 5
    "walking2.png", # 6
    "walking3.png", # 7
    "walking4.png", # 8
    "walking5.png", # 9
    "running1.png", # 10
    "running2.png", # 11
    "running3.png", # 12
    "running4.png", # 13
    "running5.png", # 14
    "jumping1.png", # 15
    "jumping2.png", # 16
    "jumping3.png", # 17
    "jumping4.png", # 18
    "jumping5.png", # 19
    ]

def load_tiles(tile_list, tile_path, tile_size):
    loaded_tiles = []
    for img in tile_list:
        object = (pygame.image.load(os.path.join(tile_path, img[0])))
        loaded_tiles.append((pygame.transform.scale(object, (tile_size*img[1], tile_size*img[2])), img[3], img[4])) # Scales all tiles to correct size
    return loaded_tiles

def load_player_tiles(tile_list, tile_path, tile_size):
    loaded_tiles = []
    for img in tile_list:
        object = (pygame.image.load(os.path.join(tile_path, img)))
        scaling_factor = 1.2  # Define the scaling factor for player tiles
        loaded_tiles.append(pygame.transform.scale(object, (tile_size/scaling_factor, tile_size*2/scaling_factor))) # Scales all tiles to correct size
    return loaded_tiles

tile = load_tiles(raw_tile, os.path.join(file_path, "Tiles"), tile_size)
player_tile = load_player_tiles(raw_player_tiles, os.path.join(file_path, "Player_tiles"), tile_size)
assets = load_tiles(raw_assets, os.path.join(file_path, "Tiles"), tile_size)

# Classes
class player():
    def __init__(self, name, x, y, state = 0):
        self.name = name
        self.x = x
        self.y = y
        self.velocity_x = 0
        self.velocity_y = 0
        self.acceleration_x = 0.043
        self.acceleration_y = 0.03
        self.max_speed_x = 0.30
        self.max_speed_y = 0.30
        self.state = state
        self.touching_floor = True
        self.debug = False
        self.dir = "right"
        self.frame = 0
        self.frame_count = 0
        self.death_timer = 0

    def move(self, keys, touch_controls=None):
        if touch_controls is None:
            touch_controls = {}

        # Acceleration and deceleration
        if self.debug:
            self.velocity_x = 0
            self.velocity_y = 0

        if keys[pygame.K_a] or touch_controls.get("left", False):
            if self.debug:
                self.velocity_x = -self.max_speed_x
            else:
                self.velocity_x -= self.acceleration_x

        if keys[pygame.K_d] or touch_controls.get("right", False):
            if self.debug:
                self.velocity_x = self.max_speed_x
            else:
                self.velocity_x += self.acceleration_x

        if keys[pygame.K_w] or touch_controls.get("up", False):
            if self.debug:
                self.velocity_y = -self.max_speed_y
            elif self.touching_floor:
                self.frame = 16
                self.velocity_y = -self.max_speed_y

        if keys[pygame.K_s] or touch_controls.get("down", False):
            if self.debug:
                self.velocity_y = self.max_speed_y
            else:
                self.velocity_y += self.acceleration_y

        # Limit maximum speed
        if abs(self.velocity_x) > self.max_speed_x:
            self.velocity_x = self.max_speed_x * (math.copysign(1, self.velocity_x))  # Preserve the direction of velocity

        if abs(self.velocity_y) > self.max_speed_y:
            self.velocity_y = self.max_speed_y * (math.copysign(1, self.velocity_y))  # Preserve the direction of velocity
        
    def draw(self, surface, player_tile, offset_x=0, offset_y=0):
        converted_x, converted_y = fn.convert_grid_to_screen_coordinates(self.x, self.y, tile_size, cam)
        surface.blit(player_tile, ((converted_x + offset_x), (converted_y + offset_y)))  # Draw the player tile at the converted coordinates with offsets

    def gravity(self):
        if self.debug:
            return  # Skip gravity calculations if debug mode is enabled
        self.velocity_y += 0.02

    def drag(self):
        self.velocity_x = self.velocity_x*0.80
        if abs(self.velocity_x) < 0.005:
            self.velocity_x = 0

    def update_animation(self):
        if self.velocity_x > 0:
            self.dir = "right"
        elif self.velocity_x < 0:
            self.dir = "left"

        # Update frame based on movement, cycle frame count and add an offset per animation type
        if tick%8 == 0:
            self.frame_count += 1
            if self.frame_count >= 5:  # Reset frame count after 5
                self.frame_count = 0

            if self.velocity_x == 0 and self.velocity_y == 0:
                self.frame = 0+self.frame_count  # Idle frame, cycles 0-4

            elif abs(self.velocity_x) > 0 and abs(self.velocity_x) < 0.17:
                self.frame = 5+self.frame_count  # Walking frame, starts cycles 5-9

            elif abs(self.velocity_x) >= 0.17:

                self.frame = 10+self.frame_count  # Running frame, starts cycles 10-14

            # jumping animation
            if self.touching_floor == False:
                if self.velocity_y < 0:
                    self.frame = 16
                if self.velocity_y > 0:
                    self.frame = 17

    def death(self):
        particle_count = 20  # Number of particles to create
        for i in range(particle_count):
            particles.append(fn.create_particle(self.x, self.y, "blood", 360/particle_count*i/2*-1))

            self.velocity_x = 0
            self.velocity_y = 0
            self.touching_floor = True
            self.state = "dead"
            self.death_timer = 60  # Set the death timer to 60 frames (1 second at 60 FPS)

    def update_death(self):
        global death_counter
        death_counter+=1
        if self.state == "dead":
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.state = 0  # Reset state to alive
                self.x = checkpoint.x  # Reset position to checkpoint
                self.y = checkpoint.y
                self.velocity_x = 0
                self.velocity_y = 0
                self.touching_floor = True
        else: return  # If the player is not dead, do nothing



class map_tile():
    def __init__(self, x, y, layer, tile_type, dir=0):
        self.x = x
        self.y = y
        self.layer = layer
        self.tile_type = tile_type
        self.dir = dir
        self.tile_collision = False
        if self.tile_type in has_collision:
            self.tile_collision = True



##### Game loading


# Load initial map
with open(os.path.join(file_path, "mapcode.txt"), "r") as f:
    for line in f:
        map_code = line.strip()  # Read the map code from the file
        break  # Exit the loop after reading the first line

#grid = fn.make_grid(grid, 16, 16, map_tile)
grid, grid_2 = fn.load_map(map_code, map_tile)

# Find checkpoints
checkpoints = []
for key, index in grid_2.items():
    if grid_2[key].tile_type == 3: # Check if the tile is a checkpoint
        checkpoints.append(index) # Adds checkpoints to a list for later use

checkpoint = checkpoints[0] # Sets the first checkpoint as the default respawn point
moveable_objects.append({"object": player("player", checkpoint.x, checkpoint.y, state=0), "visible": True})
# Center the camera on the checkpoint
cam[0] = checkpoint.x * tile_size - screen.get_width() / 2
cam[1] = checkpoint.y * tile_size - screen.get_height() / 2

# Find collectables
for key, index in grid.items():
    match grid[key].tile_type:
        case 8:
            collectables["gem"]["collected"] += 1
            continue
        case _: continue

##### 

def adjust_tile_size():
    global tile, player_tile, assets, tile_size
    previous_tile_size = tile_size  # Store the previous tile size
    tile_size = screen.get_width() // grid_size  # Adjust tile size based on the new screen width and grid size
    if tile_size != previous_tile_size:
        tile = load_tiles(raw_tile, os.path.join(file_path, "Tiles"), tile_size)
        player_tile = load_player_tiles(raw_player_tiles, os.path.join(file_path, "Player_tiles"), tile_size)
        assets = load_tiles(raw_assets, os.path.join(file_path, "Tiles"), tile_size)
    



# Main loop
# The loops live inside an async function so the browser gets control back every frame
# (that is what `await asyncio.sleep(0)` does). Variables that are reassigned inside the loops
# and also used elsewhere in the file are declared global.
async def main():
    global screen, cam, checkpoint, tick, tile_size, mouse, moveable_objects
    global gui_state, currently_placing, placement_queue, layer
    global checkpoint_progression, device_button_interaction

    running = True
    device_selection_screen = True
    while device_selection_screen:
        clock.tick(60)
        screen.fill((40,40,40))
        events = pygame.event.get()
        fn.render_text(screen, font, "Please Select Device", offset_x=screen.get_width()*0.3, offset_y=screen.get_height()*0.2)
        device_button_interaction = fn.device_buttons(screen, tile_size, assets, device_button_interaction, events)
        if device_button_interaction in ("phone", "desktop"):
            device_selection_screen = False
            break

        for event in events: # Was a second pygame.event.get(), which always came back empty
            if event.type == pygame.QUIT:
                running = False
                device_selection_screen = False
                break

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.SCALED | pygame.RESIZABLE)

        adjust_tile_size()
        pygame.display.flip()
        await asyncio.sleep(0)  # Hand control back to the browser

    touch_points = {} # Must persist between frames so held fingers keep their buttons pressed
    while running:
        clock.tick(60)  # Limit the frame rate to 60 FPS
        tick+=1
        grids = (grid, grid_2) # Bundle grid layers (bad system but i dont need many layers)
        keys = pygame.key.get_pressed() # Get key presses
        touch_controls = {}
        events = pygame.event.get()


        # Functions calls
        checkpoint_binder = (checkpoint, checkpoints, checkpoint_progression)
        mouse = fn.mousebinderfunction(mouse, mouse_action_repeat, grids, tile_size, cam, map_tile, currently_placing, tile_layer_data, layer, checkpoint_binder)

        fn.render_play_grid(screen, grids, cam, tile, tile_size, currently_placing, checkpoint) # Render map based on grid

        fn.render_particles(screen, particles, cam, tile_size) # Render particles
        if device_button_interaction == "phone":
            touch_controls = fn.phone_controls(screen, events, touch_points, font)
        else:
            touch_controls = {}

        moveable_objects, cam, checkpoint = fn.handle_player_actions(moveable_objects, keys, screen, grids, tile_size, player_tile, cam, checkpoint_binder, collectables, touch_controls)

        placement_queue, close_gui = fn.render_gui(gui_state, screen, tile, mouse_action_repeat, currently_placing, placement_queue, tile_size) # Renders the gui and returns if it should be closed

        fn.render_ghost_tile(gui_state, screen, tile, mouse, currently_placing, cam, tile_size)

        placement_queue, currently_placing = fn.placement_queue(placement_queue, currently_placing, mouse_action_repeat) # Handles the queue

        if close_gui == True: # closes guis
            gui_state = None
            close_gui = False

        # Key presses
        if 1: # if state is just so that i can close this
            if keys[pygame.K_SPACE]: # Handle space bar presses
                # Toggle map tile selector gui
                if gui_state == None and not key_action_repeat["space"]:
                    gui_state = "map_tile_selector"
                    key_action_repeat["space"] = True

                elif gui_state == "map_tile_selector" and not key_action_repeat["space"]:
                    gui_state = None
                    key_action_repeat["space"] = True

            if keys[pygame.K_ESCAPE] and not WEB: # Quit if escape is pressed (desktop only, pointless in a browser tab)
                running = False
                break

            if keys[pygame.K_p]: # Send map code
                print("code")
                print(fn.save_map(grids))
                print("code")

            if keys[pygame.K_i]: # instant death
                for obj in moveable_objects:
                    if obj["object"].name == "player":
                        obj["object"].death()

            if keys[pygame.K_1]:
                layer = 1

            if keys[pygame.K_2]:
                layer = 2

            if keys[pygame.K_l] and not key_action_repeat["l"]: # toggle debug mode
                for obj in moveable_objects:
                    if obj["object"].name == "player":
                        obj["object"].debug = not obj["object"].debug
                        key_action_repeat["l"] = True
                    
                
            # Reset key presses
            for key in key_action_repeat:
                if key_action_repeat[key]:
                    access_key = key
                    if key == "space": # Handle special case for space key
                        access_key = key.upper()

                    if not keys[getattr(pygame, f"K_{access_key}")]:
                        key_action_repeat[key] = False

        # Handle events
        aspect_ratio = 1.5 
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.SCALED | pygame.RESIZABLE)

        # Update checkpoint progression
        checkpoint_progression = fn.checkpoint_progression_updater(checkpoint, checkpoint_progression)

        # Adjust tile size based on screen width and grid size
        adjust_tile_size()
            
        # Display debug information
        sx, sy = screen.get_size()
        sx, sy = sx / 100, sy / 100
        if round((screen.get_width() / screen.get_height()), 2) != aspect_ratio:
            fn.render_text(screen, font, f"Aspect Ratio: {screen.get_width() / screen.get_height():.3f}", offset_x = sx*2, offset_y=sy*1)
            fn.render_text(screen, font, f"Width: {screen.get_width()}, Height: {screen.get_height()}", offset_x = sx*2, offset_y=sy*4)
            
        if currently_placing != None:
            fn.render_text(screen, font, f"Currently Placing: {currently_placing}", offset_x = sx*85, offset_y=sy*1)
            fn.render_text(screen, font, f"Layer: {layer}", offset_x = sx*85, offset_y=sy*4)

        for obj in moveable_objects:
            if obj["object"].name == "player":
                if obj["object"].debug:
                    fn.render_text(screen, font, f"Player X: {obj['object'].x:.2f}, Player Y: {obj['object'].y:.2f}", offset_x = sx*2, offset_y=sy*7)
                    fn.render_text(screen, font, f"Velocity X: {obj['object'].velocity_x:.3f}, Velocity Y: {obj['object'].velocity_y:.3f}", offset_x = sx*2, offset_y=sy*10)
                    fn.render_text(screen, font, f"Touching Floor: {obj['object'].touching_floor}", offset_x = sx*2, offset_y=sy*13)
                    fn.render_text(screen, font, f"Frame: {obj['object'].frame}", offset_x = sx*2, offset_y=sy*16)
                    fn.render_text(screen, font, f"FPS: {clock.get_fps():.2f}", offset_x = sx*2, offset_y=sy*19)

        # Flip to next frame
        pygame.display.flip()
        await asyncio.sleep(0)  # Hand control back to the browser

    if not WEB:
        pygame.quit()


# Desktop entry point. In the browser, pygodide calls main() itself.
if __name__ == "__main__" and not WEB:
    asyncio.run(main())
