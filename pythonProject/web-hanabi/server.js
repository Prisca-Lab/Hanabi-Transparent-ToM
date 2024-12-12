/*
 * Basic Node.js express server that runs a socket.io instance
 * to mirror all data sent by one client to all others (in the same
 * socket.io room)
 */


// Check for the gameChoice parameter
const gameChoice = process.argv[2];

if (!gameChoice || !['tom', 'tom_human'].includes(gameChoice.toLowerCase())) {
    console.error('Error: gameChoice parameter is required and must be either "ToM" or "ToM_Human" (case insensitive).');
    process.exit(1);
}


/*
 * Helper Functions
 */
function extend(a,b) {
    let k;
    for (k in b) {
        a[k] = b[k];
    }
    return a;
}


// Preliminaries
require('dotenv').config({path:__dirname+'/../properties.env'});
var express = require('express');
const axios = require('axios');
var app = express();
var http = require('http');
var server = http.createServer(app);
var io = require('socket.io').listen(server);
var game_init = require('./public/js/game_init');
io.set('log level', 1) // reduce the debug messages

// Leggi la variabile d'ambiente
const hostIp = process.env.FRONTEND_HOST_IP;  // To set this, use the command 'curl ifconfig.me' in a Linux terminal
const port = process.env.FRONTEND_HOST_PORT;
const backendIp = process.env.BACKEND_HOST_IP;
const backendPort = process.env.BACKEND_HOST_PORT;
const backendEndpoint = 'http://' + backendIp + ':' + backendPort;
console.log('dir is:', __dirname+'/../properties.env')
console.log('hostIp:', hostIp, ', port:', port)

// console.log(`FRONTEND_HOST_IP: ${hostIp}`);
// console.log('FRONTEND_HOST_PORT IS:', port)

// Middleware per aggiungere le intestazioni CORS
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*"); // Permetti tutte le origini, oppure specifica un dominio esatto
    res.header("Access-Control-Allow-Methods", "GET,HEAD,OPTIONS,POST,PUT");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization, socket-id");
    next();
});

// Statically server pages from the public directory
app.use(express.static(__dirname + '/public'));

// Start the server
server.listen(Number(port), hostIp, () => {
    console.log(`Server listening on ${hostIp}:${port}`);
});

// global data about the game for a room
var gamesList = {};
let boardSocket = null;
let shutdownRequests = new Set();

// Endpoint per lo shutdown del server
app.post('/shutdown', (req, res) => {
    const socketId = req.headers['socket-id'];

    if (!shutdownRequests.has(socketId)) {
        shutdownRequests.add(socketId);

        // Disconnetti immediatamente la socket che ha fatto la richiesta
        const socket = io.sockets.sockets[socketId];
        if (socket) {
            socket.disconnect(true);
            console.log(`Socket ID ${socketId} disconnected.`);
        }

        if (shutdownRequests.size === 1) {
            console.log('First shut down request received from socket ID:', socketId);
            res.send('First shut down request received...');
        } else if (shutdownRequests.size === 2) {
            console.log('Second shut down request received from socket ID:', socketId);
            res.send('Second shut down request received...');
        } else if (shutdownRequests.size === 3) {
            console.log('Third shut down request received from a different socket ID, proceeding with termination...');
            res.send('Shutting down the server...');
            server.close(() => {
                console.log('Frontend server terminated successfully.');
                process.exit(0);
            });

            // Chiudiamo anche tutte le socket aperte rimanenti
            Object.values(io.sockets.sockets).forEach(socket => {
                socket.disconnect(true);
            });
        }
    } else {
        res.send('Shutdown request already received from this socket ID.');
    }
});


let player0_me = null;
let player0_id = null;
let player0_room = null;
let player0_socket = null;

