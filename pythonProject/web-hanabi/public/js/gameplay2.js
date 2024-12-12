'use strict';

// determines whether the cards in your hand are blank or shown.
var showCards = false;
var lobbyUrl = "/tests/lobby.html";
var game = null;

//decode the URI to get player information
function parseUriSearchString(str) {
    // Remove leading questionmark
    if (str.charAt(0) == '?') {
        str = str.slice(1);
    }

    // Split up strings in the form of "foo=bar&baz=bat" into
    // objects {foo: 'bar', baz: 'bat'}
    var ret = {}
    str.split('&').forEach(function (s) {
        var vals = s.split('=');
        ret[decodeURI(vals[0] || '')] = decodeURI(vals[1] || '');
    });
    return ret;
}

function extend(a, b) {
    var i;
    for (i in b) {
        a[i] = b[i];
    }
}

function capitalize(w) {
    return w.charAt(0).toUpperCase() + w.slice(1);
}

// take an object a and give it a key for
// every item in arr and set the corresponding key to
// true
function extendByArray(a, arr) {
    var i;
    for (i = 0; i < arr.length; i++) {
        a[arr[i]] = true;
    }
}

//add an event lister if none exists otherwise do nothing
function initializeListener(obj, type, callback, prevCallback) {
    if(prevCallback !== null)
        removeListener(obj, type, prevCallback)

    if (!obj.getAttribute('x-callback')) {
        obj.addEventListener(type, callback);
        obj.setAttribute('x-callback', 1);
        obj.listener = callback;
    }
}

//if an event lister exists remove it from the object
function removeListener(obj, type, prevCallback) {
    if (obj.getAttribute('x-callback')) {
        obj.removeAttribute('x-callback');
        obj.removeEventListener(type, prevCallback);
        obj.listener = null;
    }
}

// returns a list of classes corresponding to
// what is known about this card
function getKnowledgeClasses(card) {
    var possibleKnowledge = ['red', 'yellow', 1, 2, 3, 4, 5];
    var ret = [];
    for (var i = 0; i < possibleKnowledge.length; i++) {
        var possibility = possibleKnowledge[i];
        if (!card.impossible[possibility]) {
            ret.push("maybe-" + possibility);
        }
    }
    return ret;
}

// Funzione per chiudere i server frontend e backend
function shutdownServers(game, socket, invokingPlayer) {
    const headers = new Headers({
        'Content-Type': 'application/json',
        'socket-id': socket.socket.sessionid
    });
    const init = {
        method: 'POST',
        headers: headers
    }

    console.log('Socket =', socket, ', socket.id =', socket.socket.sessionid)

    socket.emit('end-game', game, invokingPlayer, (response) => {
        // Chiudiamo il server per il frontend
        fetch(`${endpoint}/shutdown`, init)
        .then(response => {
            if (response.ok) {
                console.log('Richiesta di spegnimento server frontend inviata con successo.');
            } else {
                console.error('Errore durante la richiesta di spegnimento server frontend:', response.status);
            }
        })
        .catch(error => {
            console.error('Errore durante la richiesta di spegnimento server frontend:', error);
        });

        // Chiudiamo il server per il backend
        fetch(`${backendEndpoint}/shutdown`, init)
        .then(response => {
            if (response.ok) {
                console.log('Richiesta di spegnimento server backend inviata con successo.');
            } else {
                console.error('Errore durante la richiesta di spegnimento server backend:', response.status);
            }
        })
        .catch(error => {
            console.error('Errore durante la richiesta di spegnimento server backend:', error);
        });
    });
}


// end the game shows the score and allows quick access to the lobby
function endGame(game, socket, invokingPlayer) {
    console.log('endGame was called...')
    const messageDiv = document.querySelector('#messages');

    messageDiv.innerHTML = "<p>End of Game! You got " + game.score + " points!</p>"
    messageDiv.setAttribute('style', '');

    // Disable all buttons and controls
    const allButtons = document.querySelectorAll('[x-button]');
    allButtons.forEach(button => {
        button.classList.add('disabled');
        button.style.pointerEvents = 'none';
    });

    const allHands = document.querySelectorAll('.hand');
    allHands.forEach(hand => {
        hand.style.pointerEvents = 'none';
    });

    // Hide the instruction menus
    const instructions = document.querySelectorAll('.instruction');
    instructions.forEach(instruction => {
        instruction.setAttribute('style', 'display: none;');
    });

    shutdownServers(game, socket, invokingPlayer);
}

// records a move in the game log, also sets the game log to the move that is being logged.
function logMove(game, name, instruction, numberColor, isPlayed, other) {
    if (other) {
        var s = name + " told <i>" + other + "</i> about their <span class='"+numberColor+"'>" + numberColor + "</span>'s";
    } else {
        var type = instruction == "discard-card" ? "discard" : "card";
        if (type == "discard") {
            var s = name + ' ' + type + "ed a <span class='"+numberColor+"'>" + numberColor + "</span>";
        } else {
            s = name + " tried to play a <span class='"+numberColor+"'>" + numberColor + "</span> and was "
            s += isPlayed ? "" : "<b>not</b> ";
            s += "successful";
        }
    }
    game.lastAction = s;
    game.gameLog.push(s);
}

// places a message in the message div, displays it and sets up a click event to return to the game
function displayMessage(messageDiv, message) {
    messageDiv.innerHTML = "<p>" + message + "</p>"
    messageDiv.setAttribute('style', '');
    messageDiv.addEventListener('click', function (e) {
        messageDiv.setAttribute('style', 'display: none;');
    });
}

let firstTimePlayer0Update = true;
let p0startedGetLastAction = false;
// Siccome quando rimuovo un listener ho bisogno del ref alla funzione precedente, uso queste variabili
let prevInstructionButtonEnter = null;
let prevReEmphasizeAllCards = null;
let prevClickedOnOther = null;
let prevInstructionClick = null;
let prevClickedMyHand = null;
let prevMyHandClick = null;
// let requestedEndGame = false;
let finishingPlayerSecondPlay = false;

