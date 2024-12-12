#!/bin/bash

# Function to stop running processes
kill_processes() {
    echo "Stopping processes..."
    if [ -f /tmp/hanabi_project_server_pid ]; then
        kill "$(cat /tmp/hanabi_project_server_pid)" 2>/dev/null
        rm -f /tmp/hanabi_project_server_pid
    fi
    if [ -f /tmp/hanabi_project_backend_server_pid ]; then
        kill "$(cat /tmp/hanabi_project_backend_server_pid)" 2>/dev/null
        rm -f /tmp/hanabi_project_backend_server_pid
    fi
}

# Handle SIGINT (Ctrl+C) signal
trap 'kill_processes; exit' SIGINT

# Ask the user to choose between "tom" and "tom_human"
printf "\nThis script allows you to start the servers needed for the Hanabi project.\n"
printf "\nType \"1\" for the ToM + Human scenario\nType \"2\" for the ToM scenario\n\n"

# Function to prompt for a valid choice
get_valid_choice() {
    while true; do     
        # Read the user's choice
        read -r -n 1 choice
        echo  # for a newline

        case "$choice" in
            1)
                arg="tom_human"
                break
                ;;
            2)
                arg="tom"
                break
                ;;
            *)
                echo "Invalid choice! Please try again."
                ;;
        esac
    done
}

# Function to prompt for a valid close tabs choice
get_valid_close_tabs_choice() {
    while true; do
        # Ask the user if they want to close the tabs when done
        echo ""
        printf "Type \"1\" to close the tabs when the script terminates\nType \"2\" to keep the tabs open\n\n"

        # Read the user's choice for closing tabs
        read -r -n 1 close_tabs
        echo  # for a newline

        case "$close_tabs" in
            1)
                close_tabs_option="close"
                break
                ;;
            2)
                close_tabs_option="keep"
                break
                ;;
            *)
                echo "Invalid choice."
                close_tabs_option="keep"
                ;;
        esac
    done
}

# Get a valid choice for the scenario
get_valid_choice

# Get a valid choice for closing tabs
get_valid_close_tabs_choice

if [ "$close_tabs_option" == "close" ]; then 
    # Open the first terminal in a new tab with the title "Frontend Server"
    gnome-terminal --tab --title="Frontend Server" -- bash -c "
    cd ~/HanabiBackend/pythonProject/web-hanabi
    node server.js $arg &
    echo \$! > /tmp/hanabi_project_server_pid
    wait \$!
    " &

    # Open the second terminal in a new tab with the title "Backend Server"
    gnome-terminal --tab --title="Backend Server" -- bash -c "
    cd ~/HanabiBackend/pythonProject/web-hanabi-backend
    node backend-server.js $arg &
    echo \$! > /tmp/hanabi_project_backend_server_pid
    wait \$!
    " &
else 
    # Open the first terminal in a new tab with the title "Frontend Server"
    gnome-terminal --tab --title="Frontend Server" -- bash -c "
    cd ~/HanabiBackend/pythonProject/web-hanabi
    node server.js $arg &
    echo \$! > /tmp/hanabi_project_server_pid
    while true; do sleep 1; done
    " &

    # Open the second terminal in a new tab with the title "Backend Server"
    gnome-terminal --tab --title="Backend Server" -- bash -c "
    cd ~/HanabiBackend/pythonProject/web-hanabi-backend
    node backend-server.js $arg &
    echo \$! > /tmp/hanabi_project_backend_server_pid
    while true; do sleep 1; done
    " &
fi

# Wait for background processes to start
sleep 1

printf '\nPress Ctrl+C or type "q" to stop the processes...\n\n'

# Monitor the processes
while true; do
    if [ -f /tmp/hanabi_project_server_pid ]; then
        SERVER_PID=$(cat /tmp/hanabi_project_server_pid)
        if ! kill -0 $SERVER_PID 2>/dev/null; then
            echo "server.js has terminated"
            kill_processes
            break
        fi
    fi
    if [ -f /tmp/hanabi_project_backend_server_pid ]; then
        BACKEND_SERVER_PID=$(cat /tmp/hanabi_project_backend_server_pid)
        if ! kill -0 $BACKEND_SERVER_PID 2>/dev/null; then
            echo "backend-server.js has terminated"
            kill_processes
            break
        fi
    fi

    # Check for user input with a timeout
    read -t 1 -n 1 key
    if [ "$key" = "q" ]; then
        printf "\n\nQuit command received. "
        kill_processes
        break
    fi
done

# Terminate the main script
exit 0

