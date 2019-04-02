#!/usr/bin/env python2

import sys, shlex

from random import random
from bisect import bisect
from ConfigParser import ConfigParser

from gomill import gtp_controller, gtp_engine, gtp_proxy

def weighted_choice(choices):
    weights, values = zip(*choices)
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    return values[bisect(cum_weights, random() * total)]

class Rand_GTP(gtp_proxy.Gtp_proxy):
    def __init__(self, weight, cmd, **kwargs):
        super(Rand_GTP, self).__init__()

        self.set_back_end_subprocess(cmd, **kwargs)
        self.engine.add_command('name', lambda args: 'Random GTP')
        self.engine.add_command('version', lambda args: '0.0')
        self.engine.add_command('genmove', self._handle_genmove)

        self._engines = [(int(weight), self.controller)]

    def add_additional_engine(self, weight, cmd, **kwargs):
        try:
            channel = gtp_controller.Subprocess_gtp_channel(cmd, **kwargs)
        except gtp_controller.GtpChannelError, e:
            raise gtp_proxy.BackEndError('can\'t launch back end command\n%s' % e, cause = e)
        name = cmd[0] if isinstance(cmd, list) else cmd
        controller = gtp_controller.Gtp_controller(channel, name)
        self._engines.append((int(weight), controller))
        # TODO: fixup supported commands

    def pass_command(self, command, args):
        for _, controller in self._engines:
            self._send_command(controller, command, args)

    def _send_command(self, controller, command, args):
        tmp = self.controller
        self.controller = controller
        value = super(Rand_GTP, self).pass_command(command, args)
        self.controller = tmp
        return value

    def _handle_genmove(self, args):
        executor = weighted_choice(self._engines)
        value = self._send_command(executor, 'genmove', args)
        if value != 'resign':
            for _, controller in self._engines:
                if controller != executor:
                    self._send_command(controller, 'play', args + [value])
        else:
            for _, controller in self._engines:
                self._send_command(controller, 'quit')
        return value

if __name__ == "__main__":
    conf = ConfigParser()
    conf.read([sys.argv[1]])
    engines = conf.sections()
    primary, secondary = engines[0], engines[1:]

    r = Rand_GTP(conf.get(primary, 'weight'), conf.get(primary, 'command'))
    for engine in secondary:
        r.add_additional_engine(conf.get(engine, 'weight'), shlex.split(conf.get(engine, 'command')))

    try:
        r.run()
    except KeyboardInterrupt:
        sys.exit(1)
