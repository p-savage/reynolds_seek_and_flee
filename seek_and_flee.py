import sys
import pygame
from enum import Enum, auto

class Mode(Enum):
    SEEK = auto()
    FLEE = auto()

class SeekerState(Enum):
    RETURNING = auto()
    FLEEING = auto()

INITIAL_MODIFIERS = {
    "mass": 1.0,
    "responsiveness": 1.0,
    "max_speed": 1.0,
    "max_force": 1.0,
    "flee_distance": 150,
    "calm_buffer": 1.1,
}

modifiers = INITIAL_MODIFIERS.copy()

SLIDER_LUTS = {
    "mass": (0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0),
    "responsiveness": (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0),
    "max_speed": (0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0),
    "max_force": (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0),
    "flee_distance": (50, 75, 100, 125, 150, 175, 200, 225, 250, 275),
    "calm_buffer": (1, 1.1, 1.3, 1.6, 2.0, 2.5),
}

class Seeker:
    """Class definition for seeker bots"""
    def __init__(self, x_pos, y_pos, color, max_speed, mass, radius):
        """Initialize seeker attributes"""
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.color = color
        self.max_speed = max_speed
        self.mass = mass
        self.radius = radius
        self.velocity = pygame.Vector2()
        self.state = SeekerState.RETURNING

class Slider:
    """Class for an interactive slider"""

    def __init__(
        self, 
        name: str, 
        screen, 
        x_pos: int,
        sliders_index: int, 
        init_lut_index: int, 
        colors: dict
    ):
        """Initialize slider attributes"""

        self.name = name
        self.screen = screen
        self.sliders_index = sliders_index
        self.spacing = 15
        self.size = (100, 40)
        self.x_pos = x_pos
        self.y_pos = (
            self.spacing
            + (self.spacing * self.sliders_index) 
            + (self.size[1] * self.sliders_index)
        )
        self.pos = self.x_pos, self.y_pos
        self.colors = colors
        self.lut_index = init_lut_index
        self.normalized_x = (
            self.lut_index 
            / (len(SLIDER_LUTS[self.name]) - 1)
        )
        self.slider_height = 4
        self.button_radius = self.slider_height * 2
        self.bounding_rect = pygame.Rect(
            self.pos[0], 
            self.pos[1], 
            self.size[0], 
            self.size[1],
        )
        self.slider_y = (
            self.bounding_rect.bottom 
            - self.slider_height
            - (self.button_radius - (self.slider_height / 2))
        )
        self.slider_rect = pygame.Rect(
            self.pos[0], 
            self.slider_y, 
            self.size[0], 
            self.slider_height,
        )
        self.slider_image = pygame.draw.rect(
            self.screen, 
            self.colors["cream"], 
            self.slider_rect,
        )
        self.button_x = (
            self.slider_rect.left 
            + (self.slider_rect.width * self.normalized_x)
        )
        self.button_y = (
            self.slider_rect.top 
            + (self.slider_height / 2)
        )
        self.button_image = pygame.draw.circle(
            self.screen, 
            self.colors["faded_purple"], 
            (self.button_x, self.button_y), 
            self.button_radius,
        )
        self.font = pygame.font.SysFont("Menlo", 14, bold=True)            
        self.slider_label_text = self.font.render(
            self.name, 
            True, 
            self.colors["yellow_cream"],
        )
        self.slider_label_rect = self.slider_label_text.get_rect()
        self.label_height = self.slider_label_rect.height
        self.width_diff = (
            self.slider_rect.width 
            - self.slider_label_rect.width
        )
        self.label_slider_gap = (
            self.slider_rect.top 
            - (self.label_height * 1.5)
        )
        
    def draw_slider(self, name):
        """Draw slider"""

        self.slider_rect = pygame.Rect(
            self.pos[0], 
            self.slider_y, 
            self.size[0], 
            self.slider_height,
        )
        self.slider_image = pygame.draw.rect(
            self.screen, 
            self.colors["cream"], 
            self.slider_rect,
        )
        self.button_image = pygame.draw.circle(
            self.screen, 
            self.colors["faded_purple"], 
            (self.button_x, self.button_y), 
            self.button_radius,
        )
        if name is not None and name == self.name:
            pygame.draw.circle(
                self.screen, 
                self.colors["cream"],
                (self.button_x, self.button_y), 
                self.button_radius + 2, 
                width=2,
            ) 
        
    def draw_slider_label(self):
        """Render slider label text"""

        self.screen.blit(
            self.slider_label_text, 
            (self.slider_rect.left + (self.width_diff / 2), 
            self.label_slider_gap),
        )
        
    def draw_slider_value(self, value):
        """Render the current slider value"""

        slider_value = self.font.render(
            f"{value}", 
            True, 
            self.colors["yellow_cream"],
        )
        slider_value_rect = slider_value.get_rect()
        button_overhang = self.button_radius / 2 + 5
        adjusted_x = self.slider_rect.right + button_overhang
        centered_y = (
            self.slider_rect.centery 
            - (slider_value_rect.height / 2)
        )
        self.screen.blit(slider_value, (adjusted_x, centered_y))

    def _check_buttons(self, active_slider, pos):
        """Dispatch mouse position for slider button behavior"""

        if active_slider is not None:
            if active_slider == self.name:
                x_pos = pos[0]
                normalized_x = self._normalize_x_pos(x_pos)
                mapped_lut_index = self._map_to_slider_context(
                    self.name, 
                    normalized_x,
                )
                self.button_x = (
                    self.slider_rect.left 
                    + (self.slider_rect.width * normalized_x)
                )
                return (self.name, mapped_lut_index)
            else:
                return None
        else:
            return None
        
    def _normalize_x_pos(self, x_pos):
        """Couple button center to mouse x_pos"""

        clamped_x = min(
            self.slider_rect.right, 
            max(self.slider_rect.left, x_pos),
        )
        distance_along_slider = clamped_x - self.slider_rect.left
        normalized_x = distance_along_slider / self.slider_rect.width
        return normalized_x
    
    def _map_to_slider_context(self, name, nx):
        """Take an x value and convert to a LUT index"""

        N = len(SLIDER_LUTS[name])
        index = min(int(nx * N), N - 1)
        return index
    
    def sync_ui(self):
        """Use modifiers variable to determine button x pos"""

        index = SLIDER_LUTS[self.name].index(modifiers[self.name])
        normalized_x = index / (len(SLIDER_LUTS[self.name]) - 1)
        self.button_x = (
            self.slider_rect.left 
            + (self.slider_rect.width * normalized_x)
        )