const updateScreenHelperFunction = function(game, others, me, socket, currPlayerId, myId, ignoreEndGame) {
    let myHandButtons;
    const gameChoice = game.gameChoice.toLowerCase();

    let i;
    // clear the screen of all information
    const cardLists = document.querySelectorAll('.card-list');
    for (i = 0; i < cardLists.length; i++) {
        cardLists[i].innerHTML = "";
    }
    const messageDiv = document.querySelector('#messages');
    messageDiv.setAttribute('style', 'display: none;');
    messageDiv.innerHTML = '';

    // hide the buttons, the first one found will be the instructions to move around
    // XXX Fix this, this relies on the other's instruction being before #my-hand .instructions
    const knowledgeButtons = document.querySelector('.instruction');
    knowledgeButtons.setAttribute('style', 'display: none;');
    console.log('Il giocatore', me.name, 'ora imposta', others[0].name, 'come il current player')

    const currPlayer = me.id === game.players[0].id ? 0 : 1;
    // setup all other player's hands
    for (i = 0; i < others.length; i++) {
        var handDiv = document.querySelector("#hand" + i);
        // Se sono il giocatore 0, la prima volta devo giocare io e non devo impostare G1 come current player
        if(currPlayer === 0 && firstTimePlayer0Update === true) {
            firstTimePlayer0Update = false;
        }
        else {
            if (others[i].id == currPlayerId) {
                handDiv.classList.add('current-player');
            } else {
                handDiv.classList.remove('current-player');
            }
        }

        setupHand(others[i].hand, handDiv.querySelector('.card-list'), i);
        handDiv.querySelector('.player-name').textContent = others[i].name;
    }

    if(isBoard === 'true') {
        // set up our own hand
        handDiv = document.querySelector("#my-hand")
        if (myId == currPlayerId) {
            handDiv.classList.add('current-player');
        } else {
            handDiv.classList.remove('current-player');
        }

        setupMyHand(me.hand, handDiv.querySelector('.card-list'), showCards);

        // setup heart
        document.querySelector('#hearts-display').textContent = game.hearts;
        // setup clues
        document.querySelector('#clue-display').textContent = game.clueTokens;
        // setup deck
        document.querySelector('#deck-display').textContent = game.deck.length;
        // setup log
        const logUl = document.querySelector('#log ul');
        logUl.innerHTML = "<li>" + game.gameLog.join('</li><li>') + "</li>";
        handDiv.querySelector('.player-name').textContent = me.name;
    }


    console.log('Sono in updateScreenHelper, game =', game)

    if(!ignoreEndGame) {
        if(game.hearts === 0) {
            console.log('Sono in game.hearts === 0')
            if(isBoard === 'true') {
                discard = document.querySelector("#discard");
                tableau = document.querySelector("#tableau");
                document.querySelector('#deck-display').textContent = game.deck.length;
                setupTableau(game, discard, tableau);
            }

            endGame(game, socket, currPlayer);
            return;
        }

        // end the game if there are no hearts or if this is the final round of play
        if (game.finishingPlayerId === currPlayer && finishingPlayerSecondPlay === true) {
            console.log('Sono in game.finishingPlayerId === currPlayer && finishingPlayerSecondPlay === true')

            if(isBoard === 'true') {
                discard = document.querySelector("#discard");
                tableau = document.querySelector("#tableau");
                document.querySelector('#deck-display').textContent = game.deck.length;
                setupTableau(game, discard, tableau);
            }

            console.log('Ho fatto endgame');
            endGame(game, socket, currPlayer);
            return;
        } else if (game.finishingPlayerId === currPlayer) {
            console.log('Init: finishingPlayerSecondPlay = true')
            finishingPlayerSecondPlay = true;
        }

        // end the game after one more round if there are no more cards in the deck
        // if the finalRound is not defined and there are no more cards set the final round
        if (!game.finalRound && game.deck.length === 0) {
            // game.finishingPlayer = game.currentPlayer;
            game.finishingPlayerId = currPlayer;
            game.finalRound = true;

            if(isBoard === 'true') {
                var message = "This is the final Round, only one turn left";
                console.log('Ora faccio display message su messageDiv =', messageDiv)
                displayMessage(messageDiv, message);
            }

            console.log('Ora game.finalRound = true, faccio game-server-update');
            socket.emit('game-server-update', game, (response) => {});
        }
    }

    if(gameChoice === "tom_human") {
        // click listener for others' hands.  This pops up the
        // menu where you can choose what information to give
        if(isBoard === 'false') {
            var clickedOnOther = function (e) {
                reEmphasizeAllCards();
                if (currPlayerId != myId) {
                    return;
                }
                var target = e.target;
                if (target.classList.contains("card")) {
                    var playerNumber = target.getAttribute('x-player-number');
                    var cardIndex = target.getAttribute('x-card-index');
                    var cardColor = others[playerNumber].hand[cardIndex].color;
                    var cardNumber = others[playerNumber].hand[cardIndex].number;

                    e.currentTarget.appendChild(knowledgeButtons);
                    knowledgeButtons.setAttribute('x-color', cardColor);
                    knowledgeButtons.setAttribute('x-number', cardNumber);
                    knowledgeButtons.setAttribute('x-player-number', playerNumber);

                    // set the button text
                    knowledgeButtons.querySelector('[x-button="tell-number"]').textContent = "Tell " + cardNumber;
                    knowledgeButtons.querySelector('[x-button="tell-color"]').textContent = "Tell " + capitalize(cardColor);

                    // show the buttons
                    knowledgeButtons.setAttribute('style', '');
                }
                // check to see if the buttons are hidden
                if (!myHandButtons.getAttribute('style').match(/display:\s*none/)) {
                    myHandButtons.setAttribute('style', 'display: none;');
                }
            }

            // attach the listener to everyones hands
            for (i = 0; i < others.length; i++) {
                var handDiv = document.querySelector("#hand" + i);
                initializeListener(handDiv, 'click', clickedOnOther, prevClickedOnOther);
                prevClickedOnOther = clickedOnOther;
            }

            let alreadyCalledHintButtons = false;

            // setup the instruction clicks for the information menu.
            var instructionClick = function (e) {
                var target = e.currentTarget;
                var instructionType = e.target.getAttribute('x-button');
                var playerNumber = target.getAttribute('x-player-number');
                var instructionColor = target.getAttribute('x-color');
                var instructionNumber = target.getAttribute('x-number');
                var instruction = instructionType === 'tell-color' ? instructionColor : instructionNumber;
                const currPlayer = game.currentPlayer % game.players.length;
                switch (instructionType) {
                    case "cancel":
                        knowledgeButtons.setAttribute('style', 'display: none;');
                        break;
                    case "tell-color":
                    case "tell-number":
                        if (alreadyCalledHintButtons)
                            return;

                        console.log('Ok ora faccio', instructionType)

                        if (game.clueTokens <= 0) {
                            const message = "No clue tokens!";
                            knowledgeButtons.setAttribute('style', 'display: none;');
                            document.getElementById("footer").style.display = "";
                            displayMessage(messageDiv, message);
                            setTimeout(function () {
                                document.getElementById("footer").style.display = "none";
                                messageDiv.setAttribute('style', 'display: none;');
                            }, 3000);

                            return;
                        }

                        alreadyCalledHintButtons = true;
                        game.clueTokens--;
                        setKnowledge(others[playerNumber].hand, instruction);
                        logMove(game, me.name, instructionType, instruction, null, others[playerNumber].name);
                        game.currentPlayer++;

                        let data = {
                            instructionType: instructionType,
                            info: instruction,
                            currentPlayer: currPlayer
                        };

                        if (currPlayer === 0) {  // Qui gameChoice === "tom_human"
                            /* Se il giocatore corrente è 1 allora non devo ricomunicare questa azione, me la sono presa
                               da chi già sa di averla fatta. Se siamo in gameChoice "tom" a maggior ragione non
                               serve mai ricomunicare l'azione. */
                            socket.emit('update-last-action', data);
                        }

                        tom_human_send_action(game, socket, me, myId, currPlayer, true);

                        break;
                }
            };
            initializeListener(knowledgeButtons, 'click', instructionClick, prevInstructionClick);
            prevInstructionClick = instructionClick;
            var instructionButtonEnter = function (e) {
                var target = e.currentTarget;
                var playerNumber = knowledgeButtons.getAttribute('x-player-number');
                var parent = document.querySelector('#hand' + playerNumber);
                var cards = parent.querySelectorAll('.card');
                switch (target.getAttribute('x-button')) {
                    case 'tell-number':
                        for (var i = 0; i < cards.length; i++) {
                            var card = cards[i];
                            if (others[playerNumber].hand[card.getAttribute('x-card-index')].number == knowledgeButtons.getAttribute('x-number')) {
                                card.classList.remove('de-emphasize');
                            } else {
                                card.classList.add('de-emphasize');
                            }
                        }
                        break;
                    case 'tell-color':
                        for (var i = 0; i < cards.length; i++) {
                            var card = cards[i];
                            if (others[playerNumber].hand[card.getAttribute('x-card-index')].color == knowledgeButtons.getAttribute('x-color')) {
                                card.classList.remove('de-emphasize');
                            } else {
                                card.classList.add('de-emphasize');
                            }
                        }
                        break;
                }
            };
            const tellNumberObj = knowledgeButtons.querySelector('[x-button="tell-number"]');
            const tellColorObj = knowledgeButtons.querySelector('[x-button="tell-color"]');
            initializeListener(tellNumberObj, 'mouseover', instructionButtonEnter, prevInstructionButtonEnter);
            initializeListener(tellNumberObj, 'mouseout', reEmphasizeAllCards, prevReEmphasizeAllCards);
            initializeListener(tellColorObj, 'mouseover', instructionButtonEnter, prevInstructionButtonEnter);
            initializeListener(tellColorObj, 'mouseout', reEmphasizeAllCards, prevReEmphasizeAllCards);
            prevInstructionButtonEnter = instructionButtonEnter;
            prevReEmphasizeAllCards = reEmphasizeAllCards;
        }

        //look for my hand buttons and hide them
        myHandButtons = document.querySelector('#my-hand .instruction');
        myHandButtons.setAttribute('style', 'display: none;');

        if(isBoard === 'true') {
            var mydiv = document.querySelector("#my-hand");

            // setup listener for our hand
            var clickedMyHand = function (e) {
                if (currPlayerId != myId) {
                    return;
                }
                var target = e.target;
                if (target.classList.contains("card")) {
                    var cardIndex = target.getAttribute('x-card-index');
                    myHandButtons.setAttribute('style', '');
                    myHandButtons.setAttribute('x-card-index', cardIndex);

                    // de-emphasize all the cards we didn't click on
                    var cards = e.currentTarget.querySelectorAll('.card');
                    for (var i = 0; i < cards.length; i++) {
                        var card = cards[i];
                        if (card.getAttribute('x-card-index') !== cardIndex) {
                            card.classList.add('de-emphasize');
                        } else {
                            card.classList.remove('de-emphasize');
                        }
                    }
                }
                // check to see if the other buttons are hidden
                if (!knowledgeButtons.getAttribute('style').match(/display:\s*none/)) {
                    knowledgeButtons.setAttribute('style', 'display: none;');
                }
            }

            initializeListener(mydiv, 'click', clickedMyHand, prevClickedMyHand);
            prevClickedMyHand = clickedMyHand;
        }
    } else {
        //look for my hand buttons and hide them
        myHandButtons = document.querySelector('#my-hand .instruction');
        myHandButtons.setAttribute('style', 'display: none;');
    }

    if (isBoard === 'true' && currPlayerId == myId && gameChoice === 'tom_human') {
        message = "Its your turn!";
        displayMessage(messageDiv, message);
    }

    if(isBoard === 'true') {
        //set up the discard and the tableau
        var discard = document.querySelector("#discard");
        var tableau = document.querySelector("#tableau");
        setupTableau(game, discard, tableau);
    }

    if(gameChoice === "tom_human" && isBoard === 'true') {
        let alreadyCalledMyHandClick = false;
        const myHandClick = function (e) {
            if(alreadyCalledMyHandClick)
                return;

            const instructionType = e.target.getAttribute('x-button');

            if(instructionType.toString() !== "cancel")
                alreadyCalledMyHandClick = true;

            const target = e.currentTarget;
            const cardIndex = target.getAttribute('x-card-index');
            console.log('Ok ora faccio', instructionType)
            console.log('Sono in myHandClick e instructionType =', instructionType);
            myHandInstruction(game, instructionType, cardIndex, me, socket, myHandButtons);
        }

        initializeListener(myHandButtons, 'click', myHandClick, prevMyHandClick);
        prevMyHandClick = myHandClick;
    }

    if(!ignoreEndGame) {
        if (gameChoice === "tom") {
            if (currPlayer === 0 && !p0startedGetLastAction) {
                p0startedGetLastAction = true;
                console.log('Ok non faccio get-last-action, p0startedGetLastAction = true')
                // Dico a get-last-action che voglio l'azione mia, così la rimanda a me stesso,
                // a differenza degli altri emit in cui loro passano other perché la loro azione già l'hanno fatta
            } else {
                const otherPlayer = currPlayer === 0 ? 1 : 0;
                if (!game.finalRound) {
                    console.log('Sono il giocatore', currPlayer, 'e ora faccio get-last-action')
                    socket.emit('get-last-action', others[0], otherPlayer);
                } else {
                    // Se sono il finishingPlayer, prendo la mossa dell'altro player e glie la faccio eseguire,
                    // dopodiché, lui farà altrettanto con me e infine il finishingPlayer fa 'get-last-action-and-do-it-by-myself'
                    if (game.finishingPlayerId === currPlayer) {
                        if (finishingPlayerSecondPlay === true) {
                            console.log('Ora faccio get-last-action-and-do-it-by-myself')
                            socket.emit('get-last-action-and-do-it-by-myself', game, me, currPlayer);
                        } else {
                            console.log('Sono il giocatore', currPlayer, 'e ora faccio get-last-action')
                            socket.emit('get-last-action', others[0], otherPlayer);
                        }
                    } else {
                        socket.emit('get-last-action', others[0], otherPlayer);
                    }
                }
            }
        } else {
            if (currPlayer === game.finishingPlayerId && finishingPlayerSecondPlay === true) {
                console.log('Ora faccio get-last-action-and-do-it-by-myself')
                socket.emit('get-last-action-and-do-it-by-myself', game, me, currPlayer);
            }
        }
    }
}

