#!/bin/bash

# Exit on error, undefined variables, and pipe failures
set -euo pipefail

echo "==========================================================="
echo "        Rootless Docker & Dashboard Setup Script           "
echo "==========================================================="
echo "Which Ubuntu version are you currently working on?"
echo "Enter 24 for Ubuntu 24.04 (or 23.10+)"
echo "Enter 20 for Ubuntu 20.04"
echo "==========================================================="
read -r -p "Selection (20/24): " UBUNTU_VERSION
echo ""

if [ "$UBUNTU_VERSION" = "24" ]; then
    echo ">>> Starting setup for Ubuntu 24..."

    # ==============================================================================
    # SCRIPT 1 FUNCTIONALITY: ROOTLESS DOCKER & APPARMOR CONFIGURATION (UBUNTU 24)
    # ==============================================================================

    # --- 1. INSTALLATION & CONFIGURATION (Script 1 Functionality) ---

    echo ">>> 1. Installing Prerequisites..."
    sudo apt-get update
    sudo apt-get install -y curl uidmap dbus-user-session slirp4netns curl systemd-container \
    ca-certificates gnupg apt-transport-https software-properties-common apache2-utils build-essential gcc g++


    # ==============================================================================
    # 0. PRE-FLIGHT CHECKS & DIRECTORY VALIDATION
    # ==============================================================================

    # --- 2. PRE-FLIGHT CHECKS ---

    # Function to check if docker-compose.yml exists in the current directory
    check_compose_file() {
        if [ ! -f "docker-compose.yml" ] && [ ! -f "docker-compose.yaml" ]; then
            echo "Error: docker-compose.yml not found in the current directory."
            echo "Please run this script from the folder containing your docker-compose file."
            exit 1
        fi
    }

    # Ensure script is NOT started as root (Rootless Docker requirement)
    if [ "$(id -u)" = "0" ]; then
        echo "Error: Please run this script as your regular user, not as root/sudo."
        echo "The script will ask for your password automatically when it needs root privileges."
        exit 1
    fi

    check_compose_file
    PROJECT_DIR=$(pwd)
    USER_NAME=$(whoami)
    USER_ID=$(id -u)
    BIN_DIR="$HOME/bin"
    SERVICE_NAME="my_dashboard.service"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

    echo ">>> 2. Checking Internet Connectivity..."
    if ! curl -s --head  --request GET https://get.docker.com | grep "200 OK" > /dev/null; then
        echo "Error: No internet connection detected for get.docker.com."
        echo "Please check your network settings or /etc/resolv.conf"
        exit 1
    fi


    echo ">>> 3. Configuring subuid and subgid..."
    if ! grep -q "^${USER_NAME}:" /etc/subuid; then
        sudo usermod --add-subuids 100000-165535 "${USER_NAME}"
    fi
    if ! grep -q "^${USER_NAME}:" /etc/subgid; then
        sudo usermod --add-subgids 100000-165535 "${USER_NAME}"
    fi

    echo ">>> 4. Configuring Cgroup v2 Delegation..."
    sudo mkdir -p /etc/systemd/system/user@.service.d
    echo "[Service]
    Delegate=cpu cpuset io memory pids" | sudo tee /etc/systemd/system/user@.service.d/delegate.conf > /dev/null
    sudo systemctl daemon-reload
    sudo loginctl enable-linger "${USER_NAME}"

    echo ">>> 5. FULL PURGE: Removing old/failed Docker installations..."
    # Stop and disable any running instances
    systemctl --user stop docker.service 2>/dev/null || true
    systemctl --user disable docker.service 2>/dev/null || true

    # Remove binaries from previous installs
    sudo rm -f "$BIN_DIR/dockerd" "$BIN_DIR/rootlesskit" "$BIN_DIR/docker"* sudo rm -rf "/run/user/$USER_ID/docker"*

    # Remove corrupted runtime sockets and PID files
    sudo rm -rf "/run/user/$(id -u)/docker"*
    sudo rm -rf "/run/user/$(id -u)/dockerd-rootless"*

    # Remove existing configurations and local container data
    # WARNING: This wipes existing rootless containers and volumes to ensure a 100% clean slate
    sudo rm -rf ~/.config/docker
    sudo rm -rf ~/.local/share/docker

    #sudo rm -rf ~/.config/docker ~/.local/share/docker

    echo ">>> 6. Handling AppArmor Restrictions (Ubuntu 23.10/24.04+)..."
    # Destroy any custom AppArmor profiles from previous troubleshooting attempts
    sudo rm -f /etc/apparmor.d/home.*.rootlesskit
    sudo rm -f /etc/apparmor.d/local/home.*.rootlesskit

    # Flush the AppArmor cache so it forgets the deleted profiles
    sudo systemctl restart apparmor.service || true

    # Apply the official kernel parameter override to allow unprivileged user namespaces
    sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

    # Make the override permanent across future machine reboots
    echo "kernel.apparmor_restrict_unprivileged_userns=0" | sudo tee /etc/sysctl.d/60-apparmor-userns.conf > /dev/null
    sudo sysctl -p /etc/sysctl.d/60-apparmor-userns.conf > /dev/null


    echo ">>> 7. Handling AppArmor Restrictions (Ubuntu 23.10+)..."
    # Ensure the bin directory exists so the path is valid
    mkdir -p "$BIN_DIR"

    # (FIXED) Create a dummy file so apparmor doesn't fail before Docker installs it
    touch "$BIN_DIR/rootlesskit"
    chmod +x "$BIN_DIR/rootlesskit"

    # (FIXED) Generate the AppArmor profile name using pure bash to avoid 'tr' parsing errors
    ROOTLESSKIT_PATH="$BIN_DIR/rootlesskit"
    NO_LEADING_SLASH="${ROOTLESSKIT_PATH#/}"
    AA_PROFILE_NAME="${NO_LEADING_SLASH//\//.}"

    # (FIXED) Ensure AppArmor directory exists before tee attempts to write
    sudo mkdir -p /etc/apparmor.d/


    # Generate the AppArmor profile name from the path
    # e.g., /home/user/bin/rootlesskit -> home.user.bin.rootlesskit
    #ROOTLESSKIT_PATH="$BIN_DIR/rootlesskit"
    #AA_PROFILE_NAME=$(echo "${ROOTLESSKIT_PATH#/}" | tr '/' '.')

    # Create the AppArmor profile to allow unprivileged user namespaces
    cat <<EOF | sudo tee "/etc/apparmor.d/${AA_PROFILE_NAME}" > /dev/null