class ResetButton:
    """Reset button class"""

    def __init__(self, screen, screen_rect, edge_spacer, colors):
        """Initialize the reset button"""
        self.screen = screen
        self.screen_rect = screen_rect
        self.colors = colors
        self.font = pygame.font.SysFont("Menlo", 14, bold=True)
        self.text = self.font.render(
            "RESET", 
            True, 
            self.colors["yellow_cream"],
        )
        self.text_rect = self.text.get_rect()
        self.button_width = self.text_rect.width * 1.50
        self.button_text_width_diff = (
            self.button_width 
            - self.text_rect.width
        )
        self.button_height = self.text_rect.height * 1.50
        self.button_text_height_diff = (
            self.button_height
            - self.text_rect.height
        )
        self.x = edge_spacer
        self.y = (
            self.screen_rect.bottom 
            - (edge_spacer + self.button_height)
        )
        self.button_rect = pygame.rect.Rect(
            self.x,
            self.y,
            self.button_width,
            self.button_height,
        )
        
    def draw_reset_button(self, status):
        """Draw the reset button to the screen"""

        adjusted_x = (
            self.button_rect.left 
            + self.button_text_width_diff / 2
        )
        adjusted_y = (
            self.button_rect.top 
            + self.button_text_height_diff / 2
        )
        if not status:
            self.button_image = pygame.draw.rect(
                self.screen,
                self.colors["cream"],
                self.button_rect,
                width=2,
                border_radius=3,
            )
            self.screen.blit(self.text, (adjusted_x, adjusted_y))
        else:
            self.button_image = pygame.draw.rect(
                self.screen,            
                self.colors["cream"],
                self.button_rect,
                border_radius=3,
            )
            self.screen.blit(self.text, (adjusted_x, adjusted_y))
                