//updates all information based on the game object
function executeAction(game, me, socket, currPlayerId, myId, lastAction) {
    if (!lastAction) return;
    const { instructionType, info } = lastAction;

    if (instructionType === 'tell-color' || instructionType === 'tell-number') {
        hintInstruction(game, instructionType, info, socket, me, myId);
    } else if (instructionType === 'play-card' || instructionType === 'discard-card') {
        const cardIndex = parseInt(info);
        myHandInstruction(game, instructionType, cardIndex, me, socket, null);
    }
}

function updateScreen(game, me, socket, currPlayerId, myId, ignoreEndGame, dontUpdateBoard) {
    const gameChoice = game.gameChoice.toLowerCase();
    let currPlayer = me.id === game.players[0].id ? 0 : 1;

    console.log('isBoard =', isBoard, ', currPlayer =', currPlayer);
    if(currPlayer === 0 && isBoard === 'false' && !dontUpdateBoard)
        socket.emit('game-update-board', game, me, myId);

    const others = [];
    for (let i = 0; i < game.players.length; i++) {
        if (game.players[i].id !== me.id) {
            // Others is now a list of the index of the player in the array of game.players
            others.push(game.players[i]);
        }
    }

    console.log('Sono in updateScreen, others =', others);
    console.log('me =', me)
    console.log('game.players =', game.players)

    if (gameChoice === "tom") {
        if (currPlayer === 0) {
            // Allora gioca l'utente graficamente
            console.log('Inizializzo la grafica per il giocatore 0.')
            console.log('Ora game-update vale:', game)
        } else {
            // Se il gameChoice non è "tom", continua con il normale aggiornamento dello schermo
            console.log('Inizializzo la grafica per il giocatore 1.');
            console.log('2. Game =', game)
        }

        updateScreenHelperFunction(game, others, me, socket, currPlayerId, myId, ignoreEndGame);
    }
    else {
        if (currPlayer === 0) {
            // Allora gioca l'utente graficamente
            console.log('Inizializzo la grafica per il giocatore 0.')
            console.log('Ora game-update vale: ', game)
        } else {
            // Se il gameChoice non è "tom", continua con il normale aggiornamento dello schermo
            console.log('Inizializzo la grafica per il giocatore 1.');
            console.log('2. Game = ', game)
        }

        updateScreenHelperFunction(game, others, me, socket, currPlayerId, myId, ignoreEndGame);

        const discardButton = document.querySelector("[x-button='discard-card']");
        if(game.clueTokens === game.maxClueTokens) {
            discardButton.classList.add("hidden");
        } else {
            if (discardButton.classList.contains("hidden")) {
                discardButton.classList.remove("hidden");
            }
        }
    }
}


