import base64
import json
import os
import time
import traceback

from copy import deepcopy
from datetime import datetime
from discord import Intents, Game, Status, Emoji, Embed
from discord.ext import commands
from enum import Enum
from nova.entity import EmbedField
from log_config import *

logger = get_logger(__name__)

ENTITY_FIELDS = {
    'ship':{
        'labels':[
            {'name':'name', 'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}', 'agg_label':True},
            {'name':'ship_class', 'width':2, 'label':'c'},
        ],
        'main':[
            # {'name':'level', 'width':2, 'label':'lv'},
            {'name':'size',  'width':4, 'label':'size'},
            {'name':'power', 'width':5, 'divk':True, 'fmt':'{:4.0f}', 'label':'pwr', 'aggs':['avg','sum']},
            {'name':'chip',  'width':4, 'label':'chip'},
        ],
        'diag':[
            {'name':'last_stats_id', 'width':32, 'lbl_fmt':'{:32}', 'fmt':'{:32.32}'},
        ],
    },
    'slot':{
        'main':[
            {'name':'slot',  'width':2, 'label':'sl'},
            {'name':'label', 'width':20, 'lbl_fmt':'{:20}', 'fmt':'{:20.20}'},
            {'name':'ship_name', 'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}'},
            {'name':'stats_id', 'width':20, 'lbl_fmt':'{:20}', 'fmt':'{:20.20}'},
        ],
    },
    'stats':{
        'ship_labels':[
            {'name':'ship_name', 'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}', 'agg_label':True},
        ],
        'labels':[
            {'type':'_hl', 'width':1, 'label':'-'},
            {'name':'stats_label', 'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}'}
        ],
        'in_fleet':[
            {'name':'slot',  'width':1, 'label':'s'},
        ],
        'out_fleet':[
            {'name':'fleet_num', 'width':2, 'label':'f'},
        ],
        'version':[
            {'name':'version', 'width':2, 'label':'v'},
        ],
        'main':[
            {'name':'level', 'width':2, 'label':'lv'},
            {'name':'btt',   'width':2, 'label':'bt'},
            {'name':'power', 'width':5, 'divk':True, 'divm':True, 'fmt':'{:4.0f}|{:3.2f}', 'label':'pwr', 'aggs':['avg','sum']},
            {'name':'dpr',   'width':6, 'divk':True, 'fmt':'{:5.2f}', 'aggs':['avg']},
            {'name':'hp',    'width':4, 'divk':True, 'fmt':'{:3.0f}', 'aggs':['avg']},
            {'name':'shd',   'width':5, 'divk':True, 'divm':True, 'fmt':'{:4.0f}|{:3.2f}', 'aggs':['avg']},
            {'name':'armor', 'width':5, 'divk':True, 'fmt':'{:4.2f}', 'label':'arm', 'aggs':['avg']},
            {'name':'acu',   'width':6, 'divk':True, 'fmt':'{:5.2f}', 'aggs':['avg']},
            {'name':'evd',   'width':5, 'divk':True, 'fmt':'{:4.2f}', 'label':'evade', 'aggs':['avg']}
        ],
        'res':[
            {'name':'r_kin',  'width':4, 'label':'kin', 'aggs':['avg']},
            {'name':'r_beam', 'width':4, 'label':'beam', 'aggs':['avg']},
            {'name':'r_mis',  'width':4, 'label':'mis', 'aggs':['avg']}
        ],
        'ext':[
            {'name':'ftl', 'width':3},
            {'name':'stl', 'width':4}
        ]
    },
    'fleet':{
        'all':[
            {'name':'num', 'width':3},
            {'name':'name', 'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}'},
            {'name':'power', 'width':9, 'divm':True, 'fmt':'{:5.3f}|{:8.5f}', 'label':'power'},
            # {'name':'power', 'width':8, 'label':'pwr'},
            {'name':'admiral', 'width':18, 'lbl_fmt':'{:18}', 'fmt':'{:18.18}'},
            {'name':'focus', 'width':8, 'lbl_fmt':'{:8}', 'fmt':'{:8.8}'},
        ]
    },
    'member':{
        'labels':[
            {'type':'_counter', 'width':3, 'label':'num'},
            {'name':'leader', 'type':'_leader', 'width':1, 'label':'-'},
            {'name':'label', 'width':20, 'lbl_fmt':'{:20}', 'fmt':'{:20.20}'}
        ],
        'main':[
            {'name':'level', 'width':2, 'label':'lv'},
            {'name':'name', 'width':15, 'lbl_fmt':'{:15}', 'fmt':'{:15.15}'},
            {'name':'power', 'width':8}
        ]
    },
    'br':{
        'label':[
            {'name':'label',      'width':20, 'lbl_fmt':'{:20}', 'fmt':'{:20.20}'},
        ],
        'list':[
            {'name':'created',    'width':19, 'type':'_date', 'fmt':'%d-%m-%Y %H:%M:%S', 'lbl_fmt':'{:19}'},
            {'name':'player',     'width':20, 'lbl_fmt':'{:20}', 'fmt':'{:20.20}'},
            {'name':'opponent',   'width':20, 'lbl_fmt':'{:20}', 'fmt':'{:20.20}'},
        ],
        'player':[
            {'name':'player',     'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}'},
            # {'name':'p_name',     'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}'},
            {'name':'p_power',    'width':6, 'divm':True, 'fmt':'|{:5.1f}', 'label':'power', 'aggs':['avg']},
            {'name':'p_pow_lost', 'width':5, 'divm':True, 'fmt':'|{:4.1f}', 'label':'lost', 'aggs':['avg']},
            {'name':'p_shp_lst',  'width':5, 'label':'ships', 'aggs':['avg']},
            {'name':'p_pow_dest', 'width':5, 'divm':True, 'fmt':'|{:4.1f}', 'label':'dstry', 'aggs':['avg']},
            # {'name':'p_shp_tot',  'width':3, 'label':'shp'},
        ],
        'opponent':[
            {'name':'opponent',   'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}'},
            # {'name':'o_name',     'width':12, 'lbl_fmt':'{:12}', 'fmt':'{:12.12}'},
            {'name':'o_power',    'width':6, 'divm':True, 'fmt':'|{:5.1f}', 'label':'power', 'aggs':['avg']},
            {'name':'o_pow_lost', 'width':5, 'divm':True, 'fmt':'|{:4.1f}', 'label':'lost', 'aggs':['avg']},
            {'name':'o_shp_lst',  'width':5, 'label':'ships', 'aggs':['avg']},
            {'name':'o_pow_dest', 'width':5, 'divm':True, 'fmt':'|{:4.1f}', 'label':'dstry', 'aggs':['avg']},
            # {'name':'o_shp_tot',  'width':3, 'label':'shp'},
        ],
        'fleet':[
            {'name':'num',       'width':1, 'label':'n'},
            {'name':'name',      'width':18, 'lbl_fmt':'{:18}', 'fmt':'{:18.18}'},
            {'name':'destroyed', 'width':16, 'divk':True, 'divm':True, 'fmt':'{:>15.0f}|{:>15.2f}'},
        ]
    }
}
TICK_TABLES_2 = [
    {'name':'stats_list_main', 'field_groups':[
        {'from':'stats', 'group':'labels'},
        {'from':'stats', 'group':'main'},
        {'from':'stats', 'group':'res'},
    ]},
    {'name':'fleet_list_main', 'field_groups':[
        {'from':'fleet', 'group':'all'},
    ]},
    {'name':'member_list_main', 'field_groups':[
        {'from':'member', 'group':'labels'},
        {'from':'member', 'group':'main'},
    ]},
    {'name':'fleet_ships_default', 'field_groups':[
        # {'from':'stats', 'group':'ship_labels', 'entity':'ship'},
        {'from':'ship', 'group':'labels'},
        {'from':'ship', 'group':'main'},
        {'from':'stats', 'group':'in_fleet'},
        {'from':'stats', 'group':'main'},
        {'from':'stats', 'group':'res'},
        {'from':'stats', 'group':'ext'},
    ]},
    {'name':'fleet_ships_slots', 'field_groups':[
        {'from':'ship', 'group':'labels'},
        {'from':'ship', 'group':'main'},
        {'from':'slot', 'group':'main'},
    ]},
    {'name':'fleet_ships_v2', 'field_groups':[
        {'from':'ship', 'group':'labels'},
        {'from':'ship', 'group':'main'},
    ]},
    {'name':'all_ships_main', 'field_groups':[
        {'from':'ship', 'group':'labels'},
        {'from':'stats', 'group':'ship_labels'},
        {'from':'stats', 'group':'out_fleet'},
        {'from':'stats', 'group':'version'},
        {'from':'stats', 'group':'main'},
        {'from':'stats', 'group':'res'},
    ]},
    {'name':'ships_diag', 'field_groups':[
        {'from':'ship', 'group':'labels'},
        {'from':'ship', 'group':'main'},
        {'from':'ship', 'group':'diag'},
    ]},
    {'name':'br_list_default', 'field_groups':[
        {'from':'br', 'group':'label'},
        {'from':'br', 'group':'list'},
    ]},
    {'name':'br_list_detail', 'field_groups':[
        {'from':'br', 'group':'label'},
        {'from':'br', 'group':'player'},
        {'from':'br', 'group':'opponent'},
    ]},
    {'name':'br_combatants', 'field_groups':[
        {'from':'br', 'group':'player'},
        {'from':'br', 'group':'opponent'},
    ]},
    {'name':'br_fleets', 'field_groups':[
        {'from':'br', 'group':'fleet', 'entity':'player'},
        {'from':'br', 'group':'fleet', 'entity':'opponent'},
    ]}

]