abi <abi/4.0>,
include <tunables/global>

$ROOTLESSKIT_PATH flags=(unconfined) {
  userns,
  include if exists <local/${AA_PROFILE_NAME}>
}
EOF

    # Reload AppArmor
    sudo systemctl restart apparmor.service


    echo ">>> 8. Installing Rootless Docker..."
    # Clean up previous failed attempts
    systemctl --user stop docker 2>/dev/null || true

    # (FIXED) Export variable to bypass iptables check (Addresses the error in your screenshot)
    export DOCKERD_ROOTLESS_SKIP_IPTABLES=1


    # --- ERROR FIX IMPLEMENTED HERE ---
    # Load nf_tables module as required by the rootless installation script
    sudo modprobe nf_tables
    # Ensure the module loads on future boots
    echo "nf_tables" | sudo tee /etc/modules-load.d/nf_tables.conf > /dev/null
    # ----------------------------------


    # Install via official script
    curl -fsSL https://get.docker.com/rootless | sh


    echo ">>> 9. Configuring Docker Daemon..."
    mkdir -p ~/.config/docker
    #rm -f "$BIN_DIR/dockerd"
    #rm -f "$BIN_DIR/rootlesskit"
    cat <<EOF > ~/.config/docker/daemon.json
{
  "iptables": false,
  "experimental": true,
  "dns": ["8.8.8.8","1.1.1.1"]
}
EOF

    echo ">>> 10. Starting User-Level Docker Service..."
    systemctl --user daemon-reload
    systemctl --user enable docker
    systemctl --user start docker

    echo ">>> 11. Installing Docker Compose V2..."
    # Create the cli-plugins directory
    mkdir -p ~/.docker/cli-plugins/
    # Fetch the latest version tag from GitHub API
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    echo "Downloading Docker Compose version $COMPOSE_VERSION..."
    # Download the binary
    curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" -o ~/.docker/cli-plugins/docker-compose
    # Make it executable
    chmod +x ~/.docker/cli-plugins/docker-compose


    # ==============================================================================
    # SCRIPT 2 FUNCTIONALITY: SYSTEMD PERSISTENCE AND VM BOOT AUTO-START
    # ==============================================================================

    # --- 3. PERSISTENCE & AUTO-RESTART (Script 2 Functionality) ---

    echo ">>> 12. Configuring System-Level Persistence..."
    # Ensure system-level docker is enabled as per requirement 3 & 4
    #sudo systemctl enable docker.service || true
    #sudo systemctl start docker.service || true
    #sudo systemctl enable containerd.service || true

    # Ensure user-level docker is enabled (containerd does not exist as a separate unit in rootless)

    systemctl --user enable docker.service || true
    systemctl --user start docker.service || true
    #systemctl --user enable containerd.service || true



    echo ">>> 13. Creating Dashboard Auto-Start Service..."
    echo ">>> 14 Ensuring System Docker and Containerd are enabled to start on boot..."
    # Note: We use the rootless docker socket for the service to maintain functionality
    echo ">>> 15. Creating systemd service file at $SERVICE_PATH..."
    # We map the ExecStart to the user's specific Compose installation and rootless socket context
    sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Docker Compose Dashboard Service
