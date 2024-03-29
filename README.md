# cad2gis
Tool to convert autocad file format to geojson file format

## Build and run

### with docker

```
$ docker build . -t openindoor/cad2gis
$ docker run --rm openindoor/cad2gis
```

### with docker-compose

``` 
docker-compose up cad2gis
```

## Usage

### Specs
```
https://cad2gis.openindoor.io/api/convert/_LNG_/_LAT_/_XOFFSET_/_YOFFSET_/_ROTATION_/_SCALE_
```

### Example

```
curl -F "file=@data/my_dxf.dxf" \
    https://cad2gis.openindoor.io/api/convert/3.93/43.56 \
    > my_geojson.geojson
```

Result:

![Latitude/longitude located](doc/lat_lng_location.png)

### Play with XOFFSET and YOFFSET

```
curl -F "file=@data/my_dxf.dxf" \
    https://cad2gis.openindoor.io/api/cad2gis/convert/3.93/43.56/0.01/0.0 \
    > my_geojson.geojson
```

![xoffset (longitude)](doc/xoffset.png)


```
curl -F "file=@cad2gis/data/kingconf/sett_22-11_23.dxf"     https://cad2gis.openindoor.io/api/convert/3.93/43.56/0.01/0.0 > cad2gis/data/kingconf/sett_22-11_23.geojson
```

## Other...
```
curl \
    -F "file=@cad2gis/data/kingconf/sett_22-11_23.dxf" \
    -F "setup=@cad2gis/data/kingconf/setup.json" \
    https://cad2gis.openindoor.io/api/convert/3.9425/43.5695/0.0/0.0/236.23/0.25 \
    > cad2gis/data/kingconf/sett_22-11_23.geojson
```
```
curl \
    -F "file=@cad2gis/data/kingconf/sett_22-11_23.dxf" \
    -F "setup=@cad2gis/data/kingconf/setup.json" \
    https://cad2gis.openindoor.io/api/convert/3.94238/43.56971/0.0/0.0/236.23/0.25 \
    > cad2gis/data/kingconf/sett_22-11_23.geojson
```

744.61
187.26

43,5705037, 3,9510574
43,5707698, 3,9509225
0,0002661, -0,0001349