class Named():
    def __init__(self, name):
        self.name = name

class RunTable():
    def __init__(self, name = None, header = None, spacer = None, fields = [], aggs = {}):
        self.name   = name
        self.header = header
        self.spacer = spacer
        self.fields = fields
        self.aggs = aggs

    def __repr__(self):
        s = []
        s.append("<RunTable name:%s>" % self.name)
        s.append("%s:" % self.name.upper())
        s.append("%s" % self.header)
        for field in self.fields:
            s.append("\t[%s]" % field)

        return '\n'.join(s)

    def __str__(self):
        s = []
        s.append("<RunTable name:%s>" % self.name)
        s.append("%s:" % self.name.upper())
        s.append("%s" % self.header)
        for field in self.fields:
            s.append("\t[%s]" % field)
        # for k_agg, agg in self.aggs:
        #     s.append("agg[%s] agg:%" % (k_agg, agg))
        s.append("aggs:%s" % (self.aggs))

        return '\n'.join(s)

class RunField():
    def __init__(self, name = None, type = None, from_ent = None, label = None, lbl_fmt = None, fmt = None, agg_fmt = None, agg_label = False, divk = False, divm = False):
        self.name = name
        self.type = type
        self.from_ent = from_ent
        self.label = label
        self.lbl_fmt = lbl_fmt
        self.fmt = fmt
        self.agg_fmt = agg_fmt
        self.agg_label = agg_label
        self.divk = divk
        self.divm = divm
        self.attr = None

        # self.divisor = divisor
    def __repr__(self):
        # return "name:%s type:%s from_ent:%s label:%s lbl_fmt:%s fmt:%s agg_fmt:%s agg_label:%s divk:%s" % (self.name, self.type, self.from_ent, self.label, self.lbl_fmt, self.fmt, self.agg_fmt, self.agg_label, self.divk)
        return "name:%s fmt:%s " % (self.name, self.fmt)

    def __str__(self):
        # return "name:%s type:%s from_ent:%s label:%s lbl_fmt:%s fmt:%s agg_fmt:%s agg_label:%s divk:%s" % (self.name, self.type, self.from_ent, self.label, self.lbl_fmt, self.fmt, self.agg_fmt, self.agg_label, self.divk)
        return "name:%s fmt:%s " % (self.name, self.fmt)

