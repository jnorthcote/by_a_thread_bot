import time

from datetime import datetime
from log_config import *

from elasticsearch import Elasticsearch
from elasticsearch_dsl import (
    Boolean,
    Date,
    Document,
    InnerDoc,
    Integer,
    Join,
    Keyword,
    Long,
    Nested,
    Object,
    Search,
    Text,
    connections,
)
from nova.types import TierEnum, ShipClassEnum, FleetTypeEnum, FleetFocusEnum, AdmiralEnum

logger = get_logger(__name__)

# class User(InnerDoc):
#     """
#     Class used to represent a denormalized user stored on other objects.
#     """
#
#     d_id = Long(required=True)
#     username = Text(fields={"keyword": Keyword()}, required=True)

class CompTier(InnerDoc):

    # id = Integer(required=True)
    tier_name = Text(fields={"keyword": Keyword()}, required=True)

class ShipClass(InnerDoc):

    # id = Integer(required=True)
    class_name = Text(fields={"keyword": Keyword()}, required=True)

    def __str__(self):
        return f"{self.class_name}"

    def __format__(self, format_spec):
        # logger.debug("__format__ %s spec: %s" % (f"({self.alliance}){self.name}", format_spec) )
        c = self.class_name[:2]
        return f'{c:{format_spec}}'

class FleetType(InnerDoc):

    # id = Integer(required=True)
    type_name = Keyword()
    slots = Integer(required=True)

class Combatant(InnerDoc):

    name = Keyword(required=True)
    alliance = Keyword(required=True)

    def __str__(self):
        return f"({self.alliance}){self.name}"

    def __format__(self, format_spec):
        # logger.debug("__format__ %s spec: %s" % (f"({self.alliance}){self.name}", format_spec) )
        # c = f"({self.alliance}){self.name}"
        return f'{self.name:{format_spec}}'

class Admiral(InnerDoc):

    name = Keyword(required=True)

    def __str__(self):
        return f"{self.name}"

    def __format__(self, format_spec):
        # logger.debug("__format__ %s spec: %s" % (f"({self.alliance}){self.name}", format_spec) )
        c = f"{self.name}"
        return f'{c:{format_spec}}'


class NovaBase(Document):
    """
    Base class for Question and Answer containing the common fields.
    """
    author = Long(required=True)
    created = Date(required=True)
    modified = Date(required=True)
    ship_stats = Join(relations={"ship": "stats"})

    @classmethod
    def _matches(cls, hit):
        # Post is an abstract class, make sure it never gets used for
        # deserialization
        return False

    class Index:
        name = "nova_ship_data_v2"
        # name = "nova_ship_data_v1"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    def save(self, **kwargs):
        # if there is no date, use now
        if self.created is None:
            self.created = datetime.now()
        if self.modified is None:
            self.modified = datetime.now()
        return super().save(**kwargs)

