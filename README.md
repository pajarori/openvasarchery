# openvasarchery
setup network
```
docker network create --driver bridge openvasd                                                                                               [4:12:39]
```
run archerysec
```
docker-compose up
```

run openvas
```
docker-compose -f openvas-compose.yaml up
```
library
https://github.com/pajarori/openvas_lib


