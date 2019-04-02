# Random GTP proxy
Playing with AI is too predictable, too hard or maybe too easy?
This GTP engine distributes `genmove` command between multiple other engines.

Sample configuration:
```ini
# Leela zero with some AmiGo blunders in-between.

[amigo]
command=/path/to/amigogtp
weight=1

[leela-zero]
command=/path/to/leelaz --gtp --weights /path/to/network.gz
weight=8
```

GTP command:
```shell
/path/to/rand_gtp.py /path/to/config.ini
```