class ShipType(NovaBase):

    name = Keyword(required=True)
    ship_class = Object(ShipClass)
    hull_tier = Object(CompTier)
    size = Integer()
    power = Long(required=True)
    chip = Integer()
    last_stats_id = Keyword()

    @classmethod
    def from_map(cls, author, entity_map):
        ship = cls.getOne(author, name=entity_map['name'])
        if ship is None:
            ship = ShipType(
                author = author,
                name = entity_map['name'],
                size = 0,
                power = 0,
                chip = 0
            )
        logger.debug("ShipType.from_map entity_map: %s" % (entity_map))

        if 'chip' in entity_map: #and len(entity_map['chip']) > 0:
            ship.chip = entity_map['chip']

        if 'ship_class' in entity_map:
            ship.ship_class = SearchTypes.getShipClass(entity_map['ship_class'])

        if 'power' in entity_map:
            ship.power = entity_map['power']
        if 'size' in entity_map:
            ship.size = entity_map['size']

        ship.save()
        return ship

    @classmethod
    def _matches(cls, hit):
        if 'ship_stats' not in hit["_source"]:
            # logger.debug("_matches %s" % (hit["_source"]))
            return False
        return hit["_source"]["ship_stats"] == "ship"

    @classmethod
    def getOne(cls, author, **kwargs):
        logger.debug("ShipType.getOne kwargs: %s" % (kwargs))
        ship_search = cls.search(author)
        if 'name' in kwargs:
            ship_search = ship_search.query("match", name=kwargs['name'])[0:1]
        r = ship_search.execute()
        if (ship_search.count())>0:
            for ship in ship_search:
                logger.debug("ShipType.getOne  ship: %s" % (ship.to_dict()))
                return ship
        return None

    @classmethod
    def search(cls, author, **kwargs):
        return cls._index.search(**kwargs).filter("term", ship_stats="ship").filter("term", author=author)

    def add_stats(self, author, entities, created = None, commit=True, refresh=False):
        logger.debug("ShipType.add_stats power: %s" % (self.power))
        logger.debug("ShipType.add_stats entities: %s" % (entities))
        if 'power' not in entities or len(entities['power'])==0:
            entities['power'] = self.power

        stats = Stats(
            # required make sure the answer is stored in the same shard
            _routing=self.meta.id,
            # since we don't have explicit index, ensure same index as self
            _index=self.meta.index,
            # set up the parent/child mapping
            ship_stats={"name": "stats", "parent": self.meta.id},
            author = author,
            created = created,
            version = 1,
            ship_name = self.name,
            level = entities['level'],
            power = entities['power'],
            dpr = entities['dpr'],
            hp = entities['hp'],
            shd = entities['shd'],
            armor = entities['armor'],
            acu = entities['acu'],
            evd = entities['evd'],
            stl = entities['stl'],
            ftl = entities['ftl'],
            r_kin = entities['r_kin'],
            r_beam = entities['r_beam'],
            r_mis = entities['r_mis'],
            btt = entities['btt']

        )
        if 'stats_label' in entities:
            stats.stats_label = entities['stats_label']
        if 'fleet_num' in entities:
            stats.fleet_num = entities['fleet_num']
        if 'fleet_id' in entities:
            stats.fleet_id = entities['fleet_id']

        if commit:
            v_rev = Stats.update(author).filter("term", parent=self.meta.id)
            # update_current = update_current.query("match", current=True)
            v_rev = v_rev.script(source="ctx._source.version++")
            uc = v_rev.execute()
            stats.save()
            self.last_stats_id = stats.meta_id
            self.save()
        if refresh:
            ShipType._index.refresh()
        return stats

    def search_stats(self, author):
        # search only our index
        s = Stats.search(author)
        # filter for answers belonging to us
        s = s.filter("parent_id", type="stats", id=self.meta.id)
        # add routing to only go to specific shard
        s = s.params(routing=self.meta.id)
        return s

    def get_stats(self, author, ignore_meta = False):
        """
        Get answers either from inner_hits already present or by searching
        elasticsearch.
        """
        if not ignore_meta and "inner_hits" in self.meta and "stats" in self.meta.inner_hits:
            return self.meta.inner_hits.stats.hits
        return list(self.search_stats(author).sort('-created'))

    @property
    def last_stats(self):
        # cache question in self.meta
        # any attributes set on self would be interpretted as fields
        logger.debug("last_stats %s meta %s" % (self.last_stats_id, self.meta))
        if self.last_stats_id is None:
            self.meta.last_stats = None

        elif "last_stats" not in self.meta:
            self.meta.last_stats = Stats.get(
                id=self.last_stats_id, index=self.meta.index
            )

        return self.meta.last_stats

    def save(self, **kwargs):
        self.ship_stats = "ship"
        return super().save(**kwargs)

