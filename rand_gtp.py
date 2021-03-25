#!/usr/bin/env python2

import sys, shlex

from collections import namedtuple, OrderedDict
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

Engine = namedtuple('Engine', 'name weight command analyze')

class Rand_GTP(gtp_proxy.Gtp_proxy):
    def __init__(self, engine):
        super(Rand_GTP, self).__init__()

        self.set_back_end_subprocess(engine.command)
        self.engine.add_command('name', lambda args: 'Random GTP')
        self.engine.add_command('version', lambda args: '0.0')
        self.engine.add_command('genmove', self._handle_genmove)
        self.engine.add_command('showboard', self._handle_showboard)
        self.engine.add_command('place_free_handicap', self._handle_place_free_handicap)

        self._engines = [(engine, self.controller)]

    def add_additional_engine(self, engine):
        try:
            channel = gtp_controller.Subprocess_gtp_channel(engine.command)
        except gtp_controller.GtpChannelError, e:
            raise gtp_proxy.BackEndError('can\'t launch back end command: %s\n%s' % (e, engine.command), cause = e)
        controller = gtp_controller.Gtp_controller(channel, engine.name)
        self._engines.append((engine, controller))

    def run(self):
        self._engines = OrderedDict([(e[0].name, e) for e in sorted(self._engines, key=lambda x: x[0].weight)])

        return super(Rand_GTP, self).run()

    def pass_command(self, command, args):
        for engine, controller in self._engines.values():
            # TODO: proper handling of commands which return data
            # (e.g. final_score etc.) and of commands not supported by all engines.
            print >>sys.stderr, engine.name, command, args
            r = self._send_command(controller, command, args)

            if r:
                return r

    def _send_command(self, controller, command, args = None):
        tmp = self.controller
        self.controller = controller
        value = super(Rand_GTP, self).pass_command(command, args or [])
        self.controller = tmp
        return value

    def _handle_genmove(self, args):
        executor = weighted_choice(((e[0].weight, e) for e in self._engines.values()))

        for engine, controller in self._engines.values():
            print >>sys.stderr, engine.name, 'showboard'
            print >>sys.stderr, self._send_command(controller, 'showboard', [])

        value = self._send_command(executor[1], 'genmove', args)
        print >>sys.stderr, 'Passing genmove to %s: %s' % (executor[0].name, value)

        for engine, controller in self._engines.values():
            if controller != executor[1] and value.lower() != 'resign':
                self._send_command(controller, 'play', args + [value])

            if engine.analyze is not None:
                analyze = self._send_command(controller, engine.analyze)
                print >>sys.stderr, 'Analysis from %s: %s' % (engine.name, analyze)

        return value

    def _handle_showboard(self, args):
        for engine, controller in self._engines.values():
            print >>sys.stderr, 'Showboard from', engine.name
            print >>sys.stderr, self._send_command(controller, 'showboard', [])

    def _handle_place_free_handicap(self, args):
        value = None
        for engine, controller in self._engines.values():
            if value is None:
                value = self._send_command(controller, 'place_free_handicap', args).split()
            else:
                self._send_command(controller, 'set_free_handicap', value)

        return ' '.join(value)

if __name__ == "__main__":
    conf = ConfigParser()
    conf.read([sys.argv[1]])
    engines = conf.sections()
    print >>sys.stderr, 'Engines:', engines

    def _make_engine(name):
        return Engine(name    = name,
                      weight  = conf.getint(name, 'weight'),
                      command = shlex.split(conf.get(name, 'command')),
                      analyze = conf.get(name, 'analyze') if conf.has_option(name, 'analyze') else None)

    r = Rand_GTP(_make_engine(engines[0]))
    for engine in engines[1:]:
        r.add_additional_engine(_make_engine(engine))

    try:
        r.run()
    except KeyboardInterrupt:
        sys.exit(1)
