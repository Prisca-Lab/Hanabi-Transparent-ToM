"use strict";

//used for testing everyone ready behaviour.
var pageRedirect = "/tests/flex-reactive.html";

function parseUriSearchString (str) {
    // Remove leading questionmark
    if (str.charAt(0) == '?') {
        str = str.slice(1);
    }

    // Split up strings in the form of "foo=bar&baz=bat" into
    // objects {foo: 'bar', baz: 'bat'}
    var ret = {}
    str.split('&').forEach(function(s){
        var vals = s.split('=');
        ret[decodeURI(vals[0] || '')] = decodeURI(vals[1] || '')
    });
    return ret;
}


// update window.location.search without having the browser refresh
function updateUriString (vals) {
    var search = [];
    for (var k in vals) {
        search.push(encodeURI(k) + "=" + encodeURI(vals[k]));
    }
    var searchString = "?" + search.join('&');
    var newUrl = window.location.protocol + "//" + window.location.host + window.location.pathname + searchString;
    window.history.replaceState({path: newUrl}, '', newUrl);
}

function createRandomRoomName (excludeNames) {
    excludeNames = excludeNames || [];
    var adjectives = ['Adorable', 'Alert', 'Different', 'Clever', 'Rich', 'Shy', 'Cruel', 'Defiant', 'Scary', 'Itchy', 'Hungry', 'Homeless'];
    var nouns = ['Room', 'Castle', 'Manner', 'Boutique', 'Swamp', 'Forest', 'Bridge', 'Sky-scraper', 'Condo', 'House'];

    var newName = adjectives[Math.floor(Math.random()*adjectives.length)] + " " + nouns[Math.floor(Math.random()*nouns.length)];
    // avoid repeating a name in the excludeNames list
    for (var i = 0; i < excludeNames.length; i++) {
        if (newName == excludeNames[i]) {
            return createRandomRoomName(excludeNames);
        }
    }
    return newName;
}

// Takes an element elm and looks for some text with the .editable-text
// class.  When elm is clicked, a textbox appears. The text that is edited
// in the textbox then appears in the .editable-text element.
function makeElementEditable(elm, callback){
    callback = callback || function(){};
    
    var textElm = elm.querySelector('.editable-text');
    var textbox = document.createElement('input');
    textbox.setAttribute('type', 'text');
    textbox.setAttribute('style', 'display: none');
    elm.appendChild(textbox);

    function changeTextValue(val) {
        textElm.setAttribute('style', '');
        textbox.setAttribute('style', 'display: none;');
        textbox.classList.remove('editing');
        if (val.length > 0) {
            textElm.textContent = val;
            callback(val);
        }
    }
    // Events where we should be watching for name changes
    textbox.addEventListener('keydown', function(e) {
        // pressed enter
        if (e.keyCode == 13) {
            changeTextValue(textbox.value)
        }
        // pressed escape
        if (e.keyCode == 27) {
            textElm.setAttribute('style', '');
            textbox.setAttribute('style', 'display: none;');
            textbox.classList.remove('editing');
        }
    });
    textbox.addEventListener('blur', function(e) {
            changeTextValue(textbox.value)
    });

    elm.addEventListener('click', function() {
        // If we're already editing, do nothing
        if (textbox.classList.contains('editing')) {
            return;
        }
        textbox.classList.add('editing');
        textbox.value = textElm.textContent;
        textbox.setAttribute('style', '');
        textbox.focus();
        textbox.setSelectionRange(0,textbox.value.length);
        textElm.setAttribute('style', 'display: none;')
    });
}