class Stats(NovaBase):

    stats_label = Text()
    version = Integer(required=True)
    # current = Boolean(required=True)
    ship_name = Keyword(required=True)
    level = Integer(required=True)
    power = Long(required=True)
    dpr = Long(required=True)
    hp = Long(required=True)
    shd = Long(required=True)
    armor = Integer(required=True)
    acu = Long(required=True)
    evd = Long(required=True)
    stl = Integer(required=True)
    ftl = Integer(required=True)
    r_kin = Integer(required=True)
    r_beam = Integer(required=True)
    r_mis = Integer(required=True)
    btt = Integer(required=True)
    fleet_num = Integer()
    # fleet_id = Keyword()

    @classmethod
    def _matches(cls, hit):
        if 'ship_stats' not in hit["_source"]:
            # logger.debug("_matches %s" % (hit["_source"]))
            return False
        return (
            isinstance(hit["_source"]["ship_stats"], dict)
            and hit["_source"]["ship_stats"].get("name") == "stats"
        )

    @classmethod
    def search(cls, author, **kwargs):
        return cls._index.search(**kwargs).filter("term", author=author).exclude("term", ship_stats="ship")

    @classmethod
    def update(cls, author, **kwargs):
        return cls._index.updateByQuery(**kwargs).filter("term", author=author).exclude("term", ship_stats="ship")

    @property
    def ship(self):
        # cache question in self.meta
        # any attributes set on self would be interpretted as fields
        if "ship" not in self.meta:
            self.meta.ship = ShipType.get(
                id=self.ship_stats.parent, index=self.meta.index
            )
            if self.ship_name is None or len(self.ship_name)==0:
                self.ship_name = self.meta.ship.name
                self.save()
        return self.meta.ship

    @property
    def fleet(self):
        # cache question in self.meta
        # any attributes set on self would be interpretted as fields
        if "fleet" not in self.meta:
            self.meta.fleet = Fleet.get(
                id=self.fleet_id, index=self.meta.index
            )
        return self.meta.fleet

    @property
    def meta_id(self):
        return self.meta.id

    def save(self, **kwargs):
        # if there is no date, use now
        self.meta.routing = self.ship_stats.parent
        if self.version is None:
            self.version = 1
        if self.fleet_num is None:
            self.fleet_num = 0
        return super().save(**kwargs)

class NovaFleetBase(Document):
    """
    Base class for Question and Answer containing the common fields.
    """

    author = Long(required=True)
    created = Date(required=True)
    modified = Date(required=True)
    fleet_slots = Join(relations={"fleet": "fleet_slot"})

    @classmethod
    def _matches(cls, hit):
        # Post is an abstract class, make sure it never gets used for
        # deserialization
        return False

    class Index:
        name = "nova_fleet_data_v2"
        # name = "nova_fleet_data_v1"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    def save(self, **kwargs):
        # if there is no date, use now
        if self.created is None:
            self.created = datetime.now()
        if self.modified is None:
            self.modified = datetime.now()
        return super().save(**kwargs)

