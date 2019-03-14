from kivy.app import App
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from helpers.starfield import Starfield
from helpers.game_object import GameObject
from kivy.clock import Clock 
from time import time


FPS = 90

class Player(GameObject):
    turn_friction = .3
    last_shot = None
    fire_rate = 2
    health = 100 
    controls = {
       'thrust': 'w',
       'turn_right': 0,
       'turn_left': 0,
       'attack': 0, 
    } 
    def __init__(self, game_obj, controls=None):
        GameObject.__init__(self, source=game_obj.image_map['player'])
        self.image_map = game_obj.image_map
        self.game_obj = game_obj
        if controls: self.controls.update(controls)

    def update_controls(self, controls):
        self.controls = dict(self.controls)
        self.controls.update(controls) 

    def update(self, delta, relative_obj):
        GameObject.update(self, delta, relative_obj)
        if self.controls['thrust'] == 1: self.push_forward()
        if self.controls['turn_right'] == 1: self.turn_right()
        if self.controls['turn_left'] == 1: self.turn_left()
        if self.controls['attack'] == 1: self.shoot() 

    def shoot(self):
        if self.last_shot is None or time() - self.last_shot > (1.0/self.fire_rate):
           bullet = Bullet(
            loc=self.loc,vel=self.vel,
            angle=self.angle,
            source=self.image_map['bullet'],
            shooter=self,
            game_obj=self.game_obj
           )
           self.game_obj.add_obj(bullet)
           self.last_shot = time()

    def on_hit(self, obj):
        if isinstance(obj, Bullet) and obj.shooter == self: return
        if isinstance(obj, Bullet):
            self.game_obj.remove_obj(obj)
            self.health -= obj.damage
            if self.health <= 0:
                self.health = 100
                self.loc.x = 0
                self.loc.y = 0
                self.vel.x = 0
                self.vel.y = 0
    def get_data(self):
        d = GameObject.get_data(self)
        d['health'] = self.health
        return d

    def set_data(self, data):
        GameObject.set_data(self, data)
        if 'health' in data:
            self.health = data['health'] 

class Planet(GameObject):
    def __init__(self, game_obj, source):
        GameObject.__init__(self, source=source)
        self.game_obj = game_obj

class Bullet(GameObject):
    max_vel = 500
    created_at = time()
    def __init__(self, shooter, game_obj, range=500, damage=20, *args, **kwargs):
        GameObject.__init__(self, *args, **kwargs)
        self.range = range
        self.damage = damage
        self.shooter = shooter
        self.game_obj = game_obj
        self.push_forward(self.max_vel)
        self.start_loc = self.loc 

    def update(self, delta, relative_obj):
        GameObject.update(self, delta, relative_obj)
        if self.loc.sub(self.start_loc).magnitude() > self.range:
            self.game_obj.remove_obj(self)

    def get_data(self):
        d = GameObject.get_data(self)
        d['shooter_id'] = self.shooter.id
        return d 
        
class SpaceGame(App):
    def close_keyboard(self):
        self._keyboard.unbind(
            on_key_down = self.key_down,
            on_key_up = self.key_up
            ) 

    def key_down(self, keyboard, keycode, text, modifiers):
            key = keycode[1]
            print 'down', key
            if key in self.keymap:
                self.controls[self.keymap[key]] = 1
                self.player.update_controls(self.controls)

    def key_up(self, keyboard, keycode):
            key = keycode[1]
            print 'up', key
            if key in self.keymap:
                self.controls[self.keymap[key]] = 0
                self.player.update_controls(self.controls)

    def update_game(self, delta_time):
        for obj in self.objects.values():
            obj.update(delta_time, self.player)
            for other_obj in self.objects.values():
                if other_obj == obj: continue
                obj.test_collision(other_obj) 
        self.starfield.scroll(self.player.loc.x, self.player.loc.y, 0)
        self.health.value = self.player.health
        
    def add_obj(self, obj, index=0):
        self.objects[obj.id] = obj
        self.hud.add_widget(obj.image, index=index)

    def remove_obj(self, obj):
        if obj.id in self.objects:
            del self.objects[obj.id]
            self.hud.remove_widget(obj.image) 

    def build(self):
        self.keyboard = Window.request_keyboard(self.close_keyboard, self)
        self.keyboard.bind(on_key_down = self.key_down)
        self.keyboard.bind(on_key_up = self.key_up)
        self.image_map = {
            'player': 'images/player.png',
            'planet': 'images/planet.png',
            'bullet': 'images/Buggy.png', 
        }
        self.keymap = {
            'w': 'thrust',
            'a': 'turn_left',
            'd': 'turn_right',
            'spacebar': 'attack', 
        }
        self.controls = {} 
        self.layout = FloatLayout()
        self.starfield = Starfield()
        self.layout.add_widget(self.starfield) 
        self.hud = FloatLayout(size_hint=(1,1))
        self.layout.add_widget(self.hud) 
        health_label = Label(
            text='Health',
            pos_hint={
                'top':1.4,
                'center_x':0.5
            }
        )
        self.hud.add_widget(health_label)
        self.health = ProgressBar(
           pos_hint={
                'top': 1,
               'center_x': 0.5
            },
            size_hint=(0.5, 0.1),
            max = 100,
            value = 50
        ) 

        self.hud.add_widget(self.health)
        self.objects = {}
        planet = self.add_obj(Planet(game_obj=self,source=self.image_map['planet'])) 
        self.player = Player(self)
        self.add_obj(self.player) 
        Clock.schedule_interval(self.update_game, 1.0 / FPS) 
        return self.layout
 


if __name__ == '__main__':
    SpaceGame().run() 