function setupTableau(game, discardArea, tableauArea) {
    var i, j;

    // set up the discard area
    var s = "<ul>";
    for (i = 0; i < game.discard.length; i++) {
        var card = game.discard[i];
        s += "<li>";
        s += "<img class='card' src='/images/cards/" + card.number + "-" + card.color + ".png' />";
        s += "</li>";
    }
    s += "</ul>"
    discardArea.querySelector('.contents').innerHTML = s;

    // set up the tableau
    var s = "<ul>"//;
    for (i in game.tableau) {
        var stack = game.tableau[i];
        s += "<li><ul class='card-stack'>";
        for (j = 0; j < stack.length; j++) {
            var card = stack[j];
            s += "<li>";
            s += "<img class='card' src='/images/cards/" + card.number + "-" + card.color + ".png' />";
            s += "</li>";
        }
        s += "</ul></li>";
    }
    s += "</ul>"
    tableauArea.querySelector('.contents').innerHTML = s;

}

// returns whether a card is playable in the current game
function isCardPlayable(game, card) {
    // checks if the length is undefined, if it is use 0 as the length.
    var length = game.tableau[card.color] ? game.tableau[card.color].length : 0;
    // if the card number is the length +1 then it is the right card to play otherwise it is invalid
    return card.number === length + 1;
}

