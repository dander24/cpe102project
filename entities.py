import point

class Entity(object):
   def __init__(self, name, imgs):
      self.name = name
      self.imgs = imgs
      self.current_img = 0

   def get_images(self):
      return self.imgs

   def get_image(self):
      return self.imgs[self.current_img]

   def get_name(self):
      return self.name

   def next_image(self):
      self.current_img = (self.current_img + 1) % len(self.imgs)

   def self_string(self):
      return 'unknown'

class Non_static(Entity):
   def __init__(self, name, position, imgs):
      super(Non_static, self).__init__(name,imgs)
      self.position = position

   def set_position(self, point):
      self.position = point

   def get_position(self):
      return self.position

class Actor(Non_static):
   def __init__(self, name, position, imgs, rate):
      super(Actor,self).__init__(name, position, imgs)
      self.rate = rate
      self.pending_actions = []

   def remove_pending_action(self, action):
      self.pending_actions.remove(action)

   def add_pending_action(self, action):
      self.pending_actions.append(action)

   def get_pending_actions(self):
      return self.pending_actions

   def clear_pending_actions(self):
      self.pending_actions = []

   def get_rate(self):
      return self.rate

class ActorDist(Actor):
   def __init__(self, name, rate, position, imgs, resource_distance):
      super(ActorDist,self).__init__(name, position, imgs, rate)
      self.resource_distance = resource_distance

   def get_resource_distance(self):
      return self.resource_distance
      
class Miner(Actor):
   def __init__(self, name, resource_limit, position, rate, imgs, animation_rate):
      super(Miner,self).__init__(name, position, imgs, rate)
      self.resource_limit = resource_limit
      self.resource_count = 0
      self.animation_rate = animation_rate

   def set_resource_count(self, n):
      self.resource_count = n

   def get_resource_count(self):
      return self.resource_count

   def get_resource_limit(self):
      return self.resource_limit

   def get_animation_rate(self):
      return self.animation_rate
   
   
   

#########################################################################################################################


class Background(Entity):
   def __init__(self, name, imgs):
      super(Background,self).__init__(name,imgs)


class MinerNotFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs, animation_rate):
      super(MinerNotFull,self).__init__(name, resource_limit, position, rate, imgs,
      animation_rate)

   def self_string(self):
      return ' '.join(['miner', self.name, str(self.position.x),
            str(self.position.y), str(self.resource_limit),
            str(self.rate), str(self.animation_rate)])
 

class MinerFull(Miner):
   def __init__(self, name, resource_limit, position, rate, imgs, animation_rate):
      super(MinerFull,self).__init__(name, resource_limit, position, rate, imgs,
      animation_rate)

class Vein(ActorDist):
   def __init__(self, name, rate, position, imgs, resource_distance=1):
      super(Vein,self).__init__(name, rate, position, imgs, resource_distance)
      
   def self_string(self):
      return ' '.join(['vein', self.name, str(self.position.x),
         str(self.position.y), str(self.rate),
         str(self.resource_distance)])

class Ore(Actor):
   def __init__(self, name, position, imgs, rate=5000):
      super(Ore,self).__init__(name, position, imgs, rate)

   def self_string(self):
      return ' '.join(['ore', self.name, str(self.position.x),
         str(self.position.y), str(self.rate)])

class Blacksmith(ActorDist):
   def __init__(self, name, position, imgs, resource_limit, rate,
      resource_distance=1):
      super(Blacksmith,self).__init__(name, rate, position, imgs, resource_distance)
      self.resource_limit = resource_limit
      self.resource_count = 0

   def set_resource_count(self, n):
      self.resource_count = n

   def get_resource_count(self):
      return self.resource_count

   def get_resource_limit(self):
      return self.resource_limit

   def self_string(self):
      return ' '.join(['blacksmith', self.name, str(self.position.x),
         str(self.position.y), str(self.resource_limit),
         str(self.rate), str(self.resource_distance)])

class Obstacle(Non_static):
   def __init__(self, name, position, imgs):
      super(Obstacle,self).__init__(name,position,imgs)
      self.name = name
      self.position = position
      self.imgs = imgs
      self.current_img = 0

   def self_string(self):
      return ' '.join(['obstacle', self.name, str(self.position.x),
         str(self.position.y)])

class OreBlob(Actor):
   def __init__(self, name, position, rate, imgs, animation_rate):
      super(OreBlob,self).__init__(name, position, imgs, rate)
      self.animation_rate = animation_rate

   def get_animation_rate(self):
      return self.animation_rate

class Quake(Non_static):
   def __init__(self, name, position, imgs, animation_rate):
      super(Quake,self).__init__(name, position, imgs)
      self.animation_rate = animation_rate
      self.pending_actions = []

   def get_animation_rate(self):
      return self.animation_rate

   def remove_pending_action(self, action):
      self.pending_actions.remove(action)

   def add_pending_action(self, action):
      self.pending_actions.append(action)

   def get_pending_actions(self):
      return self.pending_actions

   def clear_pending_actions(self):
      self.pending_actions = []
