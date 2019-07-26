#!/bin/bash

set -e

cd ~

mkdir -p /cshome/$USER/local/

cd /tmp/
wget ftp://xmlsoft.org/libxslt/libxslt-1.1.33.tar.gz
tar xzvf libxslt*.gz
cd libxslt*
./configure --prefix=/cshome/$USER/local
make
make install

cd ..
rm libxslt*.tar.gz

echo "export PATH=\$PATH:/cshome/$USER/local/bin" >>~/.bashrc
echo "export CPATH=\$CPATH:/cshome/$USER/local/include" >>~/.bashrc
echo "export LD_LIBRARY_PATH=\$LD_LIBRARY_PATH:/cshome/$USER/local/lib" >>~/.bashrc
source ~/.bashrc

cd ~
git clone https://github.com/Remi-Coulom/gogui 
cd gogui

#sudo apt install ant xsltproc docbook-xsl inkscape

cd /tmp
wget https://www.randelshofer.ch/quaqua/files/quaqua-8.0.nested.zip
unzip quaqua-8.0.nested.zip
unzip quaqua-8.0.zip
cd -

mkdir -p lib
cd lib
cp /tmp/Quaqua/dist/quaqua.jar .
cd -

cd src/net/sf/gogui/images
./svg.sh
cd -

ant

echo "export PATH=\$PATH:/cshome/$USER/gogui/bin" >>~/.bashrc

source ~/.bashrc

exit
