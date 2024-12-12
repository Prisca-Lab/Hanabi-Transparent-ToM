
// Importa e configura dotenv
require('dotenv').config({path:__dirname+'/../properties.env'}); // npm install dotenv

// Leggi la variabile d'ambiente
const hostLocalIp = process.env.BACKEND_HOST_IP;  // To set this, use the command 'hostname -I | cut -d' ' -f1' in a Linux terminal
const port = process.env.BACKEND_HOST_PORT;

// console.log(`BACKEND_HOST_IP: ${hostLocalIp}`);
// console.log(`BACKEND_HOST_PORT: ${port}`);


// Check for the gameChoice parameter
const gameChoice = process.argv[2];

if (!gameChoice || !['tom', 'tom_human'].includes(gameChoice.toLowerCase())) {
    console.error('Error: gameChoice parameter is required and must be either "ToM" or "ToM_Human" (case insensitive).');
    process.exit(1);
}

const express = require('express');
const bodyParser = require('body-parser');
const app = express();

// Middleware per il parsing del corpo delle richieste JSON
app.use(bodyParser.json());

// Middleware per aggiungere le intestazioni CORS
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*"); // Permetti tutte le origini, oppure specifica un dominio esatto
    res.header("Access-Control-Allow-Methods", "GET,HEAD,OPTIONS,POST,PUT");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept, Authorization, socket-id");
    next();
});

// Mazzo di default
let customDeck = [
    /*
    {"color": 'yellow', "number": 1, "impossible": {}},  // Carta G1
    {"color": 'yellow', "number": 1, "impossible": {}},  // Carta G1
    {"color": 'yellow', "number": 4, "impossible": {}},  // Carta G1
    {"color": 'red', "number": 3, "impossible": {}},     // Carta G1
    {"color": 'red', "number": 4, "impossible": {}},     // Carta G1

    {"color": 'red', "number": 2, "impossible": {}},     // Carta G2
    {"color": 'yellow', "number": 5, "impossible": {}},  // Carta G2
    {"color": 'red', "number": 1, "impossible": {}},     // Carta G2
    {"color": 'red', "number": 4, "impossible": {}},     // Carta G2
    {"color": 'yellow', "number": 3, "impossible": {}},  // Carta G2

    {"color": 'yellow', "number": 1, "impossible": {}},  // Deck
    {"color": 'red', "number": 2, "impossible": {}},     // Deck
    {"color": 'red', "number": 5, "impossible": {}},     // Deck
    {"color": 'yellow', "number": 4, "impossible": {}},  // Deck
    {"color": 'red', "number": 1, "impossible": {}},     // Deck
    {"color": 'red', "number": 3, "impossible": {}},     // Deck
    {"color": 'yellow', "number": 2, "impossible": {}},  // Deck
    {"color": 'red', "number": 1, "impossible": {}},     // Deck
    {"color": 'yellow', "number": 3, "impossible": {}},  // Deck
    {"color": 'yellow', "number": 2, "impossible": {}}   // Deck
    */
];

let p1cards = null, p2cards = null;
let last_action_player_0 = null, last_action_player_1 = null;

/*
p1cards = [
    {"color": 'yellow', "number": 1, "impossible": {}},  // Carta G1
    {"color": 'yellow', "number": 1, "impossible": {}},  // Carta G1
    {"color": 'yellow', "number": 1, "impossible": {}},  // Carta G1
    {"color": 'red', "number": 1, "impossible": {}},     // Carta G1
    {"color": 'red', "number": 1, "impossible": {}},     // Carta G1
];
p2cards = [
    {"color": 'red', "number": 2, "impossible": {}},     // Carta G2
    {"color": 'yellow', "number": 2, "impossible": {}},  // Carta G2
    {"color": 'red', "number": 2, "impossible": {}},     // Carta G2
    {"color": 'red', "number": 2, "impossible": {}},     // Carta G2
    {"color": 'yellow', "number": 2, "impossible": {}},  // Carta G2
];
 */

// Endpoint GET per ottenere il custom deck
app.get('/get_custom_deck', async (req, res) => {
    // Attendi che le carte del giocatore siano impostate
    while (customDeck.length === 0) {
        await new Promise(resolve => setTimeout(resolve, 200)); // Attendi 200ms
    }

    res.json(customDeck);
});

// Endpoint POST per impostare il custom deck
app.post('/set_custom_deck', (req, res) => {
    customDeck = req.body;
    res.send('Custom deck impostato con successo.');
});

// Endpoint POST per impostare le carte dei giocatori
app.post('/set_cards', (req, res) => {
    /*
    me.hand:  [
      { color: 'yellow', number: 1, impossible: {} },
      { color: 'red', number: 5, impossible: {} },
      { color: 'yellow', number: 3, impossible: {} },
      { color: 'yellow', number: 4, impossible: {} },
      ...
    ]
     */

    // Estrai le carte dal corpo della richiesta
    // console.log('req.body = ', req.body)
    const { p1cards: player1Cards, p2cards: player2Cards, currPlayer } = req.body;

    if(currPlayer === 0)
        p1cards = player1Cards;
    else
        p2cards = player2Cards;

    console.log('Carte del giocatore ', currPlayer, ' aggiornate con successo.');

    // Invia una risposta di conferma
    res.send('Carte del giocatore ', currPlayer, ' aggiornate con successo.');
});

function waitForLastAction(player) {
    return new Promise((resolve) => {
        const interval = setInterval(() => {
            if (player === 0 && last_action_player_0 !== null) {
                clearInterval(interval);
                resolve();
            } else if (player === 1 && last_action_player_1 !== null) {
                clearInterval(interval);
                resolve();
            }
        }, 300); // Controlla ogni 300 ms
    });
}