class TickTable():
    def __init__(self, table_defs):
        self.table_defs = table_defs
        self.tables = {}

        self.setup()

    def setup(self):

        for tdef in self.table_defs:
            self.setup_table(tdef)

    def setup_table(self, table_def):
        table_name = table_def['name']
        field_groups = table_def['field_groups']
        # logger.debug("tbl[%s]: field_groups:%s" % (table_name, field_groups))
        h_cols = []
        spc_cols = []
        table_fields = []
        aggs = {'sum':{}, 'avg':{}}
        for field_group in field_groups:
            fg_from = field_group['from']
            fg_fields = ENTITY_FIELDS[field_group['from']][field_group['group']]
            # logger.debug("fg[%s]:\nfg_fields:%s" % (field_group, fg_fields))
            from_ent = fg_from
            if 'entity' in field_group:
                from_ent = field_group['entity']
            for fn in fg_fields:
                type = ''
                if 'type' in fn:
                    type = fn['type']
                    name = fn['type']

                if 'name' in fn:
                    name = fn['name']
                    label = fn['name']
                if 'label' in fn:
                    label = fn['label']

                if 'lbl_fmt' in fn:
                    lbl_fmt = fn['lbl_fmt']
                else:
                    lbl_fmt = "{:>%s}" % fn['width']
                    fn['lbl_fmt'] = lbl_fmt

                if 'fmt' in fn:
                    fmt = fn['fmt']
                    agg_fmt = fn['fmt']
                else:
                    fmt = "{:>%s}" % fn['width']
                    agg_fmt = "{:%s.0f}" % fn['width']

                agg_label = False
                if 'agg_label' in fn:
                    agg_label = fn['agg_label']

                divk = False
                if 'divk' in fn and fn['divk'] == True:
                    divk = True

                divm = False
                if 'divm' in fn and fn['divm'] == True:
                    divm = True

                spc_fmt = "{:->%s}" % (fn['width'])

                h_cols.append(lbl_fmt.format(label))
                spc_cols.append(spc_fmt.format('-'))
                # logger.debug("spc c: %s" % (spc_cols))
                # h_cols.append("%s" % (label.rjust(fn['width'])))
                if 'aggs' in fn:
                    for agg in fn['aggs']:
                        aggs[agg][fn['name']] = {'lbl_fmt':lbl_fmt, 'fmt':agg_fmt, 'vals':[]}

                r_field = RunField(name, type, from_ent, label, lbl_fmt, fmt, agg_fmt, agg_label, divk, divm)
                table_fields.append(r_field)

        r_table = RunTable(table_name, ' '.join(h_cols), ' '.join(spc_cols), table_fields, aggs)
        # r_table.aggs = {'sum':{}, 'avg':{}}
        # r_table.header = ' '.join(h_cols)
        # r_table.spacer = ' '.join(spc_cols)
        # r_table.aggs   = aggs
        self.tables[table_name] = r_table
        # logger.debug("tbl[%s]: %s" % (table_name, r_table))

    def format(self, name = 'empty', title = 'Name me', table_data = [], hl_id = None, msg_flags = {}, no_ticks = False):
        # logger.debug("format - %s" % (self.tables))
        run_table = self.tables[name]
        desc = []
        if title != None:
            desc.append(title)
        if not no_ticks:
            desc.append("```")
        desc.append(run_table.header)
        desc.append(run_table.spacer)
        aggs = {}
        show_avg = False
        show_sum = False

        if 'show_sum' in msg_flags and msg_flags['show_sum'] == True:
            show_sum = True
            aggs['sum'] = deepcopy(run_table.aggs['sum'])
            # logger.debug("show sum - %s" % (run_table.aggs['sum']))
        if 'show_avg' in msg_flags and msg_flags['show_avg'] == True:
            show_avg = True
            aggs['avg'] = deepcopy(run_table.aggs['avg'])
            # logger.debug("show avg - %s" % (run_table.aggs['avg']))
        counter = 0
        for data_row in table_data:
            counter += 1
            is_dict = isinstance(data_row, dict)
            # is_attr = None
            # f_entity = data_row
            all_fields = run_table.fields
            cols = []
            for fn in all_fields:
                # logger.debug("fmt[%s] from_ent: %s" % (fn.name, fn.from_ent))
                # if isinstance(data_row, dict) and fn.from_ent in data_row:
                if is_dict:
                    if fn.from_ent in data_row:
                        f_entity = data_row[fn.from_ent]
                else:
                    # logger.debug("fn[%s] attr: %s" % (fn.name, fn.attr))
                    if fn.attr is None:
                        fn.attr = True
                        attr_test = getattr(data_row, fn.from_ent, [None,False])
                        if attr_test == [None,False]:
                            fn.attr = False

                    if fn.attr == True:
                        f_entity = getattr(data_row, fn.from_ent)
                    else:
                        f_entity = data_row

                # logger.debug("fn[%s] f_entity: %s" % (fn.name, f_entity))
                if f_entity == None:
                    f_entity = {}

                val = '-'
                if fn.name in f_entity:
                    val = f_entity[fn.name]

                if fn.type == '_hl':
                    val = ' '
                    if hl_id != None and f_entity.meta_id == hl_id:
                        val = '>'

                if fn.type == '_leader':
                    val = ' '
                    if val == 1:
                        val = '>'

                if fn.type == '_counter':
                    val = counter

                fmt = fn.fmt
                units = ''
                # logger.debug("fmt[%s] from_ent: %s val: %s" % (fn.name, fn.from_ent, val))
                if val == '-':
                    fmt = fn.lbl_fmt
                else:
                    if fn.divm == True and int(val) > 999999:
                        val = (val / 1000000) #fn.divisor
                        units = 'M'
                        fmt = fn.fmt.split('|')[1]
                    elif fn.divk == True and int(val) > 999:
                        val = (val / 1000) #fn.divisor
                        units = 'K'
                        fmt = fn.fmt.split('|')[0]
                val_fmt = None
                try:
                    if fn.type == '_date':
                        if isinstance(val, datetime):
                            val_fmt = val.strftime(fmt)
                        else:
                            val_fmt = time.strptime(val, fmt)

                    if val_fmt is None:
                        if isinstance(val, list):
                            val = ''.join(val)
                        val_fmt = f"{fmt.format(val)}{units}"
                except Exception as err:
                    logger.warning(f"Exception {err=}, {type(err)=}")
                    # logger.warn(traceback.format_exc())
                    logger.warning(f"{fmt} {val} {units}")
                    val_fmt = '#'

                # logger.debug("fmt: %s val_fmt %s" % (fn.fmt, val_fmt))
                cols.append(val_fmt)

                if show_avg or show_sum:
                    for agg in aggs:
                        if fn.name in aggs[agg]:
                            # logger.debug("agg: %s name %s" % (agg, fn.name))
                            aggs[agg][fn.name]['vals'].append(val)

            desc.append(' '.join(cols))

            # desc.append("l:%s p:%s dpr:%s hp:%s" % (stat_hit.level, stat_hit.power, stat_hit.dpr, stat_hit.hp))
        if show_avg or show_sum:
            for agg, agg_fields in aggs.items():
                if len(agg_fields)>0:
                    desc.append(run_table.spacer)
                    cols = []
                    for fn in run_table.fields:
                        val = None
                        fmt = None
                        units = None
                        if fn.agg_label:
                            val = agg
                            fmt = fn.lbl_fmt

                        if fn.name in agg_fields:
                            agg_fmt_val = agg_fields[fn.name]
                            fmt = agg_fmt_val['fmt']
                            if agg == 'sum':
                                val = sum(agg_fmt_val['vals'])
                                # val = sum(agg_fmt_val['vals'])
                                # if val >= 1000 and fn.divk == False:
                                #     val = val / 1000
                                #     fmt = "{:3.2f}K" #% fn['width']
                            if agg == 'avg':
                                num = len(agg_fmt_val['vals'])
                                if num > 0:
                                    val = sum(agg_fmt_val['vals'])/num

                        if val == None:
                            fmt = fn.lbl_fmt
                            val = '-'
                        else:
                            if fn.divm == True and int(val) > 999999:
                                val = (val / 1000000) #fn.divisor
                                units = 'M'
                                fmt = fn.fmt.split('|')[1]
                            elif fn.divk == True and int(val) > 999:
                                val = (val / 1000) #fn.divisor
                                units = 'K'
                                fmt = fn.fmt.split('|')[0]

                        if len(fmt.split('|'))>1:
                            fmt = fn.fmt.split('|')[0]

                        logger.debug("fmt: %s val %s" % (fmt, val))
                        val_fmt = fmt.format(val)
                        cols.append(val_fmt)

                    desc.append(' '.join(cols))
        if not no_ticks:
            desc.append("```")

        nl_desc = '\n'.join(desc)

        return nl_desc

TT = TickTable(TICK_TABLES_2)




def to_embed(title = 'Title', description = '', type = 'rich', color = 0x000000, fields = {}):

    em = Embed.from_dict({
        'title': title,
        'description': description,
        'type':  type,
        'color': color
    })

    for name, value in fields.items():
        logger.debug("Em Field name: %s value: %s" % (name, value))
        if isinstance(value, str):
            value = EmbedField(value)

        value.as_embed_field(em, name)
        # try: 
        # except AttributeError: 
        #     return False

    return em
