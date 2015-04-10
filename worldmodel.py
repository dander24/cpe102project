import entities
import pygame
import ordered_list
import occ_grid
import point
import math
import image_store
import random
import actions

BLOB_RATE_SCALE = 4
BLOB_ANIMATION_RATE_SCALE = 50
BLOB_ANIMATION_MIN = 1
BLOB_ANIMATION_MAX = 3

ORE_CORRUPT_MIN = 20000
ORE_CORRUPT_MAX = 30000

QUAKE_STEPS = 10
QUAKE_DURATION = 1100
QUAKE_ANIMATION_RATE = 100

VEIN_SPAWN_DELAY = 500
VEIN_RATE_MIN = 8000
VEIN_RATE_MAX = 17000

class WorldModel:
   def __init__(self, num_rows, num_cols, background):
      self.background = occ_grid.Grid(num_cols, num_rows, background)
      self.num_rows = num_rows
      self.num_cols = num_cols
      self.occupancy = occ_grid.Grid(num_cols, num_rows, None)
      self.entities = []
      self.action_queue = ordered_list.OrderedList()


   def within_bounds(self, pt):
      return (pt.x >= 0 and pt.x < self.num_cols and
         pt.y >= 0 and pt.y < self.num_rows)


   def is_occupied(self, pt):
      return (self.within_bounds(pt) and
         self.occupancy.get_cell(pt) != None)


   def nearest_entity(self, entity_dists):
      if len(entity_dists) > 0:
         pair = entity_dists[0]
         for other in entity_dists:
            if other[1] < pair[1]:
               pair = other
         nearest = pair[0]
      else:
         nearest = None

      return nearest


   def distance_sq(self, p1, p2):
      return (p1.x - p2.x)**2 + (p1.y - p2.y)**2


   def find_nearest(self, pt, type):
      oftype = [(e, self.distance_sq(pt, e.get_position()))
         for e in self.entities if isinstance(e, type)]

      return self.nearest_entity(oftype)


   def add_entity(self, entity):
      pt = entity.get_position()
      if self.within_bounds(pt):
         old_entity = self.occupancy.get_cell(pt)
         if old_entity != None:
            entities.clear_pending_actions(old_entity)
         self.occupancy.set_cell(pt, entity)
         self.entities.append(entity)


   def move_entity(self, entity, pt):
      tiles = []
      if self.within_bounds(pt):
         old_pt = entity.get_position()
         self.occupancy.set_cell(old_pt, None)
         tiles.append(old_pt)
         self.occupancy.set_cell(pt, entity)
         tiles.append(pt)
         entity.set_position(pt)

      return tiles


   def world_remove_entity(self, entity):
      self.world_remove_entity_at(entity.get_position())


   def world_remove_entity_at(self, pt):
      if (self.within_bounds(pt) and
         self.occupancy.get_cell(pt) != None):
         entity = self.occupancy.get_cell(pt)
         entity.set_position(point.Point(-1, -1))
         self.entities.remove(entity)
         self.occupancy.set_cell(pt, None)


   def world_schedule_action(self, action, time):
      self.action_queue.insert(action, time)


   def unschedule_action(self, action):
      self.action_queue.remove(action)


   def update_on_time(self, ticks):
      tiles = []

      next = self.action_queue.head()
      while next and next.ord < ticks:
         self.action_queue.pop()
         tiles.extend(next.item(ticks))  # invoke action function // hey, more comments than this next time, please
         next = self.action_queue.head()

      return tiles


   def get_background_image(self, pt):
      if self.within_bounds(pt):
         return self.background.get_cell(pt).get_image()


   def get_background(self, pt):
      if self.within_bounds(pt):
         return self.background.get_cell(pt)


   def set_background(self, pt, bgnd):
      if self.within_bounds(pt):
         self.background.set_cell(pt, bgnd)


   def get_tile_occupant(self, pt):
      if self.within_bounds(pt):
         return self.occupancy.get_cell(pt)


   def get_entities(self):
      return self.entities

   def next_position(self, entity_pt, dest_pt):
      horiz = actions.sign(dest_pt.x - entity_pt.x)
      new_pt = point.Point(entity_pt.x + horiz, entity_pt.y)

      if horiz == 0 or self.is_occupied(new_pt):
         vert = actions.sign(dest_pt.y - entity_pt.y)
         new_pt = point.Point(entity_pt.x, entity_pt.y + vert)

         if vert == 0 or self.is_occupied(new_pt):
            new_pt = point.Point(entity_pt.x, entity_pt.y)

      return new_pt


   def blob_next_position(self, entity_pt, dest_pt):
      horiz = actions.sign(dest_pt.x - entity_pt.x)
      new_pt = point.Point(entity_pt.x + horiz, entity_pt.y)

      if horiz == 0 or (self.is_occupied(new_pt) and
         not isinstance(self.get_tile_occupant(new_pt),
         entities.Ore)):
         vert = actions.sign(dest_pt.y - entity_pt.y)
         new_pt = point.Point(entity_pt.x, entity_pt.y + vert)

         if vert == 0 or (self.is_occupied(new_pt) and
            not isinstance(self.get_tile_occupant(new_pt),
            entities.Ore)):
            new_pt = point.Point(entity_pt.x, entity_pt.y)

      return new_pt


   def miner_to_ore(self, entity, ore):
      entity_pt = entity.get_position()
      if not ore:
         return ([entity_pt], False)
      ore_pt = ore.get_position()
      if actions.adjacent(entity_pt, ore_pt):
         entity.set_resource_count(
            1 + entity.get_resource_count())
         self.world_remove_entity(ore)
         return ([ore_pt], True)
      else:
         new_pt = self.next_position(entity_pt, ore_pt)
         return (self.move_entity(entity, new_pt), False)


   def miner_to_smith(self, entity, smith):
      entity_pt = entity.get_position()
      if not smith:
         return ([entity_pt], False)
      smith_pt = smith.get_position()
      if actions.adjacent(entity_pt, smith_pt):
         smith.set_resource_count(
            smith.get_resource_count() +
            entity.get_resource_count())
         entity.set_resource_count(0)
         return ([], True)
      else:
         new_pt = self.next_position( entity_pt, smith_pt)
         return (self.move_entity( entity, new_pt), False)


   def create_miner_not_full_action(self, entity, i_store):
      def action(current_ticks):
         entity.remove_pending_action(action)

         entity_pt = entity.get_position()
         ore = self.find_nearest( entity_pt, entities.Ore)
         (tiles, found) = self.miner_to_ore( entity, ore)

         new_entity = entity
         if found:
            new_entity = self.try_transform_miner( entity,
               self.try_transform_miner_not_full)

         self.schedule_action( new_entity,
            self.create_miner_action( new_entity, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action


   def create_miner_full_action(self, entity, i_store):
      def action(current_ticks):
         entity.remove_pending_action(action)

         entity_pt = entity.get_position()
         smith = self.find_nearest( entity_pt, entities.Blacksmith)
         (tiles, found) = self.miner_to_smith( entity, smith)

         new_entity = entity
         if found:
            new_entity = self.try_transform_miner( entity,
               self.try_transform_miner_full)

         self.schedule_action( new_entity,
            self.create_miner_action( new_entity, i_store),
            current_ticks + new_entity.get_rate())
         return tiles
      return action


   def blob_to_vein(self, entity, vein):
      entity_pt = entity.get_position()
      if not vein:
         return ([entity_pt], False)
      vein_pt = vein.get_position()
      if actions.adjacent(entity_pt, vein_pt):
         self.world_remove_entity( vein)
         return ([vein_pt], True)
      else:
         new_pt = self.blob_next_position( entity_pt, vein_pt)
         old_entity = self.get_tile_occupant( new_pt)
         if isinstance(old_entity, entities.Ore):
            self.remove_entity( old_entity)
         return (self.move_entity( entity, new_pt), False)


   def create_ore_blob_action(self, entity, i_store):
      def action(current_ticks):
         entity.remove_pending_action(action)

         entity_pt = entity.get_position()
         vein = self.find_nearest( entity_pt, entities.Vein)
         (tiles, found) = self.blob_to_vein( entity, vein)

         next_time = current_ticks + entity.get_rate()
         if found:
            quake = self.create_quake( tiles[0], current_ticks, i_store)
            self.add_entity( quake)
            next_time = current_ticks + entity.get_rate() * 2

         self.schedule_action( entity,
            self.create_ore_blob_action( entity, i_store),
            next_time)

         return tiles
      return action


   def find_open_around(self, pt, distance):
      for dy in range(-distance, distance + 1):
         for dx in range(-distance, distance + 1):
            new_pt = point.Point(pt.x + dx, pt.y + dy)

            if (self.within_bounds( new_pt) and
               (not self.is_occupied( new_pt))):
               return new_pt

      return None


   def create_vein_action(self, entity, i_store):
      def action(current_ticks):
         entity.remove_pending_action(action)

         open_pt = self.find_open_around( entity.get_position(),
            entity.get_resource_distance())
         if open_pt:
            ore = self.create_ore(
               "ore - " + entity.get_name() + " - " + str(current_ticks),
               open_pt, current_ticks, i_store)
            self.add_entity( ore)
            tiles = [open_pt]
         else:
            tiles = []

         self.schedule_action( entity,
            self.create_vein_action( entity, i_store),
            current_ticks + entity.get_rate())
         return tiles
      return action


   def try_transform_miner_full(self, entity):
      new_entity = entities.MinerNotFull(
         entity.get_name(), entity.get_resource_limit(),
         entity.get_position(), entity.get_rate(),
         entity.get_images(), entity.get_animation_rate())

      return new_entity


   def try_transform_miner_not_full(self, entity):
      if entity.resource_count < entity.resource_limit:
         return entity
      else:
         new_entity = entities.MinerFull(
            entity.get_name(), entity.get_resource_limit(),
            entity.get_position(), entity.get_rate(),
            entity.get_images(), entity.get_animation_rate())
         return new_entity


   def try_transform_miner(self, entity, transform):
      new_entity = transform(entity)
      if entity != new_entity:
         self.clear_pending_actions( entity)
         self.world_remove_entity_at( entity.get_position())
         self.add_entity( new_entity)
         self.schedule_animation( new_entity)

      return new_entity


   def create_miner_action(self, entity, image_store):
      if isinstance(entity, entities.MinerNotFull):
         return self.create_miner_not_full_action( entity, image_store)
      else:
         return self.create_miner_full_action( entity, image_store)


   def create_animation_action(self, entity, repeat_count):
      def action(current_ticks):
         entity.remove_pending_action(action)

         entity.next_image()

         if repeat_count != 1:
            self.schedule_action( entity,
               self.create_animation_action( entity, max(repeat_count - 1, 0)),
               current_ticks + entity.get_animation_rate())

         return [entity.get_position()]
      return action


   def create_entity_death_action(self, entity):
      def action(current_ticks):
         entity.remove_pending_action(action)
         pt = entity.get_position()
         self.remove_entity( entity)
         return [pt]
      return action


   def create_ore_transform_action(self, entity, i_store):
      def action(current_ticks):
         entity.remove_pending_action(action)
         blob = self.create_blob( entity.get_name() + " -- blob",
            entity.get_position(),
            entity.get_rate() // BLOB_RATE_SCALE,
            current_ticks, i_store)

         self.world_remove_entity( entity)
         self.add_entity( blob)

         return [blob.get_position()]
      return action


   def remove_entity(self, entity):
      for action in entity.get_pending_actions():
         self.unschedule_action( action)
      entity.clear_pending_actions()
      self.world_remove_entity( entity)


   def create_blob(self, name, pt, rate, ticks, i_store):
      blob = entities.OreBlob(name, pt, rate,
         image_store.get_images(i_store, 'blob'),
         random.randint(BLOB_ANIMATION_MIN, BLOB_ANIMATION_MAX)
         * BLOB_ANIMATION_RATE_SCALE)
      self.schedule_blob( blob, ticks, i_store)
      return blob


   def schedule_blob(self, blob, ticks, i_store):
      self.schedule_action( blob, self.create_ore_blob_action( blob, i_store),
         ticks + blob.get_rate())
      self.schedule_animation( blob)


   def schedule_miner(self, miner, ticks, i_store):
      self.schedule_action( miner, self.create_miner_action( miner, i_store),
         ticks + miner.get_rate())
      self.schedule_animation( miner)


   def create_ore(self, name, pt, ticks, i_store):
      ore = entities.Ore(name, pt, image_store.get_images(i_store, 'ore'),
         random.randint(ORE_CORRUPT_MIN, ORE_CORRUPT_MAX))
      self.schedule_ore( ore, ticks, i_store)

      return ore


   def schedule_ore(self, ore, ticks, i_store):
      self.schedule_action( ore,
         self.create_ore_transform_action( ore, i_store),
         ticks + ore.get_rate())


   def create_quake(self, pt, ticks, i_store):
      quake = entities.Quake("quake", pt,
         image_store.get_images(i_store, 'quake'), QUAKE_ANIMATION_RATE)
      self.schedule_quake( quake, ticks)
      return quake


   def schedule_quake(self, quake, ticks):
      self.schedule_animation( quake, QUAKE_STEPS) 
      self.schedule_action( quake, self.create_entity_death_action( quake),
         ticks + QUAKE_DURATION)


   def create_vein(self, name, pt, ticks, i_store):
      vein = entities.Vein("vein" + name,
         random.randint(VEIN_RATE_MIN, VEIN_RATE_MAX),
         pt, image_store.get_images(i_store, 'vein'))
      return vein


   def schedule_vein(self, vein, ticks, i_store):
      self.schedule_action( vein, self.create_vein_action( vein, i_store),
         ticks + vein.get_rate())


   def schedule_action(self, entity, action, time):
      entity.add_pending_action(action)
      self.world_schedule_action(action, time)


   def schedule_animation(self, entity, repeat_count=0):
      self.schedule_action( entity,
         self.create_animation_action( entity, repeat_count),
         entity.get_animation_rate())


   def clear_pending_actions(self, entity):
      for action in entity.get_pending_actions():
         self.unschedule_action( action)
      entity.clear_pending_actions()
