import pygame, zlib, base64, math, random
sprite_cache = {}
deadly_objects = [4,5] # List of tiles that are harmful
collectable_objects = [8]
# Collision handling
def rects_overlap(x, y, w, h, tx, ty, tw=1, th=1):
    return x < tx + tw and x + w > tx and y < ty + th and y + h > ty

def check_collisions_with_grid_y(x, y, w, h, grid, grid_2):

    bottom, top = False, False
    flag_triggered = False

    min_gx = math.floor(x) - 1
    max_gx = math.floor(x + w) + 1
    min_gy = math.floor(y) - 1
    max_gy = math.floor(y + h) + 1

    collision_tile_type = None

    collision_grid = {(gx, gy): tile for (gx, gy, _layer), tile in grid.items() if tile.tile_collision}

    flag_grid = {(gx, gy): tile for (gx, gy, _layer), tile in grid_2.items() if tile.tile_type == 3}

    for gx in range(min_gx, max_gx + 1):
        for gy in range(min_gy, max_gy + 1):

            if not rects_overlap(x, y, w, h, gx, gy):
                continue

            # Check for flags
            if (gx, gy) in flag_grid:
                flag_triggered = True

            # Check normal collisions
            tile = collision_grid.get((gx, gy))
            if tile is None:
                continue

            if gy >= y + h - 1:
                if tile.tile_type not in collectable_objects:
                    bottom = True
                else:
                    for (kx, ky, kl), ctile in grid.items():
                        if tile == ctile:
                            del grid[(kx, ky, kl)]
                            break
                collision_tile_type = tile.tile_type

            if gy + 1 <= y + 1:
                if tile.tile_type not in collectable_objects:
                    top = True
                else:
                    for (kx, ky, kl), ctile in grid.items():
                        if tile == ctile:
                            del grid[(kx, ky, kl)]
                            break
                collision_tile_type = tile.tile_type

    return bottom, top, collision_tile_type, flag_triggered

def check_collisions_with_grid_x(x, y, w, h, grid, grid_2):

    left, right = False, False
    flag_triggered = False

    min_gx = math.floor(x) - 1
    max_gx = math.floor(x + w) + 1
    min_gy = math.floor(y) - 1
    max_gy = math.floor(y + h) + 1

    collision_tile_type = None

    collision_grid = {(gx, gy): tile for (gx, gy, _layer), tile in grid.items() if tile.tile_collision}

    flag_grid = {(gx, gy): tile for (gx, gy, _layer), tile in grid_2.items() if tile.tile_type == 3}

    for gx in range(min_gx, max_gx + 1):
        for gy in range(min_gy, max_gy + 1):

            if not rects_overlap(x, y, w, h, gx, gy):
                continue

            # Check for flags
            if (gx, gy) in flag_grid:
                flag_triggered = True

            # Check normal collisions
            tile = collision_grid.get((gx, gy))
            if tile is None:
                continue

            if gx >= x + w - 1:
                if tile.tile_type not in collectable_objects:
                    right = True
                else:
                    for (kx, ky, kl), ctile in grid.items():
                        if tile == ctile:
                            del grid[(kx, ky, kl)]
                            break
                collision_tile_type = tile.tile_type

            if gx + 1 <= x + 1:
                if tile.tile_type not in collectable_objects:
                    left = True
                else:
                    for (kx, ky, kl), ctile in grid.items():
                        if tile == ctile:
                            del grid[(kx, ky, kl)]
                            break
                        
                collision_tile_type = tile.tile_type

    return left, right, collision_tile_type, flag_triggered