function reEmphasizeAllCards() {
    var cards = document.querySelectorAll('.card');
    for (var i = 0; i < cards.length; i++) {
        var card = cards[i];
        card.classList.remove('de-emphasize');
    }
}

function hintInstruction(game, instructionType, info, socket, me, myId) {
    const gameChoice = game.gameChoice.toLowerCase();
    const currPlayer = game.currentPlayer % game.players.length;

    if (game.clueTokens <= 0) {
        if(isBoard === 'false') {
            const knowledgeButtons = document.querySelector('.instruction');
            knowledgeButtons.setAttribute('style', 'display: none;');
            const messageDiv = document.querySelector('#messages');
            const message = "No clue tokens!";
            document.getElementById("footer").style.display = "";
            displayMessage(messageDiv, message);
            setTimeout(function () {
                document.getElementById("footer").style.display = "none";
                messageDiv.setAttribute('style', 'display: none;');
            }, 3000);
        }
        return;
    }
    game.clueTokens--;

    const instruction = instructionType === 'tell-color' ? info : parseInt(info);
    if (gameChoice === "tom") {
        if(currPlayer === 0) {
            console.log('Ora faccio setKnowledge + logMove')
            setKnowledge(game.players[1].hand, instruction);
            logMove(game, game.players[0].name, instructionType, instruction, null, game.players[1].name);
        }
        else {
            console.log('Ora faccio setKnowledge + logMove')
            setKnowledge(game.players[0].hand, instruction);
            logMove(game, game.players[1].name, instructionType, instruction, null, game.players[0].name);
        }
    } else {  // Allora se sono qui so che, per la forma del chiamante, currPlayer !== 0
        console.log('Ora faccio setKnowledge + logMove')
        setKnowledge(game.players[0].hand, instruction);
        logMove(game, game.players[1].name, instructionType, instruction, null, game.players[0].name);
    }
    game.currentPlayer++;
    socket.emit('game-server-update', game, (response) => {});

    console.log('Ora faccio game-update')
    if(gameChoice === "tom")
        // socket.emit('game-update-myself-too', game, (response_) => {});
        tom_send_action(game, socket, me, myId, currPlayer);
    else {
        tom_human_send_action(game, socket, me, myId, currPlayer, true);
    }
}

// runs when the instruction buttons in our hand are clicked; can choose between playing, cancelling move and discarding a card.
function myHandInstruction(game, instructionType, cardIndex, me, socket, myHandButtons) {
    const gameChoice = game.gameChoice.toLowerCase();
    if((instructionType === "play-card" || instructionType === "discard-card") &&
        gameChoice === "tom_human" && isBoard === 'true') {
        console.log('Sto per fare pass-tom-human-myhand-action-to-player0');
        // Allora devo dire al giocatore 0 di proseguire da qui in poi
        socket.emit('pass-tom-human-myhand-action-to-player0', game, instructionType, cardIndex);
        return;
    }

    let playedCard, isPlayed, newHand;
    const playerIdx = game.players[0].id == me.id ? 0 : 1;

    switch (instructionType) {
        case "cancel":
            myHandButtons.setAttribute('style', 'display: none;');
            reEmphasizeAllCards();
            return;
        case "play-card":
            //playedCard = me.hand.splice(cardIndex, 1)[0];
            playedCard = me.hand[cardIndex];

            // Crea un nuovo array manualmente (alternativa al metodo splice)
            newHand = [];
            me.hand.forEach((card, index) => {
                if (index.toString() !== cardIndex.toString()) {
                    newHand.push(card);
                }
            });
            me.hand = newHand;
            game.players[playerIdx] = me;

            console.log('2. Scarto la carta', playedCard, 'da me.hand[', cardIndex, '], e me.hand = ', me.hand)
            // La carta verrà rimossa poi dalla mia mano quando faccio get-cards
            isPlayed = isCardPlayable(game, playedCard);
            if (isPlayed) {
                game.tableau[playedCard.color] = (game.tableau[playedCard.color] || []);
                game.tableau[playedCard.color].push(playedCard);
                game.score++;
                if (playedCard.number === 5) {
                    game.clueTokens = Math.min(game.clueTokens + 1, game.maxClueTokens);
                }
            } else {
                // put the played card on the discard pile
                game.discard.push(playedCard);
                game.hearts = game.hearts - 1;
            }
            break;
        case "discard-card":
            game.clueTokens = Math.min(game.clueTokens + 1, game.maxClueTokens);
            // playedCard = me.hand.splice(cardIndex, 1)[0];
            playedCard = me.hand[cardIndex];

            // Crea un nuovo array manualmente (alternativa al metodo splice)
            newHand = [];
            me.hand.forEach((card, index) => {
              if (index.toString() !== cardIndex.toString()) {
                newHand.push(card);
              }
            });
            me.hand = newHand;
            game.players[playerIdx] = me;

            console.log('1. Scarto la carta', playedCard, 'da me.hand[', cardIndex, '], e me.hand = ', me.hand)
            // put the played card on the discard pile
            game.discard.push(playedCard);

            break;
    }

    reEmphasizeAllCards();

    let currPlayer = me.id === game.players[0].id ? 0 : 1;

    let data = {
        instructionType: instructionType,
        info: cardIndex,
        currentPlayer: currPlayer
    };

    if(gameChoice === "tom_human" && currPlayer === 0) {
        /* Se il giocatore corrente è 1 allora non devo ricomunicare questa azione, me la sono presa
           da chi già sa di averla fatta. Se siamo in gameChoice "tom" a maggior ragione non
           serve mai ricomunicare l'azione. */
        socket.emit('update-last-action', data);
    }

    // Add a new card to your hand
    console.log('Ora faccio get-cards, instructionType =', instructionType);
    socket.emit('get-cards', game, me, instructionType, playedCard, isPlayed, currPlayer);
}

