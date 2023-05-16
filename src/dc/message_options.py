from log_config import *

logger = get_logger(__name__)

class MessageField():
    def __init__(self, name, value, type):
        self.name = name
        self.value = value
        self.type = type

    def __repr__(self):
        return self.value

class MessageOptions():
    def __init__(self, message):

        self.flags  = {'dump':False, 'diag':False, 'show_avg':False, 'show_sum':False, 'show':5, 'start':0, 'sort':None, 'q':None, 'csv':False, 'clear':False, 'detail':False, 'diff':None, 'view':'default'}
        self.fields = {}
        self.content = message.content

        self.fields['author'] = message.author
        self.parse_content()
        logger.info("flags: %s" % (self.flags))
        logger.info("fields: %s" % (self.fields))

    def parse_content(self):
        if len(self.content)==0:
            return
        for flag_field in self.content.split(' '):
            logger.debug("flag_field: %s" % (flag_field))

            if flag_field.startswith('+'):
                field = flag_field[1:].split('=')
                logger.debug("field: %s" % (field))
                self.fields[field[0]] = field[1]
                # self.fields[field[0]] = MessageField(field[0], field[1], '+')
                continue
            if flag_field.startswith('-'):
                flag = flag_field[1:].split('=')
                logger.debug("flag: %s" % (flag))
                if flag[0] in self.flags:
                    if len(flag)>1:
                        if flag[0] == 'q':
                            self.flags['q'] = flag[1]
                            s_s = flag[1].split(':')
                            self.flags['start'] = int(s_s[0])
                            self.flags['show'] = int(s_s[1])
                        else:
                            self.flags[flag[0]] = flag[1]
                    else:
                        self.flags[flag[0]] = True
                continue
            else:
                field = flag_field.split('=')
                logger.debug("field: %s" % (field))
                if len(field)>1:
                    self.fields[field[0]] = field[1]
                    # self.fields[field[0]] = MessageField(field[0], field[1], 'q')
                continue