# Mouse handling
def mouse_postion(mouse, grids, tile_size, cam):
    grid = grids[0]
    mouse[0] = int((pygame.mouse.get_pos()[0] + cam[0]) // tile_size)
    mouse[1] = int((pygame.mouse.get_pos()[1] + cam[1]) // tile_size)
    mouse[2] = grid.get((mouse[0], mouse[1]), None)
    if mouse[2] != None:
        mouse[2] = mouse[2].tile_type
    return mouse

def mouse_interaction(mouse, mouse_action_repeat, grids, map_tile_class, currently_placing, tld, layer, checkpoints):
    grid, grid_2 = grids
    if mouse_action_repeat[0] == False: # Left mouse button one time action
        if pygame.mouse.get_pressed()[0] == True:
            mouse_action_repeat[0] = True

    elif pygame.mouse.get_pressed()[0] == False: # Reset left mouse button
        mouse_action_repeat[0] = False

    if mouse_action_repeat[1] == False: # Right mouse button one time action
        if pygame.mouse.get_pressed()[2] == True:
            mouse_action_repeat[1] = True

    elif pygame.mouse.get_pressed()[2] == False: # Reset left mouse button
            mouse_action_repeat[1] = False

    if pygame.mouse.get_pressed()[0]:
        if currently_placing is not None:
            if currently_placing == 0:  # Eraser
                # Goes through all tiles, deletes them if their coordinates match the cursor
                for tile_grid in (grid, grid_2):
                    for key in list(tile_grid.keys()):
                        if key[0] == mouse[0] and key[1] == mouse[1]:
                            del tile_grid[key]

                # Checks if there is a checkpoint on the tile being deleted            
                for i in range(len(checkpoints)-1, -1, -1):
                    checkpoint_tile = checkpoints[i]

                    if checkpoint_tile.x == mouse[0] and checkpoint_tile.y == mouse[1]:
                        del checkpoints[i]
                    

            tile_key = (mouse[0], mouse[1], layer)

            if currently_placing in tld[1]:
                target_grid = grid
            elif currently_placing in tld[2]:
                target_grid = grid_2
            else:
                target_grid = None

            if target_grid is not None:
                existing_tile = target_grid.get(tile_key)

                if existing_tile is None or existing_tile.tile_type != currently_placing:

                    if target_grid == grid_2:
                        checkpoints[:] = [cp for cp in checkpoints if (cp.x, cp.y, cp.layer) != tile_key]

                    new_tile = map_tile_class(mouse[0], mouse[1], layer, currently_placing, 0)

                    target_grid[tile_key] = new_tile

                    if target_grid == grid_2 and currently_placing == 3:
                        checkpoints.append(new_tile)

    grids = (grid, grid_2)
    return mouse_action_repeat, grids, checkpoints

def mousebinderfunction(mouse, mouse_action_repeat, grids, tile_size, cam, map_tile_class, currently_placing, tld, layer, checkpointbinder):
    checkpoints = checkpointbinder[1]
    mouse = mouse_postion(mouse, grids, tile_size, cam)
    mouse_action_repeat, grids, checkpoints = mouse_interaction(mouse, mouse_action_repeat, grids, map_tile_class, currently_placing, tld, layer, checkpoints)
    return mouse

def is_mouse_over(tile_x, tile_y, size): # Checks if the mouse is hovering over a tile in the GUI
    mouse_x, mouse_y = pygame.mouse.get_pos()
    return tile_x <= mouse_x <= tile_x + size and tile_y <= mouse_y <= tile_y + size

# Action handling
def handle_player_actions(moveable_objects, keys, screen, grids, tile_size, player_tiles, cam, checkpointbinder, collectables, touch_controls):
    checkpoint, checkpoints, checkpoint_progression = checkpointbinder
    grid, grid_2 = grids
    for object in moveable_objects:
            item = object["object"] 
            # Object specific interactions
            if item.name == "player":
                if 1: # Class function calls and variable declaration regarding the player
                    if item.state == 0: # Any state that isnt 0 implies that the player is immobile
                        item.move(keys, touch_controls)
                    item.gravity()
                    item.drag()
                    item.update_death()
                
                    # Check for collisions with the grid
                    item.x += item.velocity_x
                    width = 0.75
                    height = 1
                    scaling_factor = 0.84
                left, right, collision_tile_type_x, flag_triggered_x = check_collisions_with_grid_x(item.x, item.y, width, height, grid, grid_2)
                if item.velocity_x < 0 and left:
                    item.velocity_x = 0
                    item.x = math.floor(item.x) + 1

                elif item.velocity_x > 0 and right:
                    item.velocity_x = 0
                    item.x = math.floor(item.x + width) - width

                item.y += item.velocity_y
                bottom, top, collision_tile_type_y, flag_triggered_y = check_collisions_with_grid_y(item.x, item.y, width, height, grid, grid_2)

                if item.velocity_y > 0 and bottom:
                    item.velocity_y = 0
                    item.y = int(item.y)
                    item.touching_floor = True
                else: item.touching_floor = False
    
                if item.velocity_y < 0 and top:
                    item.velocity_y = 0
                    item.y = int(item.y) + height

                cache_key = (item.name, item.dir, tile_size, item.frame)

                if cache_key not in sprite_cache:
                    rawframe = pygame.transform.scale(player_tiles[item.frame], (int(tile_size / scaling_factor * 1.5), int(tile_size * 2 / scaling_factor)))

                    if item.dir == "left":
                        rawframe = pygame.transform.flip(rawframe, True, False)

                    sprite_cache[cache_key] = rawframe

                frame = sprite_cache[cache_key]

                # If the player isnt dead, run collision behavior and rendering
                if item.state != "dead":
                    # If player touched a flag
                    flag_triggered = flag_triggered_x or flag_triggered_y
                    if flag_triggered:
                        checkpoint = claim_checkpoint(checkpoint, checkpoints, checkpoint_progression, item, width, height)

                    # If player touched deadly object
                    if collision_tile_type_x in deadly_objects or collision_tile_type_y in deadly_objects:
                        item.death()

                    # If player touched a collectable
                    if collision_tile_type_x in collectable_objects or collision_tile_type_y in collectable_objects:
                        collectable = collision_tile_type_x if collision_tile_type_x in collectable_objects else collision_tile_type_y
                        match collectable:
                            case 8: collectable_type = "gem"
                            case _: collectable_type = "error"

                        if collectable_type == "error": print("issue with collectable type")
                        else:
                            collectables[collectable_type]["collected"] += 1

                    # If the object is the player, draw it with an offset for the player's height
                    item.draw(screen, frame, offset_x=-tile_size/2, offset_y=-tile_size*1.38)
                    item.update_animation()

                if 1: # Camera positioning and interpolation logic
                    # Calculate how many tiles fit vertically
                    visible_tiles_y = screen.get_height() / tile_size

                    # Player's current vertical position relative to the camera
                    cam_edge = cam[1] / tile_size
                    player_offset_y = item.y - cam_edge

                    # Keep the same relative camera boundaries at any aspect ratio
                    camera_top_limit = visible_tiles_y * 0.4
                    camera_target_y = visible_tiles_y * 0.8

                    if player_offset_y < camera_top_limit or player_offset_y > camera_target_y:
                        cam[3] = (item.y - camera_target_y) * tile_size

                    # adjust camera x
                    cam[2] = (item.x - screen.get_width()/tile_size/2) * tile_size # Line up x camera with player

                    # Interpolate camera position
                    cam[0] += (cam[2] - cam[0]) * 0.1
                    if abs((cam[2] - cam[0])*0.1) < 0.05:
                        cam[0] = cam[2]

                    cam[1] += (cam[3] - cam[1]) * 0.05
                    if abs((cam[3] - cam[1])*0.1) < 0.05:
                        cam[1] = cam[3]

    return moveable_objects, cam, checkpoint
 
# map saving and creation
def save_map(map_tiles):
    grid, grid_2 = map_tiles[0], map_tiles[1]
    tokens = [] # Creates token list
    for key, tile in grid.items(): # Loops through all tiles on layer 1
        tokens.append(f"{tile.x},{tile.y},{tile.layer},{tile.tile_type},{tile.dir},1") # Extracts data from object

    for key, tile in grid_2.items(): # Loops through all tiles on layer 2
        tokens.append(f"{tile.x},{tile.y},{tile.layer},{tile.tile_type},{tile.dir},2") # Extracts data from object

    raw = '|'.join(tokens) # Creates a string with spacers
    compressed = zlib.compress(raw.encode('utf-8'), level=9) # Compresses the string with zlib
    return str(base64.urlsafe_b64encode(compressed).decode('utf-8')) # Encodes it in base64 to make it smaller

def load_map(map_code, map_tile_class):
    map_code += '=' * (-len(map_code) % 4)  # Re-add padding if missing
    compressed = base64.urlsafe_b64decode(map_code.encode('utf-8')) # Undoes the base64 encoding
    raw = zlib.decompress(compressed).decode('utf-8') # Decompresses
    grid = {}
    grid_2 = {}
    for token in raw.split('|'): # Splits string by spacer
        x, y, l, t, d, gridlayer = token.split(',') # extract x y and type
        x, y, l, t, d = int(x), int(y), int(l), int(t), int(d) # Turns them into integers from string

        if gridlayer == "2": # If the tile is in layer 2, add it to grid_2
            grid_2[x, y, l] = map_tile_class(x, y, l, t, d)

        else: # If the tile is in layer 1, add it to grid
            grid[x, y, l] = map_tile_class(x, y, l, t, d)

    return grid, grid_2

def make_grid(grid, grid_length, grid_height, map_tile_class):
    for x in range(grid_length):
        for y in range(grid_height):
            grid[(x,y)] = map_tile_class(x, y, 1, 1, 0)
    for x in range(grid_length):
        grid[(x,6)] = map_tile_class(x, 6, 1, 2, 0)

    return grid

# Render
def render_gui(gui_state, screen, tiles, mouse_click, currently_placing, placement_queue, base_tile_size=64):
    # A pending selection takes priority.
    if placement_queue is not None:
        return placement_queue, False

    # If placing a tile
    if currently_placing is not None:

        # Opening the selector while placing requests deselection.
        if gui_state:
            return "deselect", False

        # Right-click deselects and closes the GUI.
        if mouse_click[1]:
            return "deselect", True

        # Otherwise keep the current selection.
        return currently_placing, False

    # If gui is closed and placing a tile
    if gui_state != "map_tile_selector":
        return None, False

    # Draw the background
    menu_rect = (screen.get_width() * 0.1, screen.get_height() / 2, screen.get_width() * 0.8, screen.get_height() * 0.4)

    pygame.draw.rect(screen, (47, 71, 110), menu_rect, int(screen.get_width() * 0.2))  # Draw the border

    pygame.draw.rect(screen, (10, 38, 84), menu_rect, int(screen.get_width() * 0.03))  # Draw the inner rectangle

    # Draw selectable tiles
    for index, sprite in enumerate(tiles):
        x, y = get_tile_selection_gui_position(index, base_tile_size, screen.get_width(), screen.get_height())
        offset_y = sprite[1] * base_tile_size
        offset_x = sprite[2] * base_tile_size
        screen.blit(sprite[0], (x+offset_x, y+offset_y))

        if is_mouse_over(x, y, base_tile_size) and mouse_click[0]:
            return index, True

    # If right clicking, close the menu.
    if mouse_click[1]:
        return None, True

    return None, False
    
def render_ghost_tile(gui_state, screen, tile_sprites, mouse, currently_placing, cam, tile_size):
    if currently_placing is None or gui_state:# If you are  ot placing something or a gui is open
        return # Do not render a ghost tile

    sprite = tile_sprites[currently_placing][0]
    offset_y = tile_sprites[currently_placing][1]
    offset_x = tile_sprites[currently_placing][1]
    screen_x = (mouse[0]+offset_x) * tile_size - cam[0]
    screen_y = (mouse[1]+offset_y) * tile_size - cam[1]

    screen.blit(sprite, (screen_x, screen_y)) # Render a temporary tile over the mouse

def render_play_grid(screen, grids, cam, tile_sprites, tile_size, currently_placing, checkpoint):
    grid, grid_2 = grids
    screen.fill((0,0,0))
    cam_x = cam[0] / tile_size
    cam_y = cam[1] / tile_size
    visible_tiles_x = screen.get_width() / tile_size
    visible_tiles_y = screen.get_height() / tile_size

    def render_action(tile, type_override = False):
        if cam_x-1 <= tile.x < cam_x + visible_tiles_x and cam_y-1 <= tile.y < cam_y + visible_tiles_y:
            if type_override == False:
                block = tile_sprites[tile.tile_type][0]
                offset_y = tile_sprites[tile.tile_type][1]
                offset_x = tile_sprites[tile.tile_type][2]
            else:
                block = tile_sprites[type_override][0]
                offset_y = tile_sprites[type_override][1]
                offset_x = tile_sprites[type_override][2]

            blit_x = (tile.x+offset_x) * tile_size - cam[0]
            blit_y = (tile.y+offset_y) * tile_size - cam[1]
            screen.blit(block, (blit_x, blit_y))


    layers = sorted({tile.layer for tile in grid.values()}) # Sorts all tiles in grid by layer

    for layer in layers: # For every layer in all layers 1-x
        for tile in grid.values(): # Select tile
            render_action(tile) # Render it
        

        if currently_placing != None: # Render grid 2 if placing tiles
            for key, tile in grid_2.items():
                render_action(tile)
        else: # Special rendering behavior for tiles in grid 2
            for key, tile in grid_2.items():
                if tile.tile_type == 3: # If its a checkpoint flag
                    if tile.x == checkpoint.x and tile.y == checkpoint.y:
                        render_action(tile, 7)
                    else:
                        render_action(tile, 6)

def render_text(screen, font, text, offset_x=0, offset_y=0):
    text = font.render(text, True, (255,0,0), None)
    screen.blit(text, (30+offset_x, 10+offset_y)) 

def render_particles(screen, particles, cam, tile_size):
    if not particles:
        return  # No particles to render
    
    else:
        for particle in particles[:]:  # Iterate over a copy so removing particles doesn't skip the next one
            particle["x"] += particle["velocity_x"]  # Update the particle's x position
            particle["y"] += particle["velocity_y"]  # Update the particle's y position
            screen_x = particle["x"] * tile_size - cam[0] + tile_size / 2  # Center the particle on the tile
            screen_y = particle["y"] * tile_size - cam[1] + tile_size / 2  # Center the particle on the tile
            particle["velocity_y"] += 0.01  # Apply gravity to the particle's vertical velocity
            particle["velocity_x"] *= 0.98  # Apply air resistance
            size = random.randint(2, 5)  # Random size for the particle
            size = size * tile_size / 64  # Scale the size based on the tile size
            pygame.draw.circle(screen, (255, 0, 0), (int(screen_x), int(screen_y)), size)  # Draw a small red circle for the particle
            particle["lifetime"] -= 1  # Decrease the lifetime of the particle
            if particle["lifetime"] <= 0:
                particles.remove(particle)  # Remove the particle if its lifetime is over

# Extra logic
def create_particle(x, y, particle_type, angle):
    particle = {
        "x": x,
        "y": y,
        "type": particle_type,
        "lifetime": 60,  # Lifetime in frames
        "velocity_x": random.uniform(0.1, 0.3) * math.cos(math.radians(angle)),  # Initial horizontal velocity based on angle
        "velocity_y": random.uniform(0.1, 0.3) * math.sin(math.radians(angle))   # Initial vertical velocity based on angle
    }
    return particle

def placement_queue(placement_queue, currently_placing, mouse_action_repeat):
    if placement_queue != None:
        if placement_queue == "deselect":
            currently_placing = None
            placement_queue = None
        elif mouse_action_repeat[0] != True:
            currently_placing = placement_queue
            placement_queue = None
    return placement_queue, currently_placing

def get_tile_selection_gui_position(index, base_tile_size, screen_width, screen_height): # Gets position for tiles in the placement menu
    items_per_row = 9
    row = index // items_per_row
    col = index % items_per_row

    x = screen_width * 0.07 + base_tile_size + col * base_tile_size * 1.2
    y = screen_height / 1.8 + row * base_tile_size

    return x, y

def checkpoint_progression_updater(checkpoint, checkpoint_progression):
    if (checkpoint.x, checkpoint.y) not in checkpoint_progression[0]:
        checkpoint_progression[1] += 1
        checkpoint_progression[0].append((checkpoint.x, checkpoint.y))
    return checkpoint_progression

def claim_checkpoint(checkpoint, checkpoints, checkpoint_progression, item, width, height):
    for instance in checkpoints:
        if rects_overlap(item.x, item.y, width, height, instance.x, instance.y):
            if instance is not checkpoint:
                if (instance.x, instance.y) not in checkpoint_progression[0]:
                    checkpoint = instance
            break
    return checkpoint

# Conversion
def convert_grid_to_screen_coordinates(grid_x, grid_y, tile_size, cam):
    screen_x = grid_x * tile_size - cam[0]
    screen_y = grid_y * tile_size - cam[1]
    return screen_x, screen_y

def convert_screen_to_grid_coordinates(screen_x, screen_y, tile_size, cam):
    grid_x = (screen_x + cam[0]) // tile_size
    grid_y = (screen_y + cam[1]) // tile_size
    return grid_x, grid_y


# Device selection

def render_single_asset(screen, asset, x, y):
    screen.blit(asset, (x, y)) 

def device_buttons(screen, tile_size, assets, touching, events):

    if touching == 1:
        left_rect = (screen.get_width() * 0.16, screen.get_height()*0.29, screen.get_width() * 0.3, screen.get_height() * 0.42)
        left_start_x, left_end_x, left_start_y, left_end_y = 0.16, 0.46, 0.29, 0.71
    else:
        left_rect = (screen.get_width() * 0.17, screen.get_height()*0.3, screen.get_width() * 0.28, screen.get_height() * 0.4)
        left_start_x, left_end_x, left_start_y, left_end_y = 0.17, 0.45, 0.3, 0.7

    if touching == 2:
        right_rect = (screen.get_width() * 0.58, screen.get_height()*0.29, screen.get_width() * 0.3, screen.get_height() * 0.42)
        right_start_x, right_end_x, right_start_y, right_end_y = 0.58, 0.88, 0.29, 0.71
    else:
        right_rect = (screen.get_width() * 0.59, screen.get_height()*0.3, screen.get_width() * 0.28, screen.get_height() * 0.4)
        right_start_x, right_end_x, right_start_y, right_end_y = 0.59, 0.87, 0.3, 0.7

    mouse_x, mouse_y = pygame.mouse.get_pos()
    touching = 0

    if screen.get_width()*left_start_x < mouse_x < screen.get_width()*left_end_x:
        if screen.get_height()*left_start_y < mouse_y < screen.get_height()*left_end_y:
            touching = 1

    if screen.get_width()*right_start_x < mouse_x < screen.get_width()*right_end_x:
        if screen.get_height()*right_start_y < mouse_y < screen.get_height()*right_end_y:
            touching = 2

    pygame.draw.rect(screen, (47, 71, 110), left_rect, tile_size*3, tile_size)
    pygame.draw.rect(screen, (47, 71, 110), right_rect, tile_size*3, tile_size)

    render_single_asset(screen, assets[0][0], screen.get_width() * 0.21, screen.get_height()*0.35)
    render_single_asset(screen, assets[1][0], screen.get_width() * 0.63, screen.get_height()*0.35)

    for event in events:
        if event.type == pygame.FINGERDOWN:
            mouse_x = event.x * screen.get_width()
            mouse_y = event.y * screen.get_height()

            if screen.get_width()*left_start_x < mouse_x < screen.get_width()*left_end_x:
                if screen.get_height()*left_start_y < mouse_y < screen.get_height()*left_end_y:
                    return "phone"

            if screen.get_width()*right_start_x < mouse_x < screen.get_width()*right_end_x:
                if screen.get_height()*right_start_y < mouse_y < screen.get_height()*right_end_y:
                    return "desktop"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if touching == 1:
                return "phone"
            elif touching == 2:
                return "desktop"

    return touching

def phone_controls(screen, events, touch_points, font):
    width, height = screen.get_size()

    size = min(width, height) * 0.13
    gap = size * 0.12

    # Left-side movement buttons
    left_x = width * 0.05
    left_y = height - size - height * 0.08

    # Right-side jump and down buttons
    right_x = width * 0.95 - size
    right_y = height - (size * 2 + gap) - height * 0.08

    buttons = {
        "left": pygame.Rect(left_x, left_y, size, size),
        "right": pygame.Rect(left_x + size + gap, left_y, size, size),
        "up": pygame.Rect(right_x, right_y, size, size),
        "down": pygame.Rect(right_x, right_y + size + gap, size, size)
    }

    # Track active fingers
    for event in events:
        if event.type == pygame.FINGERDOWN or event.type == pygame.FINGERMOTION:
            touch_points[event.finger_id] = (
                event.x * width,
                event.y * height
            )

        elif event.type == pygame.FINGERUP:
            touch_points.pop(event.finger_id, None)

    controls = {direction: False for direction in buttons}

    # Check whether any finger is pressing a button
    for pos in touch_points.values():
        for direction, rect in buttons.items():
            if rect.collidepoint(pos):
                controls[direction] = True

    # Draw buttons
    for direction, rect in buttons.items():
        color = (90, 130, 190) if controls[direction] else (47, 71, 110)
        pygame.draw.rect(screen, color, rect, border_radius=12)

        # Direction symbols
        symbols = {"up": "^", "down": "v", "left": "<", "right": ">"}
        text = font.render(symbols[direction], True, (255, 255, 255))
        screen.blit(text, text.get_rect(center=rect.center))

    return controls