// Set up my hand, can either show the cards or hide the cards
function setupMyHand(hand, parent, show) {
    var s = "";
    for (var i = 0; i < hand.length; i++) {
        var knowledge = getKnowledgeClasses(hand[i]).join(' ');
        s += "<li>";
        // put all the information we know about possibilities for the card in one place
        s += "<div class='knowledge " + knowledge + "'>";
        s += '<span class="color">■</span><span class="color">■</span><span class="color">■</span><span class="color">■</span><span class="color">■</span>';
        s += '<span class="number">1</span><span class="number">2</span><span class="number">3</span><span class="number">4</span><span class="number">5</span>';
        s += "</div>"
        //either show or hide the cards
        s += show ? "<img class='card' x-card-index='" + i + "' src='/images/cards/" + hand[i].number + "-" + hand[i].color + ".png'/>" : "<div class='card' x-card-index='" + i + "'></div>";
        s += "</li>";
    }
    parent.innerHTML = s;
}

function getPlayerById(gameTemp, id) {
    for (var i = 0; i < gameTemp.players.length; i++) {
        if (game.players[i].id == id) {
            return game.players[i];
        }
    }
}

// hand is the players hand, parent is the div
// that all the cards should be displayed in.
function setupHand(hand, parent, playerNumber) {
    var s = "<ul>";
    for (var i = 0; i < hand.length; i++) {
        var knowledge = getKnowledgeClasses(hand[i]).join(' ')
        s += "<li>";
        // put all the information we know about possibilities for the card in one place
        s += "<div class=\"knowledge " + knowledge + "\" style=\"font-size: x-large !important\">";
        s += '<span class="color">■</span><span class="color">■</span><span class="color">■</span><span class="color">■</span><span class="color">■</span>';
        s += '<span class="number">1</span><span class="number">2</span><span class="number">3</span><span class="number">4</span><span class="number">5</span>';
        s += "</div>";
        s += "<img class='card' x-card-index='" + i + "' src='/images/cards/" + hand[i].number + "-"
            + hand[i].color + ".png' x-player-number='" + playerNumber + "' style=\"width: 9.2em !important; height: 14em !important\"/>";
        s += "</li>";
    }
    parent.innerHTML = s;
}

function setKnowledge(hand, knowledge) {
    var allInfo = [];
    knowledge = '' + knowledge;
    var instructionType = null;

    // if knowledge lengh is 1 we assume it's a number
    if (knowledge.length == 1) {
        allInfo = [1, 2, 3, 4, 5];
        instructionType = 'number';
    } else {
        allInfo = ['red', 'yellow'];
        instructionType = 'color';
    }
    var excludedInfo = allInfo.filter(function (x) {
        return x != knowledge;
    });
    for (var i = 0; i < hand.length; i++) {
        if (hand[i][instructionType] == knowledge) { // hand[i]['color']
            extendByArray(hand[i].impossible, excludedInfo);
        } else {
            hand[i].impossible[knowledge] = true;
        }
    }
}


function tom_human_send_action(game, socket, me, myId, currPlayer, isHint) {
    // Se non è un hint allora l'aggiornamento proviene potenzialmente dal board
    if(!isHint && isBoard === 'true') {
        // Allora devo dire al giocatore 0 di proseguire da qui in poi
        socket.emit('pass-tom-human-action-to-player0', game)
        return;
    }

    const otherPlayer = currPlayer === 0 ? 1 : 0;
    const currPlayerId = game.players[game.currentPlayer % game.players.length].id;

    if(game.hearts === 0) {
        updateScreen(game, me, socket, currPlayerId, myId, false, false);
        return;
    }

    let event;

    if (!game.finalRound && game.deck.length === 0) {
        event = 'game-update-myself-too';  // Mi accorgerò dopo che è iniziato il final round
    } else {
        if(game.finalRound) {  // Quindi game.deck.length === 0
            if(currPlayer === game.finishingPlayerId) {
                // Nota che il currPlayerId è riferito al prossimo giocatore, come giusto che sia
                updateScreen(game, me, socket, currPlayerId, myId, false, false);
                // L'update precedente farà fare endgame anche all'altro giocatore, quindi posso fermarmi
                return;
            }
            else {
                // Il gioco sta finendo, sono nel round finale, ma non concluderò io il gioco, essendo
                // in questo caso io diverso dal finishing player. Se ne occuperà lui di aggiornarmi.
                updateScreen(game, me, socket, currPlayerId, myId, true, false);
                event = 'game-update';
            }
        } else {  // !game.finalRound && game.deck.length > 0
            event = 'game-update-myself-too'
        }
    }

    const others = [];
    for (let i = 0; i < game.players.length; i++) {
        if (game.players[i].id !== me.id) {
            // Others is now a list of the index of the player in the array of game.players
            others.push(game.players[i]);
        }
    }

    console.log('Ora event =', event)
    socket.emit(event, game, (response) => {
        // Se sono il giocatore 0 e gameChoice === "tom_human", allora dopo gioca il modulo di ToM,
        // per cui mi metto in attesa della last-action
        console.log('Sono prima di if (currPlayer === 0 && !game.finalRound), dopo event')
        if (currPlayer === 0 && !game.finalRound) {
            console.log('Sono il player 0 e ora faccio get-last-action, perché game.finalRound =', game.finalRound);
            socket.emit('get-last-action', others[0], otherPlayer);
        }
    });
}

