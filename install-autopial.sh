#!/usr/bin/env bash

BLACK=`tput setaf 0`
RED=`tput setaf 1`
GREEN=`tput setaf 2`
YELLOW=`tput setaf 3`
BLUE=`tput setaf 4`
MAGENTA=`tput setaf 5`
CYAN=`tput setaf 6`
WHITE=`tput setaf 7`
BOLD=`tput bold`
RESET=`tput sgr0`

AUTOPIAL_INSTALL_DIR="`pwd`/autopial"

function install-dependencies {
    MODULE_DIR=$1

    APT_PACKAGES="$MODULE_DIR/requirements_packages"
    if [ -e $APT_PACKAGES ]; then
        PACKAGE_LIST=$(grep -vE "^\s*#" $APT_PACKAGES  | tr "\n" " ")
        echo -e "${YELLOW}Installing distribution packages: $PACKAGE_LIST ${RESET}"
        sudo apt-get install -y $PACKAGE_LIST
    fi

    PIP_PACKAGES="$MODULE_DIR/requirements_pip"
    echo "$PIP_PACKAGES"
    if [ -e $PIP_PACKAGES ]; then
        PACKAGE_LIST=$(grep -vE "^\s*#" $PIP_PACKAGES  | tr "\n" " ")
        echo -e "${YELLOW}Installing pip packages: $PACKAGE_LIST ${RESET}"
        sudo pip install -r $PIP_PACKAGES
    fi
}

function create-supervisor-service {
    DEST_FILE=$1
    WORKER_NAME=$2
    WORKER_COMMAND=$3
    WORKER_DIR=$4

    sed -e "s|\${WORKER_NAME}|$MODULE_NAME|" \
    -e "s|\${WORKER_COMMAND}|$MODULE_COMMAND|" \
    -e "s|\${WORKER_DIR}|$MODULE_DIR|" \
    -e "s|\${PYTHON_PATH}|$LIBRARY_DIR|" \
    -e "s|\${AUTOPIAL_UID}|$AUTOPIAL_UID|" \
    -e "s|\${AUTOPIAL_NAME}|$AUTOPIAL_NAME|" \
    "$SUPERVISOR_TEMPLATE" > $DEST_FILE

    sudo mv -fv $DEST_FILE "/etc/supervisor/conf.d/$DEST_FILE"
}

echo -e "${BLUE}Welcome to the autopial installation process !!${RESET}"
echo -e "${YELLOW}Installing autopial in: $AUTOPIAL_INSTALL_DIR ${RESET}"

if [ ! -d "$AUTOPIAL_INSTALL_DIR" ]; then
        mkdir -p -v $AUTOPIAL_INSTALL_DIR
fi
cd $AUTOPIAL_INSTALL_DIR

AUTOPIAL_UID_FILE="$AUTOPIAL_INSTALL_DIR/autopial_uid"
if [ ! -e $AUTOPIAL_UID_FILE ]; then
        sudo apt-get install -y uuid
        /usr/bin/uuid > $AUTOPIAL_UID_FILE
fi
AUTOPIAL_UID="`cat $AUTOPIAL_UID_FILE`"
echo -e "${YELLOW}Autopial UUID of this device is: $AUTOPIAL_UID ${RESET}"

AUTOPIAL_NAME_FILE="$AUTOPIAL_INSTALL_DIR/autopial_name"
if [ ! -e $AUTOPIAL_NAME_FILE ]; then
        #read -p "Please provide Autopial name for this device: " AUTOPIAL_NAME;
        #echo "$AUTOPIAL_NAME" > "$AUTOPIAL_INSTALL_DIR/autopial_name"
        /bin/hostname > $AUTOPIAL_NAME_FILE
fi
AUTOPIAL_NAME="`cat $AUTOPIAL_NAME_FILE`"
echo -e "${YELLOW}Autopial NAME of this device is: $AUTOPIAL_NAME ${RESET}"

#############################################################################################################
echo -e "${CYAN}Step A.1: installation of mandatory dependencies${RESET}"

sudo apt-get install -y python3 python3-dev git curl build-essential

if [ ! -e "$AUTOPIAL_INSTALL_DIR/get-pip.py" ]; then
    curl -v https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    sudo python3 get-pip.py
fi
#############################################################################################################


#############################################################################################################
echo -e "${CYAN}Step A.2: installation of autopial library${RESET}"
sleep 1
LIBRARY_DIR="$AUTOPIAL_INSTALL_DIR/autopial-lib"
SUPERVISOR_TEMPLATE="$LIBRARY_DIR/supervisor_template.conf"