// Handle all the websocket connections
io.sockets.on('connection', function(socket) {
    // initialize the socket object to store some persistent data
    socket.hanabiData = {persistentId: socket.id};
    socket.terminated = false;

    /*
     * Helper Functions
     */

    // return information on all clients in a particular room.
    //      roomList: list of all rooms on the server
    //      clientList: list of objects, each containing the name of
    //                  the client and a unique identifier for that
    //                  client (which can be used to identify yourself)
    function getRoomInfo (room) {
        const clientList = [];
        for (let i = 0, clients = io.sockets.clients(room); i < clients.length; i++) {
            clientList.push({name: clients[i].hanabiData.name, id: clients[i].id, data: clients[i].hanabiData});
        }

        return {
            roomList: Object.keys(io.sockets.manager.rooms),
            clients: clientList,
        };
    }

    function informRoomOfChange (room) {
        if (room == null) {
            return;
        }
        // loop through all clients in this room and push them updated info
        // about th people in their room
        var info = getRoomInfo(room)
        for (var i = 0, clients = io.sockets.clients(room); i < clients.length; i++) {
            clients[i].emit('room-info', info);
        }

    }
    function isRoomReady(room){
        for (var i = 0, clients = io.sockets.clients(room); i < clients.length; i++) {
        if (!clients[i].hanabiData.readyState) {
            return false;
        }
        }
    return true;
    }

    socket.on('i-am-board', function() {
        boardSocket = socket;
    });

    socket.on('game-update-board', function (game, me, meId) {
        console.log('Someone tried to call game-update-board');
        if(boardSocket !== null) {
            console.log('Performing update-data-board');
            boardSocket.emit('update-data-board', game, me, meId, '15');
        }
    });


    /*
     * Event handlers
     */

    socket.on('disconnect', function () {
        console.log('Disconnecting Client', socket.hanabiData.currentRoom);
        // force ourselves to leave the room before the room
        // statistics get broadcast to the other people in the room!
        if (socket.hanabiData.currentRoom) {
            socket.leave(socket.hanabiData.currentRoom);
        }
        informRoomOfChange(socket.hanabiData.currentRoom);
    });

    // rooms allow us to limit our broadcasts to others in the same room.
    socket.on('set-room', function(room) {
        console.log('Joining room', room);
        // leave any previous room we may have been in
        if (socket.hanabiData.currentRoom) {
            socket.leave(socket.hanabiData.currentRoom);
        }
        socket.join(room);

        var oldRoom = socket.hanabiData.currentRoom;
        socket.hanabiData.currentRoom = room;
        // inform about our room change
        // to both the old room and the new room
        if (oldRoom) {
            informRoomOfChange(oldRoom);
        }
        if (oldRoom != room) {
            informRoomOfChange(room)
        }
    });
    socket.on('query-room', function (room) {
        console.log('Querying room', room);
        socket.emit('room-info', getRoomInfo(room));
    });
    socket.on('query-id', function () {
        socket.emit('id-info', {name: socket.hanabiData.name, id: socket.id, currentRoom: socket.hanabiData.currentRoom, persistentId: socket.hanabiData.persistentId});
    });
    socket.on('assert-id', function (data) {
        socket.hanabiData.persistentId = data.persistentId;
    });

    // set a new name for the client
    socket.on('set-name', function (name) {
        console.log('Setting name from', socket.hanabiData.name, ' to ', name);
        socket.hanabiData.name = name;
        informRoomOfChange(socket.hanabiData.currentRoom);
    });

    // set a new data for the client
    socket.on('set-data', async (data) => {
        console.log('Setting data', data);
        extend(socket.hanabiData, data);
        var room = socket.hanabiData.currentRoom;
        informRoomOfChange(room);
        if (isRoomReady(room)) {
            try {
                const endpoint = hostIp === 'localhost' ? 'http://127.0.0.1:'+backendPort : backendEndpoint;
                const response = await axios.get(`${endpoint}/get_custom_deck`);
                const customDeck = response.data;
                // console.log("Custom deck is: ", customDeck)
                var newGame = game_init.createNewGame(getRoomInfo(room).clients.length, customDeck);
                for (var i = 0, clients = io.sockets.clients(room); i < clients.length; i++) {
                    newGame.players[i].id = clients[i].hanabiData.persistentId;
                    newGame.players[i].name = clients[i].hanabiData.name;
                }
                newGame.room = room;
                gamesList[room] = newGame;
                socket.in(room).broadcast.emit('new-game', newGame);
                socket.emit('new-game', newGame);
            }
            catch (error) {
                console.error('Error fetching customDeck:', error);
            }
        }
    });

    // when new data is broadcast by a client, emit it to all
    // other clients in the same room
    socket.on('broadcast', function (data) {
        console.log('Got message to retransmit', data, 'room: ', socket.hanabiData.currentRoom);
        const room = socket.hanabiData.currentRoom;
        // everyone in the same room as the broadcaster will get the data
        // relayed to them
        socket.in(room).broadcast.emit('message', {message: data, senderId: socket.id});
    });

    //sends the game object back on the request to start a new game.
    socket.on('start-game', function(){
        player0_room = socket.hanabiData.currentRoom;
        const room = player0_room;
        console.log("starting game in room", room);

        const games_list_room = gamesList[room];
        games_list_room.gameChoice = gameChoice;

        const endpoint =  'http://' + hostIp + ':' + port;
        socket.emit('set-endpoints', endpoint, backendEndpoint)
        socket.emit('update-data', games_list_room, '0', (response) => {});
    });

    socket.on('set-player0', function (me, myId) {
        console.log('è stato chiamato set-player0')
        if(player0_id === null) {
            player0_id = myId;
            player0_socket = socket;
            player0_me = me;

            // console.log('player0_socket =', player0_socket)
            console.log('player0_me =', player0_me);
            console.log('player0_id =', player0_id)
        }
    });

    socket.on('get-game-choice', function () {
        socket.emit('set-game-choice', gamesList[player0_room].gameChoice.toString());
    });

    socket.on('get-endpoints', function() {
        const endpoint =  'http://' + hostIp + ':' + port;
        socket.emit('set-endpoints', endpoint, backendEndpoint)
    });

    socket.on('end-game', function(game, invokingPlayer, callback) {
        socket.terminated = true;
        const currPlayer = invokingPlayer === 1 ? 0 : 1;

        Object.values(io.sockets.sockets).forEach(socket_ => {
            if(socket_.id !== socket.id && !socket_.terminated) {
                socket_.terminated = true;
                socket_.emit('endgame', game, currPlayer);
            }
        });

        callback({
          status: "ok"
        });
    });

    socket.on('pass-tom-human-action-to-player0', function (game) {
        player0_socket.emit('do-tom-human-action', game);
    });

    socket.on('pass-tom-human-myhand-action-to-player0', function (game, instructionType, cardIndex) {
        console.log('do-tom-human-myhand-action'); //, player0_socket =', player0_socket);
        player0_socket.emit('do-tom-human-myhand-action', game, instructionType, cardIndex);
    });

    socket.on('set-board-ready', function () {
        axios.post(`${backendEndpoint}/set_board_ready`)
        .then(response => {
            console.log('Aggiornamento stato board effettuato correttamente.')
        })
        .catch(error => {
            console.error('Errore durante la comunicazione con il backend:', error);
        });
    });

    socket.on('request-first-game-update-board', function (callback) {
        const game = gamesList[player0_room];
        boardSocket.emit('update-data-board', game, player0_me, player0_id, '16');
    });

    socket.on('game-server-update', function(game, callback){
        const room = socket.hanabiData.currentRoom;
        gamesList[room] = game;

        callback({
          status: "ok"
        });
    });

    socket.on('game-update', function(game){
        const room = socket.hanabiData.currentRoom;
        gamesList[room] = game;

        const games_list_room = gamesList[room];
        games_list_room.gameChoice = gameChoice;

        Object.values(io.sockets.sockets).forEach(socket_ => {
            if(socket_.id !== socket.id) {
                socket_.emit('update-data', games_list_room, '2', (response) => {});
            }
        });
    });

    socket.on('game-update-myself-too', function(game, callback){
        const room = socket.hanabiData.currentRoom;
        gamesList[room] = game;

        const games_list_room = gamesList[room];
        games_list_room.gameChoice = gameChoice;

        socket.emit('update-data', games_list_room, '5', (response) => {
            const room = socket.hanabiData.currentRoom;
            const game_ = gamesList[room]

            // Verifico a quale socket comunicare l'azione, ossia la socket diversa dal chiamante di qui
            const socket0ID = Object.keys(io.sockets.sockets)[0];
            const socket1ID = Object.keys(io.sockets.sockets)[1];
            const socketIdDest = socket0ID === socket.id ? socket1ID : socket0ID;
            io.sockets.sockets[socketIdDest].emit('update-data', game_, '7', (response) => {});
        });

        callback({
          status: "ok"
        });
    });

    socket.on('game-update-first-others-then-myself', function(game, callback){
        const room = socket.hanabiData.currentRoom;
        gamesList[room] = game;

        const games_list_room = gamesList[room];
        games_list_room.gameChoice = gameChoice;

        // Verifico a quale socket comunicare l'azione, ossia la socket diversa dal chiamante di qui
        const socket0ID = Object.keys(io.sockets.sockets)[0];
        const socket1ID = Object.keys(io.sockets.sockets)[1];
        const socketIdDest = socket0ID === socket.id ? socket1ID : socket0ID;

        io.sockets.sockets[socketIdDest].emit('update-data', game, '9', (response) => {
            /*
            In teoria non occorre questo aggiornamento, dato che questo scenario è per quando si sta
            solamente aggiornando la grafica, quindi si assume che l'altra socket non effettui modifiche al game...

            const room = socket.hanabiData.currentRoom;
            const game_ = gamesList[room]
            */
            socket.emit('update-data', games_list_room, '10', (response_) => {
                callback({
                  status: "ok"
                });
            });
        });
    });

    socket.on('update-last-action', function(data) {
        const instructionType = data.instructionType;
        const info = data.info;
        const currPlayer = data.currentPlayer;

        console.log('Sono il frontend e ora comunico la mossa', instructionType, '', info, 'del giocatore ', currPlayer)

        // Comunica l'azione al backend
        axios.post(`${backendEndpoint}/set_last_action`, {
            player: currPlayer,
            action: {
                instructionType: instructionType,
                info: info
            }
        })
        .then(response => {
            console.log('Azione comunicata al backend con successo:', response.data);
        })
        .catch(error => {
            console.error('Errore durante la comunicazione con il backend:', error);
        });
    });

    socket.on('get-last-action', async function(other, otherPlayerId) {
        try {
            const endpoint = hostIp === 'localhost' ? 'http://127.0.0.1:'+backendPort : backendEndpoint;
            const response = await axios.get(`${endpoint}/get_last_action`, {
                params: {
                    player: otherPlayerId
                }
            });
            console.log("Server.js, response.data = ", response.data, ', fatta dal giocatore ', otherPlayerId);
            // Invia i dati ottenuti al giocatore interessato:
            // console.log('La socket corrente per get-last-action-client è ', socket.id);
            // console.log('io.sockets.sockets = ', io.sockets.sockets);

            const game_ = gamesList[socket.hanabiData.currentRoom];

            // console.log('Game dal server: ', game_)
            let others = [];
            for (var i = 0; i < game_.players.length; i++) {
                if (game_.players[i].id === other.id) {
                    //others is now a list of the index of the player in the array of game_.players
                    others.push(game_.players[i]);
                }
            }
            other = others[0];

            // Verifico a quale socket comunicare l'azione, ossia la socket diversa dal chiamante di qui
            const socket0ID = Object.keys(io.sockets.sockets)[0];
            const socket1ID = Object.keys(io.sockets.sockets)[1];
            if(socket0ID === socket.id) {
                // console.log('Mando a socket1ID: ', socket1ID)
                io.sockets.sockets[socket1ID].emit('get-last-action-client', game_, other, response.data);
            } else {
                // console.log('Mando a socket0ID: ', socket0ID)
                io.sockets.sockets[socket0ID].emit('get-last-action-client', game_, other, response.data);
            }
        } catch (error) {
            console.error('Error fetching last action:', error);
        }
    });

    socket.on('get-last-action-and-do-it-by-myself', async function(game, me, myId) {
        try {
            const endpoint = hostIp === 'localhost' ? 'http://127.0.0.1:'+backendPort : backendEndpoint;
            const response = await axios.get(`${endpoint}/get_last_action`, {
                params: {
                    player: myId
                }
            });
            console.log('Siamo in get-last-action-and-do-it-by-myself')
            console.log("Server.js, response.data = ", response.data, ', fatta dal giocatore ', myId);

            socket.emit('get-last-action-client-final-move', game, me, response.data);
        } catch (error) {
            console.error('Error fetching last action:', error);
        }
    });

    socket.on('get-cards', async function(game, me, instructionType, playedCard, isPlayed, currPlayer) {
        try {
            console.log('Backend: giocatore ', currPlayer, ' ha richiesto get-cards...')
            const endpoint = hostIp === 'localhost' ? 'http://127.0.0.1:'+backendPort : backendEndpoint;
            const response = await axios.get(`${endpoint}/get_cards`, {
                params: {
                    currPlayer: currPlayer
                }
            });

            console.log("get-cards: Server.js, response.data = ", response.data);
            // Invia i dati ottenuti
            socket.emit('get-cards-client', response.data, game, me, instructionType, playedCard, isPlayed, currPlayer);
        } catch (error) {
            console.error('Error fetching cards:', error);
        }
    });
});