function tom_send_action(game, socket, me, myId, currPlayer) {
    const currPlayerId = game.players[game.currentPlayer % game.players.length].id;

    if(game.hearts === 0) {
        updateScreen(game, me, socket, currPlayerId, myId, false, false);
        return;
    }

    let event;

    if (!game.finalRound && game.deck.length === 0) {
        event = 'game-update-myself-too';  // Mi accorgerò dopo che è iniziato il final round
    } else {
        if(game.finalRound) {  // Quindi game.deck.length === 0
            if(currPlayer === game.finishingPlayerId) {
                // Nota che il currPlayerId è riferito al prossimo giocatore, come giusto che sia
                updateScreen(game, me, socket, currPlayerId, myId, false, false);
                // L'update precedente farà fare endgame anche all'altro giocatore, quindi posso fermarmi
                return;
            }
            else {
                // Il gioco sta finendo, sono nel round finale, ma non concluderò io il gioco, essendo
                // in questo caso io diverso dal finishing player. Se ne occuperà lui di aggiornarmi.
                updateScreen(game, me, socket, currPlayerId, myId, true, false);
                event = 'game-update';
            }
        } else {  // !game.finalRound && game.deck.length > 0
            event = 'game-update-myself-too'
        }
    }

    console.log('Ora event =', event)
    socket.emit(event, game, (response) => {});
}

function hideGraphicsForPlayers() {
    document.getElementById("clues-hearts-deck").style.display = "none";
    document.getElementById("my-hand").style.display = "none";
    document.getElementById("hand1").style.display = "none";
    document.getElementById("hand2").style.display = "none";
    document.getElementById("hand3").style.display = "none";
    document.getElementById("clear-flex1").style.display = "none";
    document.getElementById("clear-flex2").style.display = "none";
    document.getElementById("tableau").style.display = "none";
    document.getElementById("discard").style.display = "none";
    document.getElementById("log").style.display = "none";
    document.getElementById("footer").style.display = "none";
    document.getElementById("messages").style.display = "none";

    // Ora, siccome abbiamo nascosto degli elementi, apportiamo delle modifiche agli stili

    // Seleziona l'elemento .player-name all'interno di .hand e sovrascrivi le proprietà CSS
    const playerNameElement = document.querySelector('.hand .player-name');
    playerNameElement.style.setProperty('position', 'relative', 'important');
    playerNameElement.style.setProperty('font-size', 'x-large', 'important');
    playerNameElement.style.setProperty('width', '120px', 'important');

    // Seleziona l'elemento .hand
    const handElement = document.querySelector('.hand');

    // Sovrascrivi le proprietà CSS con il nuovo stile, utilizzando !important
    handElement.style.setProperty('margin', '0px', 'important');
    handElement.style.setProperty('display', 'flex', 'important');
    handElement.style.setProperty('justify-content', 'center', 'important');
    handElement.style.setProperty('align-items', 'center', 'important');
    handElement.style.setProperty('text-align', 'center', 'important');

    // Rimuovi le proprietà obsolete se presenti, utilizzando !important
    handElement.style.setProperty('padding-left', '0px', 'important');
    handElement.style.setProperty('position', 'static', 'important');
}

function hideGraphicsForBoard(isTomTom) {
    document.getElementById("hand0").style.display = "none";
    document.getElementById("hand1").style.display = "none";

    if(isTomTom) {
        document.getElementById("my-hand").style.display = "none";
        document.getElementById("messages").style.display = "none";
    }
}

let endpoint, backendEndpoint, isBoard;