// Endpoint GET per ottenere le carte aggiornate dei giocatori
app.get('/get_cards', async (req, res) => {
    // Recupera il parametro currPlayer dalla richiesta
    const currPlayer = req.query.currPlayer;
    console.log('Il giocatore ', currPlayer, ' mi ha richiesto get_cards');
    console.log('p1cards = ', p1cards, ', p2cards = ', p2cards)

    // Attendi che le carte del giocatore siano impostate
    while ((currPlayer === '0' && p1cards === null) || (currPlayer === '1' && p2cards === null)) {
        await new Promise(resolve => setTimeout(resolve, 150)); // Attendi 150ms
    }

    let json_res;

    // Prepara la risposta in base al giocatore corrente
    if (currPlayer === '0') {
        json_res = { 'p1cards': p1cards };
        p1cards = null; // Resetta le carte del giocatore 0
    } else {
        json_res = { 'p2cards': p2cards };
        p2cards = null; // Resetta le carte del giocatore 1
    }

    console.log('Ora rispondo al giocatore', currPlayer, 'mandandogli ', json_res);
    res.json(json_res);
});

// Endpoint POST per impostare l'azione eseguita nel caso di gioco "tom_human"
app.post('/set_last_action', (req, res) => {
    const {player, action} = req.body;
    if (player === 0) {
        last_action_player_0 = action;
    } else if (player === 1) {
        last_action_player_1 = action;
    }
    console.log(`Azione ricevuta dal giocatore ${player}:`, action);
    res.send('Azione ricevuta con successo.');
});


// Se G1 vuole darmi la sua azione, allora quella di G2 deve essere null (cioè già stata recuperata).
// Se G2 vuole darmi la sua azione, allora quella di G1 deve essere null.
// Per far funzionare questa logica, G1 deve essere sempre il primo a comunicarmi la sua azione.
function waitForActionToBeNull(player, callback) {
    const checkInterval = 100; // intervallo di controllo in millisecondi
    const checkAction = () => {
        if ((player === 0 && last_action_player_1 === null) || (player === 1 && last_action_player_0 === null)) {
            callback();
        } else {
            setTimeout(checkAction, checkInterval);
        }
    };
    checkAction();
}

let isBoardLoaded = false;

function waitForBoardToBeReady() {
    return new Promise((resolve) => {
        const checkInterval = 300;
        const checkBoardStatus = () => {
            if (isBoardLoaded === true) {
                resolve();  // Resolve the promise when the board is ready
            } else {
                setTimeout(checkBoardStatus, checkInterval);
            }
        };
        checkBoardStatus();
    });
}

app.get('/wait_for_board', async (req, res) => {
    console.log('Waiting for board status...');
    await waitForBoardToBeReady();
    console.log('Wait is over! Board is ready.');

    // Respond with 204 No Content
    res.status(204).send();
});

// Endpoint POST per impostare l'azione eseguita nel caso di gioco "tom"
app.post('/set_last_action_tom', (req, res) => {
    const { player, action } = req.body;
    waitForActionToBeNull(player, () => {
        if (player === 0) {
            last_action_player_0 = action;
            // Per sicurezza:
            last_action_player_1 = null;
        } else if (player === 1) {
            last_action_player_1 = action;
            // Per sicurezza:
            last_action_player_0 = null;
        }
        console.log(`Azione ricevuta dal giocatore ${player}:`, action);
        res.send('Azione ricevuta con successo.');
    });
});

app.post('/set_board_ready', (req, res) => {
    isBoardLoaded = true;

    console.log('Stato board ricevuto con successo');
    res.send('Stato board ricevuto con successo.');
});

// Endpoint GET per ottenere l'ultima azione fatta
//  1. umano + robot: parte il server che si mette in attesa su /get_last_action e parte il client che fa
//    /set_last_action per l'azione dell'umano, poi appena lo fa, il server la recupera e la leva dal backend.
//    Poi contemporaneamente il client si è messo in attesa su /get_last_action e aspetta l'azione del ToM. Il server
//    quindi comunica su /set_last_action l'azione di ToM e il client se la prende, e il server si rimette in attesa.
//  2. robot + robot: /set_last_action per dire l'azione di ToM1 al client, il client fa /get_last_action e si mette
//    in attesa fino a quando non arriva la prima mossa. Poi, appena la prende, si rimette in attesa su /get_last_action.
//    per la mossa di ToM2, e così via. Ogni volta che si fa la get si rimuove last_action dal backend.
app.get('/get_last_action', async (req, res) => {
    const player = parseInt(req.query.player, 10);
    console.log('Someone asked for player', player, 'last action. Waiting for last action...')

    await waitForLastAction(player);
    console.log('Wait is over! - This is from \'Someone asked for player\'', player, 'last action')

    let action = null;
    if (player === 0) {
        action = last_action_player_0;
        last_action_player_0 = null;
    } else if (player === 1) {
        action = last_action_player_1;
        last_action_player_1 = null;
    }

    res.json(action);
});

// Avvio del server
const server = app.listen(Number(port), hostLocalIp, () => {
    console.log(`Backend server is running on http://${hostLocalIp}:${port}`);
});

let shutdownRequests = new Set();

// Endpoint per lo shutdown del server
app.post('/shutdown', (req, res) => {
    const socketId = req.headers['socket-id']; // Assumi che l'ID del socket sia passato nell'header della richiesta

    if (!shutdownRequests.has(socketId)) {
        shutdownRequests.add(socketId);

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
                console.log('Backend server terminated successfully.');
                process.exit(0);
            });
        }
    } else {
        res.send('Shutdown request already received from this socket ID.');
    }
});