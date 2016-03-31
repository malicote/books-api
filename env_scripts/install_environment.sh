#!/bin/bash

install_extension_or_die() {
    if ! flask/bin/pip install $1; then
        echo "Failed to install $1, exiting"
        popd
        exit 1
    fi
}

INSTALL_DIR="$1"
if [ -z "$1" ]; then
    INSTALL_DIR=`pwd`
fi

if [ ! -d "$INSTALL_DIR" ]; then
    echo "$INSTALL_DIR doesn't exist."
    exit 1
fi

pushd $INSTALL_DIR

if [ ! -d $INSTALL_DIR/flask ]; then
    echo "Installing flask via virtualenv"
    if ! virtualenv flask; then
        echo "Failed to install virtual env"
        popd
        exit
    fi
fi

install_extension_or_die flask
install_extension_or_die flask-login
install_extension_or_die flask-openid
install_extension_or_die flask-mail
install_extension_or_die flask-sqlalchemy
install_extension_or_die sqlalchemy-migrate
install_extension_or_die flask-whooshalchemy
install_extension_or_die flask-wtf
install_extension_or_die flask-babel
install_extension_or_die guess_language
install_extension_or_die flipflop
install_extension_or_die coverage

popd

echo "Installation complete"