window.onload = function () {
    // grab the name and room from the URI search string
    // get a few globals
    // some of these may be redundant
    const args = parseUriSearchString(window.location.search);
    let name = args.name;
    let id = args.persistentId;
    isBoard = args.isboard
    const room = args.room;
    const myId = id;
    let me = null;

    // If any of the necessary information is not there, kick them back to the lobby.
    if (!name || !id || !room || !isBoard || !(isBoard === 'false' || isBoard === 'true')) {
        document.location.href = lobbyUrl;
    }

    // Set up the background
    const b = new Bokeh();
    b.initialize();

    // Set up the web socket
    let socket = io.connect();
    window.ss = socket;

    console.log('isBoard è:', isBoard)
    if(isBoard === 'false') {
        hideGraphicsForPlayers();

        socket.emit('set-name', name);
        socket.emit('set-room', room);
        // emitting this signal will trigger the initalize-game signal
        // and cause the server to send us a copy of the game object.
        socket.emit('start-game');
    }
    else {
        socket.on('set-endpoints', function (endpoint_, backendEndpoint_) {
            endpoint = endpoint_;
            backendEndpoint = backendEndpoint_;
        });

        socket.on('set-game-choice', function (gameChoice) {
            hideGraphicsForBoard(gameChoice === "tom");
        });

        socket.on('update-data-board', function (gameTemp, me, meId, tmp) {
            console.log('Tmp =', tmp)
            game = gameTemp;

            const currPlayerId = game.players[game.currentPlayer % game.players.length].id;
            updateScreen(game, me, socket, currPlayerId, meId, true, false);
        });

        socket.emit('i-am-board');
        socket.emit('get-endpoints');
        socket.emit('get-game-choice');
        socket.emit('request-first-game-update-board');
        socket.emit('set-board-ready');
    }

    socket.on('endgame', function (game, currPlayer) {
        const currPlayerId = game.players[game.currentPlayer % game.players.length].id;
        const me = game.players[game.currentPlayer % game.players.length];
        console.log('currPlayerId =', currPlayerId, ', me =', me);
        console.log('myId =', myId, ', currPlayerId =', currPlayerId, ', game=', game);

        // Qui dontUpdateBoard è sempre true, perché l'aggiornamento lo facciamo di persona, non delegandolo a player0.
        if(currPlayer === 0) {
            updateScreen(game, me, socket, currPlayerId, myId, true, true);
        } else if(currPlayer === 1) {
            if (isBoard === 'false') {
                // Allora sto aggiornando la grafica del giocatore 0
                updateScreen(game, me, socket, currPlayerId, myId, true, true);
            } else {
                // Allora sto aggiornando la grafica del board, ma io voglio che
                // l'aggiornamento provenga dal giocatore 0, quindi agirò per nome suo.
                // Nota che la socket ha poca importanza che sia del giocatore 1 qui, idem myId. Conta 'other'.
                const otherPlayerId = game.players[(game.currentPlayer+1) % game.players.length].id;
                const other = game.players[(game.currentPlayer+1) % game.players.length];
                updateScreen(game, other, socket, otherPlayerId, myId, true, true);
            }
        }
        endGame(game, socket, currPlayer);
    });

    const myHandButtons = document.querySelector('#my-hand .instruction');
    if(isBoard === 'false') {
        socket.on('do-tom-human-action', function (game) {
            const currPlayer = me.id === game.players[0].id ? 0 : 1;
            if(currPlayer === 0)
                tom_human_send_action(game, socket, me, myId, currPlayer, false)
        });

        socket.on('do-tom-human-myhand-action', function (game, instructionType, cardIndex) {
            const currPlayer = me.id === game.players[0].id ? 0 : 1;
            console.log('sono in do-tom-human-myhand-action, currPlayer =', currPlayer);
            if(currPlayer === 0) {
                myHandInstruction(game, instructionType, cardIndex, me, socket, myHandButtons)
            }
        });

        socket.on('set-endpoints', function (endpoint_, backendEndpoint_) {
            endpoint = endpoint_;
            backendEndpoint = backendEndpoint_;
        });

        let player0set = false;

        // update the screen based on an incoming game object
        socket.on('update-data', function (gameTemp, tmp, callback) {
            console.log('Tmp =', tmp)
            game = gameTemp;
            me = getPlayerById(game, myId);

            if(!player0set) {
                const currPlayer = me.id === game.players[0].id ? 0 : 1;
                if(currPlayer === 0) {
                    player0set = true;
                    socket.emit('set-player0', me, myId);
                }
            }

            const currPlayerId = game.players[game.currentPlayer % game.players.length].id;
            updateScreen(game, me, socket, currPlayerId, myId, false, false);
            callback({
                status: "ok"
            });
        });

        // receive information from server about our name and id
        socket.on('id-info', function (data) {
            name = data.name;
            id = data.id;
        });

        // Registra il listener
        socket.on('get-last-action-client', function (game_, me_, lastAction) {
            const gameChoice = game_.gameChoice.toLowerCase();
            const currPlayer = me_.id === game_.players[0].id ? 0 : 1;
            const currPlayerId = game_.players[game_.currentPlayer % game_.players.length].id;

            console.log('1 - Sono in get-last-action-client. currPlayerId = ', currPlayerId, ', currPlayer = ', currPlayer, ' e lastAction = ', lastAction);
            // console.log('game_ = ', game_)
            // console.log('me_ = ', me_)

            if ((gameChoice === "tom_human" && currPlayer === 1) || gameChoice === "tom") {
                console.log('2 - Sono in get-last-action-client. currPlayerId = ',
                    currPlayerId, ', currPlayer = ', currPlayer, ' e lastAction = ', lastAction);

                console.log('Sto per fare executeAction...');
                console.log('1. game_ =', game_);
                console.log('1. me_ =', me_)
                executeAction(game_, me_, socket, currPlayerId, myId, lastAction);
            }
        });

        socket.on('get-last-action-client-final-move', function (game_, me_, lastAction) {
            const currPlayer = me_.id === game_.players[0].id ? 0 : 1;
            const currPlayerId = game_.players[game_.currentPlayer % game_.players.length].id;

            console.log('2 - Sono in get-last-action-client-final-move. currPlayerId = ',
                currPlayerId, ', currPlayer = ', currPlayer, ' e lastAction = ', lastAction);

            console.log('Sto per fare executeAction...');
            console.log('3. game_ =', game_);
            console.log('3. me_ =', me_)
            executeAction(game_, me_, socket, currPlayerId, myId, lastAction);
        })

        socket.on('get-cards-client', function (data, game, me, instructionType, playedCard, isPlayed, currPlayer) {
            console.log('Gotten cards per ', currPlayer, ': ', data);
            const deckIsEmpty = game.deck.length === 0;
            console.log('deckIsEmpty =', deckIsEmpty, ', game =', game);

            // La nuova carta da aggiungere, il backend la aggiunge sempre in coda
            let lastCardFromData;
            if (currPlayer === 0) {
                lastCardFromData = data['p1cards'].at(-1);
                console.log('Me.hand = ', me.hand, ', data[p1cards] =', data['p1cards'], 'lastCardFromData =', lastCardFromData)
                if (!deckIsEmpty && game.hearts > 0)
                    me.hand.push(lastCardFromData);
                console.log('Me.hand aggiornato è:', me.hand)
                game.players[0] = me;
            } else {
                lastCardFromData = data['p2cards'].at(-1);
                console.log('Me.hand = ', me.hand, ', data[p2cards] =', data['p2cards'], 'lastCardFromData =', lastCardFromData)
                if (!deckIsEmpty && game.hearts > 0)
                    me.hand.push(lastCardFromData);
                console.log('Me.hand aggiornato è:', me.hand)
                game.players[1] = me;
            }
            /*
            me.hand:  [
              { color: 'yellow', number: 1, impossible: {} },
              { color: 'red', number: 5, impossible: {} },
              { color: 'yellow', number: 3, impossible: {} },
              { color: 'yellow', number: 4, impossible: {} },
              ...
            ] */
            logMove(game, game.players[currPlayer].name, instructionType, playedCard.color + ' ' + playedCard.number, isPlayed);

            if (!deckIsEmpty && game.hearts > 0)
                game.deck.length--;

            game.currentPlayer++;
            socket.emit('game-server-update', game, (response) => {});

            console.log('Prima di game-update, esso vale: ', game)

            const gameChoice = game.gameChoice.toLowerCase();

            if (gameChoice === "tom_human") {
                tom_human_send_action(game, socket, me, myId, currPlayer, false);
            } else {
                tom_send_action(game, socket, me, myId, currPlayer);
            }
        });
    }
}