class Fleet(NovaFleetBase):

    type    = Object(FleetType, required=True)
    num     = Integer(required=True)
    slots   = Integer(required=True)
    name    = Keyword(required=True)
    code    = Keyword()
    focus   = Keyword()
    power   = Long(required=True)
    admiral = Object(Admiral)

    @classmethod
    def from_map(cls, author, entity_map):
        fleet = cls.getOne(author, num=entity_map['fleet_num'])
        if fleet is None:
            t_type = entity_map['fleet_type']
            # type = SearchTypes.getFleetType(entity_map['fleet_type']),
            type = FleetType(type_name=t_type.label, slots=t_type.slots)
            slots = t_type.slots
            if slots in entity_map:
                slots = int(entity_map['slots'])
            fleet = Fleet(
                author = author,
                type = type,
                num = entity_map['fleet_num'],
                slots = slots,
            )

        logger.debug("name - old: %s new: %s" % (fleet.name, entity_map['name']))

        fleet.name = entity_map['name']
        if 'code' in entity_map:
            fleet.code = entity_map['code']
        if 'power' in entity_map:
            fleet.power = entity_map['power']
        if 'admiral_code' in entity_map:
            fleet.admiral = SearchTypes.getAdmiral(entity_map['admiral_code'])
        if 'focus_code' in entity_map:
            fleet.focus = SearchTypes.getFleetFocus(entity_map['focus_code'])

        fleet.save()
        for slot_num in range(1, fleet.slots+1):
            entity_map['slot_num'] = slot_num
            entity_map['slot_label'] = "%s_s%s" % (entity_map['name'], slot_num)
            # entities['fleet_id'] = fleet.meta.id
            slot = fleet.add_slot(author, entity_map)
            logger.debug("slot: %s" % (slot))
        return fleet

    @classmethod
    def _matches(cls, hit):
        if 'fleet_slots' not in hit["_source"]:
            # logger.debug("_matches %s" % (hit["_source"]))
            return False
        return hit["_source"]["fleet_slots"] == "fleet"

    @classmethod
    def getOne(cls, author, **kwargs):
        logger.debug("Fleet.getOne kwargs: %s" % (kwargs))
        fleet_search = cls.search(author, **kwargs)
        if (fleet_search.count())>0:
            for fleet in fleet_search:
                logger.debug("Fleet.getOne  fleet: %s" % (fleet.to_dict()))
                # return Fleet.get(fleet['_id'])
                return fleet
        return None

    @classmethod
    def search(cls, author, **kwargs):
        fleet_search = cls._index.search()
        if 'num' in kwargs:
            fleet_search = fleet_search.query("match", num=kwargs['num'])
        if 'name' in kwargs:
            fleet_search = fleet_search.query("match", name=kwargs['name'])
        if 'sort' in kwargs:
            fleet_search = fleet_search.sort(kwargs['sort'])
        if 'start' in kwargs and 'show' in kwargs:
            fleet_search = fleet_search[kwargs['start']:kwargs['show']]

        # r = fleet_search.execute()
        return fleet_search.filter("term", fleet_slots="fleet").filter("term", author=author)

    def add_slot(self, author, entities, created = None, commit=True, refresh=False):
        slot = FleetSlot(
            # required make sure the answer is stored in the same shard
            _routing=self.meta.id,
            # since we don't have explicit index, ensure same index as self
            _index=self.meta.index,
            # set up the parent/child mapping
            fleet_slots={"name": "fleet_slot", "parent": self.meta.id},
            author = author,
            created = created,
            slot = entities['slot_num'],
        )
        if 'slot_label' in entities:
            slot.label = entities['slot_label']
        if 'fleet_id' in entities:
            stats.fleet_id = entities['fleet_id']

        if commit:
            slot.save()
        if refresh:
            Fleet._index.refresh()
        return slot

    def fill_slot(self, slot_num, **kwargs):
        slots = self.get_slots()
        f_slot = None
        logger.info("fill_slot: sn:%s sc:%s" % (slot_num, len(slots)))

        stats = None
        ship_name = None
        if 'stats' in kwargs:
            stats = kwargs['stats']
            ship_name = stats.ship.name

        for slot in slots:
            # stats_id = 'empty'
            # if 'stats_id' in slot:
            #     stats_id = slot['stats_id']
            # logger.info("slot: %s %s %s" % (slot['slot'], slot['label'], stats_id))

            if slot_num != None:
                if int(slot['slot']) == int(slot_num):
                    f_slot = slot
            else:
                if 'ship_name' in slot:
                    if slot.ship_name == ship_name:
                        f_slot = slot
                elif 'stats_id' not in slot:
                    f_slot = slot

            if f_slot != None:
                break

        logger.info("f_slot %s" % (f_slot))
        if f_slot == None:
            return None

        slot_inst = FleetSlot.get(f_slot.meta.id)
        if 'ship' in kwargs:
            ship = kwargs['ship']
            slot_inst.ship_name = ship.name

        if stats != None:
            slot_inst.stats_id = stats.meta_id

        slot_inst.save()
        return slot_inst

    def search_slots(self):
        # search only our index
        s = FleetSlot.search(self.author)
        # filter for answers belonging to us
        s = s.filter("parent_id", type="fleet_slot", id=self.meta.id)
        # add routing to only go to specific shard
        s = s.params(routing=self.meta.id)
        return s

    def get_slots(self, **kwargs):

        sl_search = self.search_slots().sort('slot')
        if 'clear' in kwargs and kwargs['clear'] == True:
            r = sl_search.delete()
            time.sleep(3)
            # r = sl_search_del.execute()
        
        slots = list(sl_search)
        if len(slots)==0:
            for slot_num in range(1, self.slots+1):
                entity_map = {}
                entity_map['slot_num'] = slot_num
                entity_map['slot_label'] = "%s_s%s" % (self.name, slot_num)
                # entities['fleet_id'] = fleet.meta.id
                slot = self.add_slot(self.author, entity_map)
                logger.debug("slot: %s" % (slot))
            slots = list(sl_search)

        # if not ignore_meta and "inner_hits" in self.meta and "fleet_slot" in self.meta.inner_hits:
        #     return self.meta.inner_hits.fleet_slot.hits
        return slots

    @property
    def meta_id(self):
        return self.meta.id

    def save(self, **kwargs):
        self.fleet_slots = "fleet"
        return super().save(**kwargs)