class SeekAndFlee:
    """House game assets"""

    def __init__(self):
        """Initialize game attributes"""

        pygame.init()
        self.screen = pygame.display.set_mode((800, 800))
        self.screen_rect = self.screen.get_rect()
        pygame.display.set_caption("SeekAndFlee")
        self.clock = pygame.time.Clock()
        self.colors = {
            "cream": pygame.Color('#fbf5ef'),
            "yellow_cream": pygame.Color('#f2d3ab'),
            "muted_orange": pygame.Color('#c69fa5'),
            "faded_purple": pygame.Color('#8b6d9c'),
            "blue_gray": pygame.Color('#494d7e'),
            "night_sky": pygame.Color('#272744'),
        }
        self.mouse_circle_radius = 5
        self.seekers = [
            Seeker(x_pos=160, 
                   y_pos=700, 
                   color=self.colors["faded_purple"], 
                   max_speed=12, 
                   mass=100, 
                   radius=30),
            Seeker(x_pos=90, 
                   y_pos=700, 
                   color=self.colors["muted_orange"], 
                   max_speed=12, 
                   mass=60, 
                   radius=20),
            Seeker(x_pos=30, 
                   y_pos=700, 
                   color=self.colors["yellow_cream"], 
                   max_speed=12,  
                   mass=20, 
                   radius=10),
        ]
        self.edge_spacer = 15
        self.sliders = [
            Slider(name="max_speed",
                   screen=self.screen, 
                   x_pos=self.edge_spacer,
                   sliders_index=0, 
                   init_lut_index=4, 
                   colors=self.colors),
            Slider(name="mass",
                   screen=self.screen,
                   x_pos=self.edge_spacer,
                   sliders_index=1,
                   init_lut_index=4,
                   colors=self.colors),
            Slider(name="responsiveness",
                   screen=self.screen,
                   x_pos=self.edge_spacer,
                   sliders_index=2,
                   init_lut_index=3,
                   colors=self.colors),                   
            Slider(name="max_force",
                   screen=self.screen,
                   x_pos=self.edge_spacer,
                   sliders_index=3,
                   init_lut_index=3,
                   colors=self.colors),
            Slider(name="flee_distance",
                   screen=self.screen,
                   x_pos=self.edge_spacer,
                   sliders_index=4,
                   init_lut_index=4,
                   colors=self.colors),
            Slider(name="calm_buffer",
                   screen=self.screen,
                   x_pos=self.edge_spacer,
                   sliders_index=5,
                   init_lut_index=1,
                   colors=self.colors),
        ]
        self.reset = ResetButton(
            screen=self.screen, 
            screen_rect=self.screen_rect, 
            edge_spacer=self.edge_spacer, 
            colors=self.colors,
        )
        self.mode = Mode.SEEK
        self.active_slider = None
        self.active_button = None
        self.sync_ui = False
   
    def run_game(self):
        """Hold the game loop"""

        while True:
            self._check_events()
            self.mouse_pos = pygame.mouse.get_pos()
            self.screen.fill(self.colors["night_sky"])
            self._update_seekers(self.mode)
            self._draw_seekers()
            if self.sync_ui:
                for slider in self.sliders:
                    slider.sync_ui()
                self.sync_ui = False
            for slider in self.sliders:
                new_global = slider._check_buttons(
                    self.active_slider,
                    self.mouse_pos,
                )
                if new_global is not None:
                    self._change_global(new_global)
                slider.draw_slider(self.active_slider)
                slider.draw_slider_label()
                slider.draw_slider_value(modifiers[slider.name])
                self._draw_mouse_circle(self.mode)
            self.reset.draw_reset_button(self.active_button)
            pygame.display.flip()
            self.clock.tick(60)
  
    def _check_events(self):
        """Check for keypresses and mouse clicks"""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._mouse_press()
            elif event.type == pygame.MOUSEBUTTONUP:
                self._mouse_release()

    def _mouse_press(self):
        """Allow the mouse to move the button"""

        button_press = False
        for slider in self.sliders:
            if slider.button_image.collidepoint(self.mouse_pos):
                button_press = True
                self.active_slider = slider.name
        if self.reset.button_rect.collidepoint(self.mouse_pos):
            button_press = True
            self.active_button = True
        if not button_press:
            self._change_mode()

    def _mouse_release(self):
        """Decouple slider button from mouse"""

        self.active_slider = None
        if self.active_button == True:
            self.active_button = None
            self._reset_globals()
            self.sync_ui = True

    def _change_mode(self):
        """Switch the simulation mode"""

        if self.mode == Mode.SEEK:
            self.mode = Mode.FLEE
        else:
            self.mode = Mode.SEEK

    def _change_global(self, change):
        """Change appropriate modifiers value"""

        name, lut_index = change
        modifiers[name] = SLIDER_LUTS[name][lut_index]

    def _reset_globals(self):
        """Reset modifiers values to INITIAL_MODIFIERS"""

        modifiers.clear()
        modifiers.update(INITIAL_MODIFIERS)

    def _draw_mouse_circle(self, mode):
        """Draw a circle at the cursor's current location"""

        pygame.mouse.set_visible(False)
        if mode == Mode.SEEK:
            self.mouse_circle = pygame.draw.circle(
                self.screen,
                self.colors["blue_gray"],
                self.mouse_pos,
                self.mouse_circle_radius,
            )
        else:
            self.mouse_circle = pygame.draw.circle(
                self.screen,
                self.colors["cream"],
                self.mouse_pos,
                self.mouse_circle_radius,
            )

    def _update_seekers(self, mode):
        """Apply the speed and target forces to update position.
        This is where the Reynolds steering philosophy is implemented
        On every frame, each agent must:
        1. Sense its surroundings
        2. Use gathered sense data to generate steering desires
        3. Blend those desires into one discrete step
        4. Apply that step according to the defined physics of the world
        """

        if mode == Mode.SEEK:
            for seeker in self.seekers:
                (
                    effective_max_speed,
                    effective_max_force,
                    slowing_distance,
                ) = self._recalculate_effective_values(seeker)
                xy_diff = (
                    (self.mouse_pos[0] - seeker.x_pos), 
                    (self.mouse_pos[1] - seeker.y_pos)
                )
                displacement_vector = pygame.Vector2(xy_diff)
                distance = displacement_vector.length()
                if distance >= 1:                
                    ramped_speed = (
                        effective_max_speed 
                        * (distance / slowing_distance)
                    )
                    clipped_speed = min(
                        ramped_speed, 
                        effective_max_speed
                    )
                    displacement_vector.normalize_ip()
                    desired_velocity = (
                        displacement_vector 
                        * clipped_speed
                    )
                    self._apply_steering(
                        seeker, 
                        desired_velocity, 
                        effective_max_force, 
                        effective_max_speed,
                    )
                else:
                    desired_velocity = pygame.Vector2()
                    self._apply_steering(
                        seeker, 
                        desired_velocity, 
                        effective_max_force, 
                        effective_max_speed,
                    )
        else:
            for seeker in self.seekers:
                (
                    effective_max_speed,
                    effective_max_force,
                    slowing_distance,
                ) = self._recalculate_effective_values(seeker)
                flee_distance = modifiers["flee_distance"]
                calm_distance = (
                    flee_distance 
                    * modifiers["calm_buffer"]
                )
                mouse_xy_diff = (
                    (self.mouse_pos[0] - seeker.x_pos),
                    (self.mouse_pos[1] - seeker.y_pos)
                )
                mouse_displacement_vector = pygame.Vector2(mouse_xy_diff)
                mouse_distance = mouse_displacement_vector.length()
                if seeker.state == SeekerState.RETURNING:
                    if mouse_distance <= flee_distance:
                        seeker.state = SeekerState.FLEEING
                if seeker.state == SeekerState.FLEEING:
                    if mouse_distance >= calm_distance:
                        seeker.state = SeekerState.RETURNING

                if seeker.state == SeekerState.FLEEING:
                    desired_velocity = self._determine_fleeing_target(
                        flee_distance,
                        mouse_displacement_vector,
                        seeker,
                        effective_max_speed,
                    )
                    self._apply_steering(
                        seeker, 
                        desired_velocity, 
                        effective_max_force, 
                        effective_max_speed,
                    )
                    
                elif seeker.state == SeekerState.RETURNING:
                    center_point = (400,400)
                    xy_diff = (
                        (center_point[0] - seeker.x_pos), 
                        (center_point[1] - seeker.y_pos),
                    )
                    displacement_vector = pygame.Vector2(xy_diff)
                    distance = displacement_vector.length()
                    if distance >= 1:                
                        ramped_speed = (
                            effective_max_speed 
                            * (distance / slowing_distance)
                        )
                        clipped_speed = min(
                            ramped_speed, 
                            effective_max_speed,
                        )
                        displacement_vector.normalize_ip()
                        desired_velocity = (
                            displacement_vector 
                            * clipped_speed
                        )
                        self._apply_steering(
                            seeker, 
                            desired_velocity, 
                            effective_max_force, 
                            effective_max_speed,
                        )
                    else:
                        desired_velocity = pygame.Vector2() 
                        self._apply_steering(
                            seeker, 
                            desired_velocity, 
                            effective_max_force, 
                            effective_max_speed,
                        )

    def _recalculate_effective_values(self, seeker):
        """Recalculate values that need current GLOBALs"""

        effective_max_speed = seeker.max_speed * modifiers["max_speed"]
        effective_mass = seeker.mass * modifiers["mass"]
        response_time = effective_mass / modifiers["responsiveness"]
        effective_max_force = (
            (effective_max_speed / response_time) 
            * modifiers["max_force"]
        )
        slowing_distance = (
            (effective_max_speed ** 2) 
            / (effective_max_force * 2)
        )
        return (effective_max_speed, effective_max_force, slowing_distance)

    def _determine_fleeing_target(
        self,
        flee_distance,
        mouse_displacement_vector,
        seeker,
        effective_max_speed,
    ):
        """Determine a new target point for fleeing behavior"""

        fleeing_target_distance = flee_distance * 2
        flipped_mouse_vector = mouse_displacement_vector.rotate(180)
        if flipped_mouse_vector.length() > 0:
            normalized_flipped_vector = flipped_mouse_vector.normalize()
        elif seeker.velocity.length() > 0:
            normalized_flipped_vector = seeker.velocity.normalize()
        else:
            normalized_flipped_vector = pygame.Vector2(1, 0)
        fleeing_target_point = (
            pygame.Vector2(seeker.x_pos, seeker.y_pos)
            + (normalized_flipped_vector * fleeing_target_distance)
        )
        xy_diff = (
            (fleeing_target_point[0] - seeker.x_pos), 
            (fleeing_target_point[1] - seeker.y_pos)
        )
        displacement_vector = pygame.Vector2(xy_diff)
        displacement_vector.normalize_ip()
        desired_velocity = displacement_vector * effective_max_speed
        return desired_velocity

    def _apply_steering(
            self, 
            seeker, 
            desired_velocity, 
            effective_max_force, 
            effective_max_speed
        ):
        """Use a desired_velocity and physics constraints to increment position"""

        steering_force = desired_velocity - seeker.velocity
        if abs(steering_force.length()) > effective_max_force:
            steering_force.scale_to_length(effective_max_force)
        seeker.velocity += steering_force
        if abs(seeker.velocity.length()) > effective_max_speed:
            seeker.velocity.scale_to_length(effective_max_speed)
        seeker.x_pos += seeker.velocity.x
        seeker.y_pos += seeker.velocity.y
                
    def _draw_seekers(self):
        """Draw seekers at their current location"""

        for seeker in self.seekers:
            pygame.draw.circle(
                self.screen,
                seeker.color,
                (seeker.x_pos, seeker.y_pos),
                seeker.radius,
            )

if __name__ == '__main__':
    s = SeekAndFlee()
    s.run_game()