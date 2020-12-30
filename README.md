# dwg-to-dxf
Tool to convert dwg file format to dxf file format

## Build

```
docker build \
    --label openindoor/dwg-to-dxf \
    -t openindoor/dwg-to-dxf \
    dwg-to-dxf
```

## Deploy

```
docker tag openindoor/dwg-to-dxf openindoor/dwg-to-dxf:1.0.0
docker push  openindoor/dwg-to-dxf:1.0.0
```

## Usage

```
docker run \
    -v $(pwd)/../private_data/PLANS:/data \
    -it \
    openindoor/dwg-to-dxf
```