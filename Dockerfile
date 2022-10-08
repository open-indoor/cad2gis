FROM debian:bullseye

RUN apt-get update && apt-get install -y \
    file \
    gdal-bin \
    libc-bin \
    procps \
    python3 \
    python3-pip \
    python3-flask \
    python3-flask-socketio \
    python3-websockets \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    imagemagick \
    x11-apps \
    x11-utils \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /openindoor
WORKDIR /openindoor

RUN wget --no-check-certificate \
    https://download.opendesign.com/guestfiles/Demo/ODAFileConverter_QT5_lnxX64_8.3dll_23.5.deb

# RUN wget --no-check-certificate \
#     https://download.opendesign.com/guestfiles/Demo/ODAFileConverter_QT5_lnxX64_7.2dll_21.11.deb

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxkbcommon-x11-0 \
    libxcursor-dev \
    && rm -rf /var/lib/apt/lists/*

RUN dpkg -i /openindoor/ODAFileConverter_QT5_lnxX64_8.3dll_23.5.deb \
    && apt-get install -f

COPY ./requirements.txt /openindoor/requirements.txt
RUN pip install -r requirements.txt

COPY ./autocad-to-gis.py /openindoor/autocad-to-gis.py
COPY ./autocad-to-ascii_dxf.sh /openindoor/autocad-to-ascii_dxf.sh
RUN chmod +x /openindoor/autocad-to-ascii_dxf.sh
RUN chmod +x /openindoor/autocad-to-gis.py

CMD /openindoor/autocad-to-gis.py