class FleetSlot(NovaFleetBase):

    slot     = Integer(required=True)
    label    = Keyword(required=True)
    ship_name= Keyword()
    stats_id = Keyword()

    @classmethod
    def search(cls, author, **kwargs):
        return cls._index.search(**kwargs).filter("term", author=author).exclude("term", fleet_slots="fleet")

    @property
    def fleet(self):
        # cache question in self.meta
        # any attributes set on self would be interpretted as fields
        if "fleet" not in self.meta:
            self.meta.fleet = Fleet.get(
                id=self.fleet_slots.parent, index=self.meta.index
            )
        return self.meta.fleet

    @property
    def meta_id(self):
        return self.meta.id

    def save(self, **kwargs):
        # if there is no date, use now
        self.meta.routing = self.fleet_slots.parent
        return super().save(**kwargs)

class BattleReport(Document):

    label      = Keyword(required=True)
    player     = Object(Combatant, required=True)
    opponent   = Object(Combatant, required=True)
    p_power    = Long(required=True)
    p_pow_dest = Long(required=True)
    p_pow_lost = Long(required=True)
    o_power    = Long(required=True)
    o_pow_dest = Long(required=True)
    o_pow_lost = Long(required=True)
    p_shp_tot  = Integer(required=True)
    p_shp_lst  = Integer(required=True)
    o_shp_tot  = Integer(required=True)
    o_shp_lst  = Integer(required=True)
    author     = Long(required=True)
    created    = Date(required=True)
    bat_fleets = Join(relations={"battle": "fleet"})

    class Index:
        name = "nova_battle_data_v1"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    @classmethod
    def from_map(cls, author, entity_map):
        report = BattleReport(
            player = Combatant(name = entity_map['player']['name'], alliance=entity_map['player']['alliance']),
            opponent = Combatant(name = entity_map['opponent']['name'], alliance=entity_map['opponent']['alliance']),
            p_power    = entity_map['p_power'],
            p_pow_dest = entity_map['p_pow_dest'],
            p_pow_lost = entity_map['p_pow_lost'],
            o_power    = entity_map['o_power'],
            o_pow_dest = entity_map['o_pow_dest'],
            o_pow_lost = entity_map['o_pow_lost'],
            p_shp_tot  = entity_map['p_shp_tot'],
            p_shp_lst  = entity_map['p_shp_lst'],
            o_shp_tot  = entity_map['o_shp_tot'],
            o_shp_lst  = entity_map['o_shp_lst'],
            author     = author
        )
        if 'label' in entity_map:
            report.label = entity_map['label']
        else:
            report.label = f'{report.opponent.name}_{datetime.now().strftime("%m_%d_%y")}_{datetime.now().strftime("%f")}'

        report.save()
        # list_key = f"{self.fields['fleet_side']}_fleet_list"
        b_fleets = []
        if 'p_fleet_list' in entity_map:
            for fleet in entity_map['p_fleet_list']:
                b_fleets.append(report.add_fleet(author, fleet))

        if 'o_fleet_list' in entity_map:
            for fleet in entity_map['o_fleet_list']:
                b_fleets.append(report.add_fleet(author, fleet))

        for b_fleet in b_fleets:
            logger.debug("b_fleet: %s-%s" % (b_fleet.side, b_fleet.num))
        return report

    @classmethod
    def _matches(cls, hit):
        return hit["_source"]["bat_fleets"] == "battle"

    @classmethod
    def search(cls, author, **kwargs):
        return cls._index.search(**kwargs).filter("term", bat_fleets="battle").filter("term", author=author)

    def add_fleet(self, author, fleet):
        b_fleet = BattleFleet(
            # required make sure the answer is stored in the same shard
            _routing=self.meta.id,
            # since we don't have explicit index, ensure same index as self
            _index=self.meta.index,
            # set up the parent/child mapping
            bat_fleets={"name": "fleet", "parent": self.meta.id},
            author    = author,
            num       = fleet['fleet_num'],
            side      = fleet['fleet_side'],
            name      = fleet['name'],
            destroyed = fleet['destroyed']
        )
        b_fleet.save()
        return b_fleet

    def search_fleets(self):
        # search only our index
        s = BattleFleet.search(self.author)
        # filter for answers belonging to us
        s = s.filter("parent_id", type="fleet", id=self.meta.id)
        # add routing to only go to specific shard
        s = s.params(routing=self.meta.id)
        return s

    def get_fleets(self, side, ignore_meta = False):

        if not ignore_meta:
            logger.debug("get_fleets side: %s meta: %s" % (side, self.meta))
            if "inner_hits" in self.meta:
                if "bat_fleets" in self.meta.inner_hits:
                    logger.debug("get_fleets side: %s hits: %s" % (side, self.meta.inner_hits.bat_fleets.hits))
                    return self.meta.inner_hits.bat_fleets.hits
        return list(self.search_fleets().filter("term", side=side).sort('num'))#.extra(explain=True)

    @property
    def meta_id(self):
        return self.meta.id

    @property
    def p_name(self):
        return self.player.name

    @property
    def o_name(self):
        return self.opponent.name

    def save(self, **kwargs):
        # if there is no date, use now
        if self.created is None:
            self.created = datetime.now()
        self.bat_fleets = 'battle'
        return super().save(**kwargs)


