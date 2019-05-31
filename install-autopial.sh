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

echo -e "${BLUE}Welcome to the autopial installation process !!${RESET}"

echo -e "${WHITE}Installing autopial in: $AUTOPIAL_INSTALL_DIR ${RESET}"

if [ ! -d "$AUTOPIAL_INSTALL_DIR" ]; then
        mkdir -p -v $AUTOPIAL_INSTALL_DIR
fi
cd $AUTOPIAL_INSTALL_DIR

if [ ! -e "$AUTOPIAL_INSTALL_DIR/autopial_uid" ]; then
        sudo apt-get install -y uuid
        /usr/bin/uuid > "$AUTOPIAL_INSTALL_DIR/autopial_uid"
fi
AUTOPIAL_UID="`cat $AUTOPIAL_INSTALL_DIR/autopial_uid`"
echo -e "${WHITE}Autopial UID of this device is: $AUTOPIAL_UID ${RESET}"

if [ ! -e "$AUTOPIAL_INSTALL_DIR/autopial_name" ]; then
        read -p "Please provide Autopial name for this device: " AUTOPIAL_NAME;
        echo "$AUTOPIAL_NAME" > "$AUTOPIAL_INSTALL_DIR/autopial_name"
fi
AUTOPIAL_NAME="`cat $AUTOPIAL_INSTALL_DIR/autopial_name`"
echo -e "${WHITE}Autopial NAME of this device is: $AUTOPIAL_NAME ${RESET}"

#############################################################################################################
echo -e "${CYAN}Step A.1: installation of mandatory dependencies${RESET}"
read -p "Confirm installation ? [y/N]: " INSTALL_BOOL;
if [ "$INSTALL_BOOL" == "y" ] || [ "$INSTALL_BOOL" == "Y" ]
then
    sudo apt-get install -y supervisor redis-server mosquitto python3 python3-dev git

    if [ ! -e "$AUTOPIAL_INSTALL_DIR/get-pip.py" ]; then
        curl -v https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        sudo python3 get-pip.py
    fi
    sudo pip install redis paho-mqtt pyyaml
fi    
#############################################################################################################


#############################################################################################################
echo -e "${CYAN}Step A.2: installation of autopial library${RESET}"
sleep 3
LIBRARY_DIR="$AUTOPIAL_INSTALL_DIR/autopial-lib"
SUPERVISOR_TEMPLATE="$LIBRARY_DIR/supervisor_template.conf"

if [ -d $LIBRARY_DIR ]; then
        sudo rm -fr $LIBRARY_DIR
fi
git clone https://github.com/picusalex/autopial-lib.git

sudo cp -f -v "$LIBRARY_DIR/supervisord.conf" /etc/supervisor/supervisord.conf

PYTHON_PATH=`python3 -m site --user-site`
PYTHON_AUTOPIAL="$PYTHON_PATH/autopial.pth"
if [ ! -e $PYTHON_PATH ]; then
        mkdir -p -v $PYTHON_PATH
fi
echo "$MODULE_DIR" > $PYTHON_AUTOPIAL

#############################################################################################################


#############################################################################################################
echo -e "${CYAN}Step B.1: installation of autopial WEBSERVER${RESET}"
read -p "Confirm installation ? [y/N]: " INSTALL_BOOL;
if [ "$INSTALL_BOOL" == "y" ] || [ "$INSTALL_BOOL" == "Y" ]
then
    MODULE_DIR="$AUTOPIAL_INSTALL_DIR/autopial-webserver"
    MODULE_SUPERVISOR="autopial-webserver.conf"
    MODULE_COMMAND="/usr/bin/python3 $MODULE_DIR/autopial-webserver.py"
    MODULE_NAME="WebServer"
    if [ -d $MODULE_DIR ]; then
            rm -fr $MODULE_DIR
    fi
    git clone https://github.com/picusalex/autopial-webserver.git
    
    sudo pip install flask Flask-SocketIO
    
    cp $SUPERVISOR_TEMPLATE "$MODULE_DIR/$MODULE_SUPERVISOR"
    sed -e "s|\${WORKER_NAME}|$MODULE_NAME|" -e "s|\${WORKER_COMMAND}|$MODULE_COMMAND|" -e "s|\${WORKER_DIR}|$MODULE_DIR|" -e "s|\${PYTHON_PATH}|$LIBRARY_DIR|" -e "s|\${AUTOPIAL_UID}|$AUTOPIAL_UID|" -e "s|\${AUTOPIAL_NAME}|$AUTOPIAL_NAME|" "$SUPERVISOR_TEMPLATE" > "$MODULE_DIR/$MODULE_SUPERVISOR"
    sudo mv -fv "$MODULE_DIR/$MODULE_SUPERVISOR" "/etc/supervisor/conf.d/$MODULE_SUPERVISOR"  
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
    
    sudo pip install psutil uptime
    
    cp $SUPERVISOR_TEMPLATE "$MODULE_DIR/$MODULE_SUPERVISOR"
    sed -e "s|\${WORKER_NAME}|$MODULE_NAME|" -e "s|\${WORKER_COMMAND}|$MODULE_COMMAND|" -e "s|\${WORKER_DIR}|$MODULE_DIR|" -e "s|\${PYTHON_PATH}|$LIBRARY_DIR|" -e "s|\${AUTOPIAL_UID}|$AUTOPIAL_UID|" -e "s|\${AUTOPIAL_NAME}|$AUTOPIAL_NAME|" "$SUPERVISOR_TEMPLATE" > "$MODULE_DIR/$MODULE_SUPERVISOR"
    sudo mv -fv "$MODULE_DIR/$MODULE_SUPERVISOR" "/etc/supervisor/conf.d/$MODULE_SUPERVISOR"   
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
    
    sudo pip install pyserial pynmea2
    
    cp $SUPERVISOR_TEMPLATE "$MODULE_DIR/$MODULE_SUPERVISOR"
    sed -e "s|\${WORKER_NAME}|$MODULE_NAME|" -e "s|\${WORKER_COMMAND}|$MODULE_COMMAND|" -e "s|\${WORKER_DIR}|$MODULE_DIR|" -e "s|\${PYTHON_PATH}|$LIBRARY_DIR|" -e "s|\${AUTOPIAL_UID}|$AUTOPIAL_UID|" -e "s|\${AUTOPIAL_NAME}|$AUTOPIAL_NAME|" "$SUPERVISOR_TEMPLATE" > "$MODULE_DIR/$MODULE_SUPERVISOR"
    sudo mv -fv "$MODULE_DIR/$MODULE_SUPERVISOR" "/etc/supervisor/conf.d/$MODULE_SUPERVISOR"   
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
    
    sudo pip install obd
    
    cp $SUPERVISOR_TEMPLATE "$MODULE_DIR/$MODULE_SUPERVISOR"
    sed -e "s|\${WORKER_NAME}|$MODULE_NAME|" -e "s|\${WORKER_COMMAND}|$MODULE_COMMAND|" -e "s|\${WORKER_DIR}|$MODULE_DIR|" -e "s|\${PYTHON_PATH}|$LIBRARY_DIR|" -e "s|\${AUTOPIAL_UID}|$AUTOPIAL_UID|" -e "s|\${AUTOPIAL_NAME}|$AUTOPIAL_NAME|" "$SUPERVISOR_TEMPLATE" > "$MODULE_DIR/$MODULE_SUPERVISOR"
    sudo mv -fv "$MODULE_DIR/$MODULE_SUPERVISOR" "/etc/supervisor/conf.d/$MODULE_SUPERVISOR"   
fi
#############################################################################################################

sudo service supervisor restart
sudo service supervisor status