window.onload = function () {
    // grab the name and room from the URI search string, or put

    // Set up the web socket
    const socket = io.connect();
    // in some defaults if they're not given.
    const args = parseUriSearchString(window.location.search);
    let name = args.name || 'Tom';
    const isboard = args.isboard

    // Check if isboard is given. If not, abort
    if (isboard === undefined) {
        console.error("isboard is not in the URI research string.");
        document.body.innerHTML = "<h1>Error: \"isboard\" parameter is not in the URI research string.</h1>";
        return; // Abort
    }

    let id = null;
    let persistentId = args.persistentId;
    let room = args.room || 'PriscaLab';
    if (!args.name || !args.room) {
        window.location.search = "?name=" + encodeURI(name) + "&room=" + encodeURI(room);
    }
    changeName(name)
    changeRoom(room)

    // Set up the background
    const b = new Bokeh();
    b.initialize();


    function changeName(newName) {
        const change = (name !== newName);
        name = newName || name;
        document.querySelector('.name').textContent = name;
        if (!change) {
            return;
        }
        updateUriString(persistentId ? {name: name, room: room, isboard: isboard, persistentId: persistentId} : {name: name, room: room, isboard: isboard});
        try {
            socket.emit('set-name', name);
        } catch (e) {}
    }

    // set up the rooms object
    const roomsList = new RoomsList(document.querySelector('.room-list'));

    function changeRoom(newRoom) {
        const change = (room !== newRoom);
        room = newRoom || room;
        const roomButtons = document.querySelectorAll('.room-list li');
        for (let i = 0; i < roomButtons.length; i++) {
            if (roomButtons[i].getAttribute('x-room') === room) {
                roomButtons[i].classList.add('selected-room');
                roomButtons[i].classList.remove('joinable');
            } else {
                roomButtons[i].classList.remove('selected-room');
                roomButtons[i].classList.add('joinable');
            }
        }
        document.querySelector('.room').textContent = room;
        if (!change) {
            return;
        }
        updateUriString(persistentId ? {name: name, room: room, isboard: isboard, persistentId: persistentId} : {name: name, room: room, isboard: isboard});
        try {
            socket.emit('set-room', room);
        } catch (e) {}
    }
    makeElementEditable(document.querySelector('.editable'), changeName);

    /*
    function roomClicked(e) {
        var elm = e.target;
        // We're actually an LI element that has a room attribute.
        // ie we're not a miss-click.
        if (elm.getAttribute('x-room')) {
            changeRoom(elm.getAttribute('x-room'));
        }
    }
    document.querySelector('.room-list').addEventListener('click', roomClicked);
    */
    roomsList.roomClicked = changeRoom;


    let readyState = false;

    function readyClicked(e) {
        readyState = !readyState;
        const readyButtonText = document.querySelector('#ready-button .text');
        const readyButtonIcon = document.querySelector('#ready-button .icon');
        if (readyState === false){
            readyButtonText.textContent = "I\'m ready!";
            readyButtonIcon.classList.add('fa-play-circle')
            readyButtonIcon.classList.remove('fa-pause')
        } else {
            readyButtonText.textContent = "I\'m not ready!";
            readyButtonIcon.classList.remove('fa-play-circle')
            readyButtonIcon.classList.add('fa-pause')
        }
        socket.emit('set-data', {readyState: readyState});
    }
    document.querySelector('#ready-button').addEventListener('click', readyClicked);

    let existingRooms = [];

    function newRoomClicked(e) {
        const newRoomName = createRandomRoomName(existingRooms);
        changeRoom(newRoomName);
    }

    // This was disabled because it's not tested yet
    // document.querySelector('#new-room-button').addEventListener('click', newRoomClicked);
    window.sss = socket;    //for debug
    socket.on('connect', function () {
        console.log('connected');
        // Set our name
        socket.emit('set-name', name);
        // Join the appropriate room as soon as we've connected
        socket.emit('set-room', room);
        if (persistentId) {
            socket.emit('assert-id', {persistentId: persistentId});
        }
        // Get our ID from the server so we know where we
        // show up in the list of people in our room
        socket.emit('query-id');
    });
    socket.on('id-info', function(data) {
        console.log('Id info:', data);
        name = data.name;
        id = data.id;
        persistentId = data.persistentId;
        updateUriString(persistentId ? {name: name, room: room, isboard: isboard, persistentId: persistentId} : {name: name, room: room, isboard: isboard});
    });
    socket.on('room-info', function(data) {
        let i;
        console.log('Room info:', data);

        // update the room list
        existingRooms = [];
        for (i = 0; i < data.roomList.length; i++) {
            let roomName = data.roomList[i];
            // There's always a blank string for a room.
            // Skip it gracefully.
            if (roomName === '') {
                continue;
            }
            // socket.io rooms always start with a slash, so get rid of it.
            roomName = roomName.slice(1);
            existingRooms.push(roomName);
            // roomListStr += "<li x-room='" + roomName + "'>" + roomName + "</li>";
        }
        //document.querySelector('.room-list').innerHTML = roomListStr;
        roomsList.updateRooms(existingRooms);
        changeRoom(room);

        // update the clients list
        let clientsListStr = "";
        for (i = 0; i < data.clients.length; i++) {
            const client = data.clients[i];
            console.log(client)
            const readyClassStr = client.data.readyState ? 'ready' : 'not-ready';
            clientsListStr += "<li class='" + readyClassStr + "' x-id='" + client.id + "' x-name='" + client.name + "'>" + client.name + "</li>";
	 }

     const readyButtonText = document.querySelector('#ready-button .text');
     const readyButtonIcon = document.querySelector('#ready-button .icon');

     //controls wether you can exit to a game, cant have too many players, cant have too few
	 if(data.clients.length < 2){
	     readyButtonText.textContent = "Not enough player\'s";
	     readyButtonIcon.classList.remove('fa-pause')
             readyButtonIcon.classList.remove('fa-play-circle')
	     document.querySelector('#ready-button').removeEventListener('click', readyClicked);
	 } else if(data.clients.length > 5){
             readyButtonText.textContent = "Too many player\'s!!";
	     readyButtonIcon.classList.remove('fa-pause')
             readyButtonIcon.classList.remove('fa-play-circle')
	     document.querySelector('#ready-button').removeEventListener('click', readyClicked);
	 } else if (readyState === false){
            readyButtonText.textContent = "I\'m ready!";
            readyButtonIcon.classList.add('fa-play-circle')
            readyButtonIcon.classList.remove('fa-pause')
	    document.querySelector('#ready-button').addEventListener('click', readyClicked);
         }else {
            readyButtonText.textContent = "I\'m not ready!";
            readyButtonIcon.classList.remove('fa-play-circle')
            readyButtonIcon.classList.add('fa-pause')
	    document.querySelector('#ready-button').addEventListener('click', readyClicked);
        }

        document.querySelector('.clients-list').innerHTML = clientsListStr;
    });

    socket.on('new-game', function(game){
            console.log(game);
            pageRedirect += window.location.search
            document.location.href = pageRedirect;
    });
}