class BattleFleet(Document):

    side       = Keyword(required=True)
    num        = Integer(required=True)
    name       = Keyword(required=True)
    destroyed  = Long(required=True)
    bat_fleets = Join(relations={"battle": "fleet"})

    class Index:
        name = "nova_battle_data_v1"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    @classmethod
    def search(cls, author, **kwargs):
        return cls._index.search(**kwargs).filter("term", author=author).exclude("term", bat_fleets="battle")

    @property
    def meta_id(self):
        return self.meta.id

    def save(self, **kwargs):
        # if there is no date, use now
        self.meta.routing = self.bat_fleets.parent
        return super().save(**kwargs)

class AllianceMember(Document):
    author   = Long(required=True)
    created  = Date(required=True)
    modified = Date(required=True)
    guild_id = Long(required=True)
    level    = Long(required=True)
    name     = Keyword(required=True)
    power    = Long(required=True)
    label    = Keyword(required=True)
    leader   = Boolean(required=True)

    class Index:
        name = "nova_member_data_v1"
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        }

    @classmethod
    def search(cls, guild_id, **kwargs):
        return cls._index.search(**kwargs).filter("term", guild_id=guild_id)

    @classmethod
    def getOne(cls, guild_id, **kwargs):
        logger.debug("AllianceMember.getOne kwargs: %s" % (kwargs))
        m_search = cls.search(guild_id)
        if 'name' in kwargs:
            m_search = m_search.query("match", name=kwargs['name'])[0:1]
        if 'label' in kwargs:
            m_search = m_search.query("match", label=kwargs['label'])[0:1]
        r = m_search.execute()
        if (m_search.count())>0:
            for mem in m_search:
                logger.debug("AllianceMember.getOne  mem: %s" % (mem.to_dict()))
                # return Fleet.get(fleet['_id'])
                return mem
        return None

    @classmethod
    def from_map(cls, guild_id, entity_map):
        a_member = cls.getOne(guild_id, name=entity_map['name'], label=entity_map['label'])
        if a_member != None:
            a_member.level = entity_map['level']
            a_member.power = entity_map['power']
        else:
            a_member = AllianceMember(
                author = entity_map['author'].id,
                guild_id = guild_id,
                level = entity_map['level'],
                name = entity_map['name'],
                power = entity_map['power']
            )
            if 'label' in entity_map:
                a_member.label = entity_map['label']
        if 'leader' in entity_map:
            a_member.leader = entity_map['leader']

        a_member.save()
        return a_member

    def save(self, **kwargs):
        # if there is no date, use now

        if self.leader is None:
            self.leader = False
        if self.label is None:
            self.label = 'current'
        if self.created is None:
            self.created = datetime.now()
        if self.modified is None:
            self.modified = datetime.now()
        return super().save(**kwargs)

