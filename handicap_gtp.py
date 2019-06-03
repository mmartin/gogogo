#!/usr/bin/env python2

import sys

from gomill import gtp_proxy, gtp_engine, handicap_layout, common

if __name__ == "__main__":
    proxy = gtp_proxy.Gtp_proxy()
    proxy.set_back_end_subprocess(sys.argv[1:])

    boardsize = None

    def handle_name(args):
        name = proxy.pass_command('name', args)
        return name + ' (with handicap support)'

    def handle_boardsize(args):
        global boardsize
        boardsize = gtp_engine.interpret_int(args[0])
        return proxy.pass_command('boardsize', args)

    def _check_boardsize(f):
        def _wrap(args):
            if boardsize is None:
                raise gtp_engine.GtpError('unknown board size')
            return f(args)
        return _wrap

    def _parse_handicap(f):
        def _wrap(args):
            try:
                return f(gtp_engine.interpret_int(args[0]))
            except IndexError:
                gtp_engine.report_bad_arguments()
        return _wrap

    @_check_boardsize
    @_parse_handicap
    def handle_fixed_handicap(handicap):
        try:
            stones = [common.format_vertex(move) for
                        move in handicap_layout.handicap_points(handicap, boardsize)]
        except ValueError:
            raise gtp_engine.GtpError('invalid number of stones')

        for stone in stones:
            proxy.pass_command('play', ['b', stone])

        return ' '.join(stones)

    @_check_boardsize
    @_parse_handicap
    def handle_place_free_handicap(handicap):
        if not 2 <= handicap <= handicap_layout.max_free_handicap_for_board_size(boardsize):
            raise gtp_engine.GtpError('invalid number of stones')

        stones = []

        for i in range(handicap):
            stone = proxy.pass_command('genmove', ['b'])
            if stone.lower() == 'pass':
                break
            stones.append(stone)

        return ' '.join(stones)

    @_check_boardsize
    def handle_set_free_handicap(stones):
        if not 2 <= len(stones) <= handicap_layout.max_free_handicap_for_board_size(boardsize):
            raise gtp_engine.GtpError('invalid number of stones')

        for stone in stones:
            proxy.pass_command('play', ['b', stone])

    proxy.engine.add_commands({
        'name': handle_name,
        'boardsize': handle_boardsize,
        'fixed_handicap': handle_fixed_handicap,
        'place_free_handicap': handle_place_free_handicap,
        'set_free_handicap': handle_set_free_handicap,
    })

    try:
        proxy.run()
    except KeyboardInterrupt:
        sys.exit(1)
