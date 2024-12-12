"use strict";

if (typeof exports == "undefined" ) {
	var exports = {};
}

function testPrint(){
	console.log('This is a test of a function');
}

// shuffle a deck
function shuffle (list) {
    // create an array with array indices and random numbers
    const indices = Array.apply(null, Array(list.length)).map(function (_, i) {
        return [i, Math.random()];
    });
    // sort based on the random numbers
    indices.sort(function (a,b) {
        return a[1] - b[1];
    });

    const ret = new Array(list.length);
    for (let i = 0; i < list.length; i++) {
        ret[i] = list[indices[i][0]];
    }
    return ret;
}

/* create a new game object for numPlayers number of players */
function createNewGame(numPlayers, deck = null) {
    const game = {
        players: [],
        deck: deck,
        discard: [],
        tableau: {},
        score: 0,
        clueTokens: 5,
        maxClueTokens: 5,
        hearts: 3,
        currentPlayer: 0,
        finalRound: null,
        lastAction: null,
        gameLog: []
    };

    // populate each player's hand
    var handSize = numPlayers <= 3 ? 5 : 4;
    // console.log(game.deck)
    for (var i = 0; i < numPlayers; i++) {
        // generate random IDs for each player.  These can be replaced with their
        // true IDs later.
        game.players.push({
            name: ('' + Math.random()).slice(2, 5),
            id: ('' + Math.random()).slice(2, 5),
            hand: game.deck.splice(0, handSize)
        });
    }

    return game;
}

exports.createNewGame = createNewGame;
exports.testPrint = testPrint;