class SearchTypes():
    comp_tiers = {}
    ship_class = {}
    fleet_type = {}
    fleet_focus= {}
    ships      = {}
    admirals   = {}

    @classmethod
    def addShip(cls, name, s_class, c_tier = None, size = None, keys = []):
        sht = ShipType(
            name = name,
            ship_class = cls.ship_class[s_class],
            hull_tier = cls.comp_tiers[c_tier],
            size = size
        )

        if len(keys) == 0:
            keys.append(name)
            keys.append("%s%s" % (name, s_class))

        for k in keys:
            cls.ships[k] = sht

    @classmethod
    def getShip(cls, name):
        return cls.ships[name]

    @classmethod
    def addShipClass(cls, name):
        cls.ship_class[name] = ShipClass(class_name=name)

    @classmethod
    def getShipClass(cls, name):
        return cls.ship_class[name]

    @classmethod
    def addTier(cls, name):
        cls.comp_tiers[name] = CompTier(tier_name=name)

    @classmethod
    def addFleetType(cls, name, slots):
        cls.fleet_type[name] = FleetType(type_name=name, slots=slots)

    @classmethod
    def getFleetType(cls, name):
        return cls.fleet_type[name]

    @classmethod
    def addFleetFocus(cls, name, code):
        cls.fleet_focus[code] = name #FleetFocus(type_name=name, slots=slots)

    @classmethod
    def getFleetFocus(cls, code):
        return cls.fleet_focus[code]

    @classmethod
    def addAdmiral(cls, name, code):
        adm = Admiral(name=name, code=code)
        cls.admirals[code] = adm

    @classmethod
    def getAdmiral(cls, code):
        return cls.admirals[code]

class Elastic_Database():
    def __init__(self, index_name: str, host_name: str):
        connections.create_connection(hosts=[host_name], timeout=20)

        ShipType.init()
        Stats.init()
        Fleet.init()
        FleetSlot.init()
        BattleReport.init()
        BattleFleet.init()
        AllianceMember.init()

        for ct in TierEnum:
            SearchTypes.addTier(ct.label)

        for sc in ShipClassEnum:
            SearchTypes.addShipClass(sc.label)

        for ft in FleetTypeEnum:
            SearchTypes.addFleetType(ft.label, ft.slots)

        for ff in FleetFocusEnum:
            SearchTypes.addFleetFocus(ff.label, ff.code)

        for ad in AdmiralEnum:
            SearchTypes.addAdmiral(ad.label, ad.code)