// Define a class to handle the room's list
// Whenever a room is clicked, the roomClicked function
// is called with the first argument being the room name
var RoomsList = (function() {
    // helper functions
    function removeAllChildren(node) {
        while (node.firstChild) {
            node.removeChild(node.firstChild);
        }
    }
    function appendChildren(node, children) {
        var i;
        for (i = 0; i < children.length; i++) {
            node.appendChild(children[i]);
        }
    }


    // class init function
    "use strict";
    function RoomsList(parent) {
        var _this = this;

        this.parent = parent;
        this.rooms = [];

        this.parent.addEventListener('click', function (e) {
            var elm = e.target;
            if (elm.hasAttribute('x-room')) {
                _this.roomClicked(elm.getAttribute('x-room'), elm, e);
            }
        });
    }

    RoomsList.prototype.createRoomElement = function(roomName) {
        var li = document.createElement('li');
        li.textContent = roomName;
        li.setAttribute('x-room', roomName);
        return li;
    };

    RoomsList.prototype.updateRooms = function(rooms) {
        var i, roomName, roomList;

        roomList = []
        for (i = 0; i < rooms.length; i++) {
            roomName = rooms[i];
            if (roomName == '') {
                continue;
            }

            roomList.push(this.createRoomElement(roomName));
        }

        removeAllChildren(this.parent);
        appendChildren(this.parent, roomList);
        this.rooms = roomList;
    };

    // called whenever a room button is clicked.
    // The argument passed to the callback is <the name of the room>,<elemnt>,<event>
    RoomsList.prototype.roomClicked = function () {};

    return RoomsList;
})();