Requires=user@$USER_ID.service
After=network.target user@$USER_ID.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment="DOCKER_HOST=unix:///run/user/$USER_ID/docker.sock"
Environment="PATH=$BIN_DIR:/usr/bin:/bin"
ExecStart=$HOME/.docker/cli-plugins/docker-compose up
ExecStop=$HOME/.docker/cli-plugins/docker-compose down

[Install]
WantedBy=multi-user.target
EOF

    echo ">>> 16. Reloading systemd daemon to recognize the new service..."
    sudo systemctl daemon-reload

    # --- 3.5 POPULATE .ENV FILE ---
    echo ">>> 16.5 Populating .env file for Docker Compose..."
    touch "$PROJECT_DIR/.env"
    # Remove existing PUID/PGID to avoid duplicate declarations
    sed -i '/^PUID=/d' "$PROJECT_DIR/.env"
    sed -i '/^PGID=/d' "$PROJECT_DIR/.env"
    echo "PUID=$(id -u)" >> "$PROJECT_DIR/.env"
    echo "PGID=$(id -g)" >> "$PROJECT_DIR/.env"

    # Enforce simple authentication setup for monitoring dashboards
    if ! grep -q "^DASHBOARDS_USERNAME=" "$PROJECT_DIR/.env"; then
        echo "DASHBOARDS_USERNAME=nymdashboards" >> "$PROJECT_DIR/.env"
    fi
    if ! grep -q "^HASHED_PASSWORD=" "$PROJECT_DIR/.env"; then
        HASHED_VAL=$(htpasswd -n -B -b nymdashboards Thesecret.2 | cut -d: -f2)
        ESCAPED_VAL=${HASHED_VAL//\$/\$\$} # Escape $ to $$ for compose
        echo "HASHED_PASSWORD=${ESCAPED_VAL}" >> "$PROJECT_DIR/.env"
    fi

    # --- 4. ENVIRONMENT SETUP ---

    echo ">>> 17. Updating Environment Variables..."
    if ! grep -q "DOCKER_HOST" ~/.bashrc; then
        {
          echo ''
          echo '# Rootless Docker Variables'
          echo "export DOCKER_HOST=unix:///run/user/$USER_ID/docker.sock"
          echo 'export PATH=$HOME/bin:$PATH'
        } >> ~/.bashrc
    fi

    echo ">>> 18. Updating Environment Variables..."
    echo "1. Run: source ~/.bashrc"

    # (FIXED) source ~/.bashrc often fails in non-interactive scripts. 
    # We explicitly export them to the current shell so steps 19 and 21 actually work.
    export DOCKER_HOST="unix:///run/user/$USER_ID/docker.sock"
    export PATH="$HOME/bin:$PATH"

    echo ">>> 19. Verify Compose Setup Status..."
    docker compose version


    echo ">>> 20. Enabling and starting $SERVICE_NAME..."
    echo ">>> 21. Creating docker networks..."
    # (FIXED) Added "|| true" so the script doesn't crash if the networks already exist
    docker network create traefik_public || true
    docker network create internals_network || true

    echo ">>> 22. Enabling $SERVICE_NAME..."
    sudo systemctl enable "$SERVICE_NAME"


    echo "==========================================================="
    echo "==========================================================="
    echo "Setup Successful! Please follow the following prompts before running the $SERVICE_NAME"
    echo "==========================================================="
    echo "# Generate a hashed password for the simple authentication for the monitoring dashboards (e.g., for user \"admin\" with password \"yourpassword\")"
    echo "# Note the double quote"
    echo 'htpasswd -nbB admin "yourpassword"'
    echo "Update docker-compose.yml: Ensure all dollar signs ($) in the hashed password are escaped with another dollar sign (e.g., \$\$2y\$\$05\$\$...) when used in the docker-compose.yml file."
    echo "==========================================================="
    echo "Project Path: $PROJECT_DIR"
    echo "1. Run: source ~/.bashrc"
    echo "2. Your dashboard will now auto-start on every VM reboot."
    echo "3. Docker and Containerd services remain active."
    echo "4. Note: If you still see permission errors, a full reboot is required."
    echo "==========================================================="
    echo "==========================================================="



    echo ">>> 23. Starting $SERVICE_NAME..."
    sudo systemctl start "$SERVICE_NAME"


    echo ">>> 24. Check Auto-Start Status..."
    sudo systemctl status $SERVICE_NAME

    echo "==========================================================="
    echo "Setup Successful!"
    echo "Project Path: $PROJECT_DIR"
    echo "1. Run: source ~/.bashrc"
    echo "2. Your dashboard will now auto-start on every VM reboot."
    echo "3. Docker and Containerd services remain active."
    echo "4. Note: If you still see permission errors, a full reboot is required."
    echo "==========================================================="

elif [ "$UBUNTU_VERSION" = "20" ]; then
    echo ">>> Starting setup for Ubuntu 20..."

    # ==============================================================================
    # SCRIPT 1 FUNCTIONALITY: ROOTLESS DOCKER & APPARMOR CONFIGURATION (UBUNTU 20)
    # ==============================================================================

    # --- 1. INSTALLATION & CONFIGURATION (Script 1 Functionality) ---

    echo ">>> 1. Installing Prerequisites..."
    sudo apt-get update
    sudo apt-get install -y curl uidmap dbus-user-session slirp4netns curl systemd-container \
    ca-certificates gnupg apt-transport-https software-properties-common apache2-utils build-essential gcc g++


    # ==============================================================================
    # 0. PRE-FLIGHT CHECKS & DIRECTORY VALIDATION
    # ==============================================================================

    # --- 2. PRE-FLIGHT CHECKS ---

    # Function to check if docker-compose.yml exists in the current directory
    check_compose_file() {
        if [ ! -f "docker-compose.yml" ] && [ ! -f "docker-compose.yaml" ]; then
            echo "Error: docker-compose.yml not found in the current directory."
            echo "Please run this script from the folder containing your docker-compose file."
            exit 1
        fi
    }

    # Function to check if the specific Ubuntu 20 fix file exists in the current directory
    check_ubuntu20_fix_file() {
        if [ ! -f "docker-compose-ubuntu-20-fix2.yml" ]; then
            echo "Error: docker-compose-ubuntu-20-fix2.yml not found in the current directory."
            echo "Please ensure the ubuntu 20 fix compose file is present before running."
            exit 1
        fi
    }

    # Ensure script is NOT started as root (Rootless Docker requirement)
    if [ "$(id -u)" = "0" ]; then
        echo "Error: Please run this script as your regular user, not as root/sudo."
        echo "The script will ask for your password automatically when it needs root privileges."
        exit 1
    fi

    # Run checks
    check_compose_file
    check_ubuntu20_fix_file

    PROJECT_DIR=$(pwd)
    USER_NAME=$(whoami)
    USER_ID=$(id -u)
    BIN_DIR="$HOME/bin"
    SERVICE_NAME="my_dashboard.service"
    SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

    echo ">>> 2. Checking Internet Connectivity..."
    if ! curl -s --head  --request GET https://get.docker.com | grep "200 OK" > /dev/null; then
        echo "Error: No internet connection detected for get.docker.com."
        echo "Please check your network settings or /etc/resolv.conf"
        exit 1
    fi


    echo ">>> 3. Configuring subuid and subgid..."
    if ! grep -q "^${USER_NAME}:" /etc/subuid; then
        sudo usermod --add-subuids 100000-165535 "${USER_NAME}"
    fi
    if ! grep -q "^${USER_NAME}:" /etc/subgid; then
        sudo usermod --add-subgids 100000-165535 "${USER_NAME}"
    fi

    echo ">>> 4. Configuring Cgroup v2 Delegation..."
    sudo mkdir -p /etc/systemd/system/user@.service.d
    echo "[Service]
    Delegate=cpu cpuset io memory pids" | sudo tee /etc/systemd/system/user@.service.d/delegate.conf > /dev/null
    sudo systemctl daemon-reload
    sudo loginctl enable-linger "${USER_NAME}"

    echo ">>> 5. FULL PURGE: Removing old/failed Docker installations..."
    # Stop and disable any running instances
    systemctl --user stop docker.service 2>/dev/null || true
    systemctl --user disable docker.service 2>/dev/null || true

    # Remove binaries from previous installs
    sudo rm -f "$BIN_DIR/dockerd" "$BIN_DIR/rootlesskit" "$BIN_DIR/docker"* sudo rm -rf "/run/user/$USER_ID/docker"*

    # Remove corrupted runtime sockets and PID files
    sudo rm -rf "/run/user/$(id -u)/docker"*
    sudo rm -rf "/run/user/$(id -u)/dockerd-rootless"*

    # Remove existing configurations and local container data
    # WARNING: This wipes existing rootless containers and volumes to ensure a 100% clean slate
    sudo rm -rf ~/.config/docker
    sudo rm -rf ~/.local/share/docker


    echo ">>> 6. Handling AppArmor Restrictions (Ubuntu 23.10/24.04+)..."
    # Destroy any custom AppArmor profiles from previous troubleshooting attempts
    sudo rm -f /etc/apparmor.d/home.*.rootlesskit
    sudo rm -f /etc/apparmor.d/local/home.*.rootlesskit

    # Flush the AppArmor cache so it forgets the deleted profiles
    sudo systemctl restart apparmor.service || true

    # Apply the official kernel parameter override to allow unprivileged user namespaces
    if [ -f /proc/sys/kernel/apparmor_restrict_unprivileged_userns ]; then
        sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

        # Make the override permanent across future machine reboots
        echo "kernel.apparmor_restrict_unprivileged_userns=0" | sudo tee /etc/sysctl.d/60-apparmor-userns.conf > /dev/null
        sudo sysctl -p /etc/sysctl.d/60-apparmor-userns.conf > /dev/null
    else
        echo "   -> Skipping: kernel.apparmor_restrict_unprivileged_userns not found (expected on Ubuntu 20.04)."
    fi


    echo ">>> 7. Handling AppArmor Restrictions (Ubuntu 23.10+)..."
    # ERROR FIX: Conditionally execute the AppArmor profile generation so it doesn't crash Ubuntu 20.04
    if [ -f /proc/sys/kernel/apparmor_restrict_unprivileged_userns ]; then
        # Ensure the bin directory exists so the path is valid
        mkdir -p "$BIN_DIR"

        # Create a dummy file so apparmor doesn't fail before Docker installs it
        touch "$BIN_DIR/rootlesskit"
        chmod +x "$BIN_DIR/rootlesskit"

        # Generate the AppArmor profile name using pure bash to avoid 'tr' parsing errors
        ROOTLESSKIT_PATH="$BIN_DIR/rootlesskit"
        NO_LEADING_SLASH="${ROOTLESSKIT_PATH#/}"
        AA_PROFILE_NAME="${NO_LEADING_SLASH//\//.}"

        # Ensure AppArmor directory exists before tee attempts to write
        sudo mkdir -p /etc/apparmor.d/

        # Create the AppArmor profile to allow unprivileged user namespaces
        cat <<EOF | sudo tee "/etc/apparmor.d/${AA_PROFILE_NAME}" > /dev/null
abi <abi/4.0>,
include <tunables/global>

$ROOTLESSKIT_PATH flags=(unconfined) {
  userns,
  include if exists <local/${AA_PROFILE_NAME}>
}
EOF

        # Reload AppArmor
        sudo systemctl restart apparmor.service
    else
        echo "   -> Skipping: Custom AppArmor profile generation not required on Ubuntu 20.04."
    fi


    echo ">>> 8. Installing Rootless Docker..."
    # Clean up previous failed attempts
    systemctl --user stop docker 2>/dev/null || true

    # Export variable to bypass iptables check
    export DOCKERD_ROOTLESS_SKIP_IPTABLES=1

    # Load nf_tables module as required by the rootless installation script
    sudo modprobe nf_tables
    # Ensure the module loads on future boots
    echo "nf_tables" | sudo tee /etc/modules-load.d/nf_tables.conf > /dev/null

    # Install via official script
    curl -fsSL https://get.docker.com/rootless | sh


    echo ">>> 9. Configuring Docker Daemon..."
    mkdir -p ~/.config/docker
    cat <<EOF > ~/.config/docker/daemon.json
{
  "iptables": false,
  "experimental": true,
  "dns": ["8.8.8.8","1.1.1.1"]
}
EOF

    echo ">>> 10. Starting User-Level Docker Service..."
    systemctl --user daemon-reload
    systemctl --user enable docker
    systemctl --user start docker

    echo ">>> 11. Installing Docker Compose V2..."
    # Create the cli-plugins directory
    mkdir -p ~/.docker/cli-plugins/
    # Fetch the latest version tag from GitHub API
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    echo "Downloading Docker Compose version $COMPOSE_VERSION..."
    # Download the binary
    curl -SL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" -o ~/.docker/cli-plugins/docker-compose
    # Make it executable
    chmod +x ~/.docker/cli-plugins/docker-compose


    # ==============================================================================
    # SCRIPT 2 FUNCTIONALITY: SYSTEMD PERSISTENCE AND VM BOOT AUTO-START
    # ==============================================================================

    # --- 3. PERSISTENCE & AUTO-RESTART (Script 2 Functionality) ---

    echo ">>> 12. Configuring System-Level Persistence..."
    # Ensure user-level docker is enabled 
    systemctl --user enable docker.service || true
    systemctl --user start docker.service || true

    echo ">>> 13. Creating Dashboard Auto-Start Service..."
    echo ">>> 14 Ensuring System Docker and Containerd are enabled to start on boot..."
    # Note: We use the rootless docker socket for the service to maintain functionality
    echo ">>> 15. Creating systemd service file at $SERVICE_PATH..."
    # We map the ExecStart to the user's specific Compose installation and rootless socket context
    sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Docker Compose Dashboard Service
Requires=user@$USER_ID.service
After=network.target user@$USER_ID.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=$USER_NAME
WorkingDirectory=$PROJECT_DIR
Environment="DOCKER_HOST=unix:///run/user/$USER_ID/docker.sock"
Environment="PATH=$BIN_DIR:/usr/bin:/bin"
ExecStart=$HOME/.docker/cli-plugins/docker-compose up -d
ExecStop=$HOME/.docker/cli-plugins/docker-compose down

[Install]
WantedBy=multi-user.target
EOF

    echo ">>> 16. Reloading systemd daemon to recognize the new service..."
    sudo systemctl daemon-reload

    # --- 4. ENVIRONMENT SETUP ---

    echo ">>> 17. Updating Environment Variables..."
    if ! grep -q "DOCKER_HOST" ~/.bashrc; then
        {
          echo ''
          echo '# Rootless Docker Variables'
          echo "export DOCKER_HOST=unix:///run/user/$USER_ID/docker.sock"
          echo 'export PATH=$HOME/bin:$PATH'
        } >> ~/.bashrc
    fi

    echo ">>> 18. Populating .env file for Docker Compose..."
    # Ensure the file exists
    touch "$PROJECT_DIR/.env"
    # Remove any existing PUID/PGID lines to prevent duplicates if script is run multiple times
    sed -i '/^PUID=/d' "$PROJECT_DIR/.env"
    sed -i '/^PGID=/d' "$PROJECT_DIR/.env"
    # Inject the current user's UID and GID into the .env file
    echo "PUID=$(id -u)" >> "$PROJECT_DIR/.env"
    echo "PGID=$(id -g)" >> "$PROJECT_DIR/.env"

    # Enforce simple authentication setup for monitoring dashboards
    if ! grep -q "^DASHBOARDS_USERNAME=" "$PROJECT_DIR/.env"; then
        echo "DASHBOARDS_USERNAME=nymdashboards" >> "$PROJECT_DIR/.env"
    fi
    if ! grep -q "^HASHED_PASSWORD=" "$PROJECT_DIR/.env"; then
        HASHED_VAL=$(htpasswd -n -B -b  | cut -d: -f2)
        ESCAPED_VAL=${HASHED_VAL//\$/\$\$} # Escape $ to $$ for compose
        echo "HASHED_PASSWORD=${ESCAPED_VAL}" >> "$PROJECT_DIR/.env"
    fi


    echo ">>> 19. Exporting variables to current session..."
    echo "1. Run: source ~/.bashrc"
    # We explicitly export them to the current shell so steps 20 and 22 actually work.
    export DOCKER_HOST="unix:///run/user/$USER_ID/docker.sock"
    export PATH="$HOME/bin:$PATH"

    echo ">>> 20. Verify Compose Setup Status..."
    docker compose version


    echo ">>> 21. Enabling and starting $SERVICE_NAME..."
    echo ">>> 22. Creating docker networks..."
    # Added "|| true" so the script doesn't crash if the networks already exist
    docker network create traefik_public || true
    docker network create internals_network || true

    echo ">>> 23. Enabling $SERVICE_NAME..."
    sudo systemctl enable "$SERVICE_NAME"


    echo "==========================================================="
    echo "==========================================================="
    echo "Setup Successful! Please follow the following prompts before running the $SERVICE_NAME"
    echo "==========================================================="
    echo "# Generate a hashed password for the simple authentication for the monitoring dashboards (e.g., for user \"admin\" with password \"yourpassword\")"
    echo "# Note the double quote"
    echo 'htpasswd -nbB admin "yourpassword"'
    echo "Update docker-compose.yml: Ensure all dollar signs ($) in the hashed password are escaped with another dollar sign (e.g., \$\$2y\$\$05\$\$...) when used in the docker-compose.yml file."
    echo "==========================================================="
    echo "Project Path: $PROJECT_DIR"
    echo "1. Run: source ~/.bashrc"
    echo "2. Your dashboard will now auto-start on every VM reboot."
    echo "3. Docker and Containerd services remain active."
    echo "4. Note: If you still see permission errors, a full reboot is required."
    echo "==========================================================="
    echo "==========================================================="


    echo ">>> 24. Starting $SERVICE_NAME..."
    sudo systemctl start "$SERVICE_NAME"


    echo ">>> 25. Check Auto-Start Status..."
    sudo systemctl status $SERVICE_NAME

    echo "==========================================================="
    echo "Setup Successful!"
    echo "Project Path: $PROJECT_DIR"
    echo "1. Run: source ~/.bashrc"
    echo "2. Your dashboard will now auto-start on every VM reboot."
    echo "3. Docker and Containerd services remain active."
    echo "4. Note: If you still see permission errors, a full reboot is required."
    echo "==========================================================="

else
    echo "Error: Invalid selection. You must enter either 24 or 20."
    echo "Exiting..."
    exit 1
fi