if [ -d $LIBRARY_DIR ]; then
    sudo rm -fr $LIBRARY_DIR
fi
git clone https://github.com/picusalex/autopial-lib.git

install-dependencies $LIBRARY_DIR

sudo cp -f -v "$LIBRARY_DIR/supervisord.conf" /etc/supervisor/supervisord.conf
#############################################################################################################


#############################################################################################################
echo -e "${CYAN}Step B.1: installation of autopial WEBSERVER${RESET}"
read -p "Confirm installation ? [y/N]: " INSTALL_BOOL;
if [ "$INSTALL_BOOL" == "y" ] || [ "$INSTALL_BOOL" == "Y" ]
then
    MODULE_DIR="$AUTOPIAL_INSTALL_DIR/autopial-webserver"
    MODULE_SUPERVISOR="autopial-webserver.conf"
    MODULE_COMMAND="/usr/bin/python3 autopial-webserver.py"
    MODULE_NAME="WebServer"
    if [ -d $MODULE_DIR ]; then
            rm -fr $MODULE_DIR
    fi
    git clone https://github.com/picusalex/autopial-webserver.git

    install-dependencies $MODULE_DIR
    create-supervisor-service $MODULE_SUPERVISOR $MODULE_NAME $MODULE_COMMAND $MODULE_DIR
fi
#############################################################################################################


#############################################################################################################
echo -e "${CYAN}Step B.2: installation of autopial SYSTEM worker${RESET}"
read -p "Confirm installation ? [y/N]: " INSTALL_BOOL;
if [ "$INSTALL_BOOL" == "y" ] || [ "$INSTALL_BOOL" == "Y" ]
then
    MODULE_DIR="$AUTOPIAL_INSTALL_DIR/autopial-system"
    MODULE_SUPERVISOR="autopial-system.conf"
    MODULE_COMMAND="/usr/bin/python3 autopial-system.py"
    MODULE_NAME="SystemWorker"

    if [ -d $MODULE_DIR ]; then
        rm -fr $MODULE_DIR
    fi
    git clone https://github.com/picusalex/autopial-system.git

    install-dependencies $MODULE_DIR
    create-supervisor-service $MODULE_SUPERVISOR $MODULE_NAME $MODULE_COMMAND $MODULE_DIR

fi
#############################################################################################################


#############################################################################################################
echo -e "${CYAN}Step B.3: installation of autopial GPS worker${RESET}"
read -p "Confirm installation ? [y/N]: " INSTALL_BOOL;
if [ "$INSTALL_BOOL" == "y" ] || [ "$INSTALL_BOOL" == "Y" ]
then
    MODULE_DIR="$AUTOPIAL_INSTALL_DIR/autopial-gps"
    MODULE_SUPERVISOR="autopial-gps.conf"
    MODULE_COMMAND="/usr/bin/python3 autopial-gps.py"
    MODULE_NAME="GPSWorker"

    if [ -d $MODULE_DIR ]; then
            rm -fr $MODULE_DIR
    fi
    git clone https://github.com/picusalex/autopial-gps.git

    install-dependencies $MODULE_DIR
    create-supervisor-service $MODULE_SUPERVISOR $MODULE_NAME $MODULE_COMMAND $MODULE_DIR
fi
#############################################################################################################

#############################################################################################################
echo -e "${CYAN}Step B.4: installation of autopial OBD2 worker${RESET}"
read -p "Confirm installation ? [y/N]: " INSTALL_BOOL;
if [ "$INSTALL_BOOL" == "y" ] || [ "$INSTALL_BOOL" == "Y" ]
then
    MODULE_DIR="$AUTOPIAL_INSTALL_DIR/autopial-obd"
    MODULE_SUPERVISOR="autopial-obd.conf"
    MODULE_COMMAND="/usr/bin/python3 autopial-obd.py"
    MODULE_NAME="OBDWorkers"
    if [ -d $MODULE_DIR ]; then
            rm -fr $MODULE_DIR
    fi
    git clone https://github.com/picusalex/autopial-obd.git

    install-dependencies $MODULE_DIR
    create-supervisor-service $MODULE_SUPERVISOR $MODULE_NAME $MODULE_COMMAND $MODULE_DIR
fi
#############################################################################################################

sudo service supervisor restart
sleep 1
sudo service supervisor status
