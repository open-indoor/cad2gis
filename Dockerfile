FROM opensuse/tumbleweed

#Install latest patches
RUN zypper up

RUN zypper in --help

RUN zypper --non-interactive in --no-recommends \
    bash \
    wget \
    xvfb-run

RUN mkdir -p /dwg-to-dxf
WORKDIR /dwg-to-dxf

# RUN zypper --non-interactive in --no-recommends \
#     fontconfig libICE6 libQt5Core5 libQt5DBus5 libQt5Gui5 libQt5Network5 \
#     libQt5Widgets5 libSM6 libdouble-conversion3 libevdev2 libfontconfig1 \
#     libgobject-2_0-0 libgraphite2-3 libgudev-1_0-0 libharfbuzz0 libicu67 \
#     libicu67-ledata libinput10 libjpeg8 libmtdev1 libpcre2-16-0 libts0 \
#     libwacom-data libwacom2 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
#     libxcb-randr0 libxcb-render-util0 libxcb-render0 libxcb-shape0 libxcb-shm0 \
#     libxcb-util1 libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 \
#     libxkbcommon-x11-0 libxkbcommon0 timezone

RUN zypper --non-interactive in --no-recommends \
    fontconfig libICE6 libQt5Core5 libQt5DBus5 libQt5Gui5 libQt5Network5 \
    libQt5Widgets5 libSM6 libdouble-conversion3 libevdev2 libfontconfig1 \
    libgobject-2_0-0 libgraphite2-3 libgudev-1_0-0 libharfbuzz0 libinput10 \
    libjpeg8 libmtdev1 libpcre2-16-0 libts0 \
    libwacom-data libwacom2 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-render0 libxcb-shape0 libxcb-shm0 \
    libxcb-util1 libxcb-xinerama0 libxcb-xinput0 libxcb-xkb1 \
    libxkbcommon-x11-0 libxkbcommon0 timezone

RUN wget --no-check-certificate https://download.opendesign.com/guestfiles/Demo/ODAFileConverter_QT5_lnxX64_7.2dll_21.11.rpm
RUN zypper --non-interactive in --no-recommends --allow-unsigned-rpm ODAFileConverter_QT5_lnxX64_7.2dll_21.11.rpm

COPY ./dwg-to-dxf.sh /dwg-to-dxf/dwg-to-dxf
RUN chmod +x /dwg-to-dxf/dwg-to-dxf

CMD /dwg-to-dxf/dwg-to-dxf