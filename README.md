# Random GTP proxy
Playing with AI is too predictable, too hard or maybe too easy?
This GTP engine distributes `genmove` command between multiple other engines
and after that gives analysis of the current position.

Sample configuration:
```ini
; Engine probabilities:
; 25% AmiGo
; 75% GnuGo
;  0% Leela Zero
;
; And after each `genmove` command GnuGo and Leela Zero will analyze current position.

[amigo]
command=amigogtp
weight=1

[gnugo]
command=gnugo --mode gtp
weight=3
analyze=estimate_score

[leela-zero]
command=leelaz --gtp --weights /path/to/network.gz --noponder --playouts 1
weight=0
analyze=lz-analyze
```

GTP command:
```shell
/path/to/rand_gtp.py /path/to/config.ini
```

# Handicap support for engines whithout it
This GTP engine adds support for fixed and free handicap for engines which do not support them.

GTP command:
```shell
/path/to/handicap_gtp.py <real GTP engine>
```
