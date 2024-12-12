:- use_module(library(assert)).
:- use_module(library(apply)).
:- use_module(library(lists)).


% Fatti
fact(hanabi_game).
fact(cooperative_game).
fact(game_goal(maximize_score)).

% Relazioni: adjacent_card(card1, card2)
adjacent_card(red1, red2).
adjacent_card(red2, red3).
adjacent_card(red3, red4).
adjacent_card(red4, red5).
adjacent_card(yellow1, yellow2).
adjacent_card(yellow2, yellow3).
adjacent_card(yellow3, yellow4).
adjacent_card(yellow4, yellow5).


% Colori statici per le carte: color(card, color)
color(yellow1, yellow).
color(yellow2, yellow).
color(yellow3, yellow).
color(yellow4, yellow).
color(yellow5, yellow).
color(red1, red).
color(red2, red).
color(red3, red).
color(red4, red).
color(red5, red).


% Rank statici per le carte: rank(card, rank)
rank(yellow1, 1).
rank(yellow2, 2).
rank(yellow3, 3).
rank(yellow4, 4).
rank(yellow5, 5).
rank(red1, 1).
rank(red2, 2).
rank(red3, 3).
rank(red4, 4).
rank(red5, 5).


% Carte statiche dati il colore e il rank: card(color, rank, card)
% Utile per aggiornare "at(player, index, card)" quando si conoscono color e rank
card(yellow, 1, yellow1).
card(yellow, 2, yellow2).
card(yellow, 3, yellow3).
card(yellow, 4, yellow4).
card(yellow, 5, yellow5).
card(red, 1, red1).
card(red, 2, red2).
card(red, 3, red3).
card(red, 4, red4).
card(red, 5, red5).


% Stack delle carte giocate correttamente. Inizialmente entrambe le pile sono vuote
stack(red, 1, -).
stack(red, 2, -).
stack(red, 3, -).
stack(red, 4, -).
stack(red, 5, -).
stack(yellow, 1, -).
stack(yellow, 2, -).
stack(yellow, 3, -).
stack(yellow, 4, -).
stack(yellow, 5, -).

% Predicato per recuperare l'ultimo elemento di una lista. Utile per lo stack.
last([X],X).
last([H|T],R):- last(T,R).


% Carte in mano ai giocatori all'inizio del gioco: "at(player, index, card)"
% at(player, index, -) indica che in index, player ha una carta "-" ossia vuota (utile verso la fine del gioco)
at(a, 1, red1).
at(a, 2, yellow3).
at(a, 3, yellow3).
at(a, 4, red2).
at(a, 5, yellow1).
   %%%%%%%%
at(b, 1, yellow2).
at(b, 2, red3).
at(b, 3, yellow1).
at(b, 4, yellow4).
at(b, 5, yellow5).


% Carte nel deck delle carte pescabili, dopo aver dato le carte ai giocatori: deck(index, card)
% Nel mazzo ci sono, per ogni colore, tre "1", due "2", due "3", due "4", un "5" (a meno delle carte in mano ai giocatori)
% deck(1, red1). % In indice 1 troviamo la carta red1
% deck(2, red1).
% deck(3, red2).
% deck(4, red3).
% deck(5, red4).
% deck(6, red4).
% deck(7, red5).
% deck(8, yellow1).
% deck(9, yellow2).
% deck(10, yellow4).

% Mettiamo queste carte dummy, che tanto saranno ignorate in quanto HLE provvederà ad occuparsene
deck(1, red5).
deck(2, red5).
deck(3, red5).
deck(4, red5).
deck(5, red5).
deck(6, red5).
deck(7, red5).
deck(8, red5).
deck(9, red5).
deck(10, red5).


% Carte scartate: discarded_deck(CardList[])
discarded_deck([]).


/* NOTA: il precedente (at e deck) è solo un esempio di partenza. Python inizializza "at" e "deck" in modo casuale.
         Ossia nel deck ci sono, per ogni colore,  tre "1", due "2", due "3", due "4", un "5". Se però al giocatore
         1 do ad esempio red1 e al giocatore 2 do yellow3, nel mazzo avrò ora 1 solo yellow3 e 2 soli red2
         (perché ci sono solo complessivamente tre 1 e due 3). Quindi nel deck ci saranno le carte
         iniziali meno quelle date in mano ai giocatori. Anche knows_at viene inizializzato coerentemente da Python. */

%%% knows a %%%:
% knows_at rappresenta le info sulle carte di tutti i giocatori. Queste info saranno aggiornate dal modulo HCIC.
% NOTA: le probabilità con 0.0 è superfluo esplicitarle
1.0::knows_at(a, (b, 1, yellow2)). % 0.0::knows_at(a, (b, 1, yellow1)). 0.0::knows_at(a, (b, 1, yellow3)). 0.0::knows_at(a, (b, 1, yellow4)). 0.0::knows_at(a, (b, 1, yellow5)).
% 0.0::knows_at(a, (b, 1, red1)). 0.0::knows_at(a, (b, 1, red2)). 0.0::knows_at(a, (b, 1, red3)). 0.0::knows_at(a, (b, 1, red4)). 0.0::knows_at(a, (b, 1, red5)).
1.0::knows_at(a, (b, 2, red3)). % 0.0::knows_at(a, (b, 2, red1)). 0.0::knows_at(a, (b, 2, red2)). 0.0::knows_at(a, (b, 2, red4)). 0.0::knows_at(a, (b, 2, red5)).
% 0.0::knows_at(a, (b, 2, yellow1)). 0.0::knows_at(a, (b, 2, yellow2)). 0.0::knows_at(a, (b, 2, yellow3)). 0.0::knows_at(a, (b, 2, yellow4)). 0.0::knows_at(a, (b, 2, yellow5)).
1.0::knows_at(a, (b, 3, yellow1)). % 0.0::knows_at(a, (b, 3, yellow2)). 0.0::knows_at(a, (b, 3, yellow3)). 0.0::knows_at(a, (b, 3, yellow4)). 0.0::knows_at(a, (b, 3, yellow5)).
% 0.0::knows_at(a, (b, 3, red1)). 0.0::knows_at(a, (b, 3, red2)). 0.0::knows_at(a, (b, 3, red3)). 0.0::knows_at(a, (b, 3, red4)). 0.0::knows_at(a, (b, 3, red5)).
1.0::knows_at(a, (b, 4, yellow4)). % 0.0::knows_at(a, (b, 4, yellow1)). 0.0::knows_at(a, (b, 4, yellow2)). 0.0::knows_at(a, (b, 4, yellow3)). 0.0::knows_at(a, (b, 4, yellow5)).
% 0.0::knows_at(a, (b, 4, red1)). 0.0::knows_at(a, (b, 4, red2)). 0.0::knows_at(a, (b, 4, red3)). 0.0::knows_at(a, (b, 4, red4)). 0.0::knows_at(a, (b, 4, red5)).
1.0::knows_at(a, (b, 5, yellow5)). % 0.0::knows_at(a, (b, 5, yellow1)). 0.0::knows_at(a, (b, 5, yellow2)). 0.0::knows_at(a, (b, 5, yellow3)). 0.0::knows_at(a, (b, 5, yellow4)).
% 0.0::knows_at(a, (b, 5, red1)). 0.0::knows_at(a, (b, 5, red2)). 0.0::knows_at(a, (b, 5, red3)). 0.0::knows_at(a, (b, 5, red4)). 0.0::knows_at(a, (b, 5, red5)).

/* 'b' possiede yellow5, e sappiamo che di 5 ce n'è solo 1 per ciascun colore. Quindi 'a' non ha 'yellow5'.
    Poiché ci sono 5 carte rosse e 4 carte gialle rimanenti (escludendo 'yellow5'),
    assegneremo una probabilità di 1/9 a ciascuna di queste carte. */

0.111111::knows_at(a, (a, 1, red1)). 0.111111::knows_at(a, (a, 1, red2)). 0.111111::knows_at(a, (a, 1, red3)). 0.111111::knows_at(a, (a, 1, red4)). 0.111111::knows_at(a, (a, 1, red5)).
0.111111::knows_at(a, (a, 1, yellow1)). 0.111111::knows_at(a, (a, 1, yellow2)). 0.111111::knows_at(a, (a, 1, yellow3)). 0.111111::knows_at(a, (a, 1, yellow4)). 0.0::knows_at(a, (a, 1, yellow5)).
0.111111::knows_at(a, (a, 2, red1)). 0.111111::knows_at(a, (a, 2, red2)). 0.111111::knows_at(a, (a, 2, red3)). 0.111111::knows_at(a, (a, 2, red4)). 0.111111::knows_at(a, (a, 2, red5)).
0.111111::knows_at(a, (a, 2, yellow1)). 0.111111::knows_at(a, (a, 2, yellow2)). 0.111111::knows_at(a, (a, 2, yellow3)). 0.111111::knows_at(a, (a, 2, yellow4)). 0.0::knows_at(a, (a, 2, yellow5)).
0.111111::knows_at(a, (a, 3, red1)). 0.111111::knows_at(a, (a, 3, red2)). 0.111111::knows_at(a, (a, 3, red3)). 0.111111::knows_at(a, (a, 3, red4)). 0.111111::knows_at(a, (a, 3, red5)).
0.111111::knows_at(a, (a, 3, yellow1)). 0.111111::knows_at(a, (a, 3, yellow2)). 0.111111::knows_at(a, (a, 3, yellow3)). 0.111111::knows_at(a, (a, 3, yellow4)). 0.0::knows_at(a, (a, 3, yellow5)).
0.111111::knows_at(a, (a, 4, red1)). 0.111111::knows_at(a, (a, 4, red2)). 0.111111::knows_at(a, (a, 4, red3)). 0.111111::knows_at(a, (a, 4, red4)). 0.111111::knows_at(a, (a, 4, red5)).
0.111111::knows_at(a, (a, 4, yellow1)). 0.111111::knows_at(a, (a, 4, yellow2)). 0.111111::knows_at(a, (a, 4, yellow3)). 0.111111::knows_at(a, (a, 4, yellow4)). 0.0::knows_at(a, (a, 4, yellow5)).
0.111111::knows_at(a, (a, 5, red1)). 0.111111::knows_at(a, (a, 5, red2)). 0.111111::knows_at(a, (a, 5, red3)). 0.111111::knows_at(a, (a, 5, red4)). 0.111111::knows_at(a, (a, 5, red5)).
0.111111::knows_at(a, (a, 5, yellow1)). 0.111111::knows_at(a, (a, 5, yellow2)). 0.111111::knows_at(a, (a, 5, yellow3)). 0.111111::knows_at(a, (a, 5, yellow4)). 0.0::knows_at(a, (a, 5, yellow5)).


%%% knows b %%%:
1.0::knows_at(b, (a, 1, red1)). % 0.0::knows_at(b, (a, 1, red2)). 0.0::knows_at(b, (a, 1, red3)). 0.0::knows_at(b, (a, 1, red4)). 0.0::knows_at(b, (a, 1, red5)).
% 0.0::knows_at(b, (a, 1, yellow1)). 0.0::knows_at(b, (a, 1, yellow2)). 0.0::knows_at(b, (a, 1, yellow3)). 0.0::knows_at(b, (a, 1, yellow4)). 0.0::knows_at(b, (a, 1, yellow5)).
1.0::knows_at(b, (a, 2, yellow3)). % 0.0::knows_at(b, (a, 2, yellow1)). 0.0::knows_at(b, (a, 2, yellow2)). 0.0::knows_at(b, (a, 2, yellow4)). 0.0::knows_at(b, (a, 2, yellow5)).
% 0.0::knows_at(b, (a, 2, red1)). 0.0::knows_at(b, (a, 2, red2)). 0.0::knows_at(b, (a, 2, red3)). 0.0::knows_at(b, (a, 2, red4)). 0.0::knows_at(b, (a, 2, red5)).
1.0::knows_at(b, (a, 3, yellow3)). % 0.0::knows_at(b, (a, 3, yellow1)). 0.0::knows_at(b, (a, 3, yellow2)). 0.0::knows_at(b, (a, 3, yellow4)). 0.0::knows_at(b, (a, 3, yellow5)).
% 0.0::knows_at(b, (a, 3, red1)). 0.0::knows_at(b, (a, 3, red2)). 0.0::knows_at(b, (a, 3, red3)). 0.0::knows_at(b, (a, 3, red4)). 0.0::knows_at(b, (a, 3, red5)).
1.0::knows_at(b, (a, 4, red2)). % 0.0::knows_at(b, (a, 4, red1)). 0.0::knows_at(b, (a, 4, red3)). 0.0::knows_at(b, (a, 4, red4)). 0.0::knows_at(b, (a, 4, red5)).
% 0.0::knows_at(b, (a, 4, yellow1)). 0.0::knows_at(b, (a, 4, yellow2)). 0.0::knows_at(b, (a, 4, yellow3)). 0.0::knows_at(b, (a, 4, yellow4)). 0.0::knows_at(b, (a, 4, yellow5)).
1.0::knows_at(b, (a, 5, yellow1)). % 0.0::knows_at(b, (a, 5, yellow2)). 0.0::knows_at(b, (a, 5, yellow3)). 0.0::knows_at(b, (a, 5, yellow4)). 0.0::knows_at(b, (a, 5, yellow5)).
% 0.0::knows_at(b, (a, 5, red1)). 0.0::knows_at(b, (a, 5, red2)). 0.0::knows_at(b, (a, 5, red3)). 0.0::knows_at(b, (a, 5, red4)). 0.0::knows_at(b, (a, 5, red5)).

0.1::knows_at(b, (b, 1, red1)). 0.1::knows_at(b, (b, 1, red2)). 0.1::knows_at(b, (b, 1, red3)). 0.1::knows_at(b, (b, 1, red4)). 0.1::knows_at(b, (b, 1, red5)).
0.1::knows_at(b, (b, 1, yellow1)). 0.1::knows_at(b, (b, 1, yellow2)). 0.1::knows_at(b, (b, 1, yellow3)). 0.1::knows_at(b, (b, 1, yellow4)). 0.1::knows_at(b, (b, 1, yellow5)).
0.1::knows_at(b, (b, 2, red1)). 0.1::knows_at(b, (b, 2, red2)). 0.1::knows_at(b, (b, 2, red3)). 0.1::knows_at(b, (b, 2, red4)). 0.1::knows_at(b, (b, 2, red5)).
0.1::knows_at(b, (b, 2, yellow1)). 0.1::knows_at(b, (b, 2, yellow2)). 0.1::knows_at(b, (b, 2, yellow3)). 0.1::knows_at(b, (b, 2, yellow4)). 0.1::knows_at(b, (b, 2, yellow5)).
0.1::knows_at(b, (b, 3, red1)). 0.1::knows_at(b, (b, 3, red2)). 0.1::knows_at(b, (b, 3, red3)). 0.1::knows_at(b, (b, 3, red4)). 0.1::knows_at(b, (b, 3, red5)).
0.1::knows_at(b, (b, 3, yellow1)). 0.1::knows_at(b, (b, 3, yellow2)). 0.1::knows_at(b, (b, 3, yellow3)). 0.1::knows_at(b, (b, 3, yellow4)). 0.1::knows_at(b, (b, 3, yellow5)).
0.1::knows_at(b, (b, 4, red1)). 0.1::knows_at(b, (b, 4, red2)). 0.1::knows_at(b, (b, 4, red3)). 0.1::knows_at(b, (b, 4, red4)). 0.1::knows_at(b, (b, 4, red5)).
0.1::knows_at(b, (b, 4, yellow1)). 0.1::knows_at(b, (b, 4, yellow2)). 0.1::knows_at(b, (b, 4, yellow3)). 0.1::knows_at(b, (b, 4, yellow4)). 0.1::knows_at(b, (b, 4, yellow5)).
0.1::knows_at(b, (b, 5, red1)). 0.1::knows_at(b, (b, 5, red2)). 0.1::knows_at(b, (b, 5, red3)). 0.1::knows_at(b, (b, 5, red4)). 0.1::knows_at(b, (b, 5, red5)).
0.1::knows_at(b, (b, 5, yellow1)). 0.1::knows_at(b, (b, 5, yellow2)). 0.1::knows_at(b, (b, 5, yellow3)). 0.1::knows_at(b, (b, 5, yellow4)). 0.1::knows_at(b, (b, 5, yellow5)).


% Inizializzazione delle disponibilità degli indizi
init_hint_and_mistakes :-
    % In accordo coi modelli, qui dovremo usare 5 hints e max 3 life tokens
	assertz(mistakes_committed(0)),
    assertz(hints_available(5)).

% Azione di suggerimento sul colore. Dice a "Player" quali delle sue carte sono di colore "Color" (es. la carta 1 e 3 sono Red)
hint_color(Player, HintedColor, GLOBAL_COUNTER) :-
    (
        hints_available(Hints),
        Hints > 0,
        between(1, 5, Index),
        at(Player, Index, Card),

        % Se la carta non è vuota ed è del colore consigliato, allora teoricamente aggiorno la conoscenza.
        % In realtà non avviene alcuna modifica oltre agli hints, perché di tali modifiche si occupa HCIC.
        Card \= -,
        color(Card, CardColor),
        CardColor = HintedColor,

        writeln('Player',Player,'has been hinted: card in index',Index,'has color',HintedColor),

        % NOTA: questo predicato sarà invocato solo una volta, come vogliamo (non dobbiamo decrementare più di 1 indizio).
        % Il motivo è che non cambia GLOBAL_COUNTER e quindi il predicato può valere al più 1 volta
        decrement_hints(GLOBAL_COUNTER)
    );
    true.


% Dice a "Player" quali delle sue carte sono di rank "HintedRank" (es. la carta 2 e 3 sono di rank 1)
hint_rank(Player, HintedRank, GLOBAL_COUNTER) :-
    (
        hints_available(Hints),
        Hints > 0,

        between(1, 5, Index), % Itero sui possibili indici di carte, da 1 a 5
        at(Player, Index, Card), % Verifico che il giocatore abbia in questo Index una Card
        Card \= -, % Verifico che Card sia non vuota
        rank(Card, Rank), % Recupero il rank di questa Card
        Rank = HintedRank, % Verifico che il Rank di questa Card sia lo stesso del Rank suggerito

        /* Se la carta non è vuota e il suo numero corrisponde al suggerimento,
           allora posso teoricamente aggiornare la conoscenza del giocatore.
           In realtà non avviene alcuna modifica oltre agli hints, perché di tali modifiche si occupa HCIC. */
        writeln('Player',Player,'has been hinted: card in index',Index,'has rank',HintedRank),

        % NOTA: questo predicato sarà invocato solo una volta, come vogliamo (non dobbiamo decrementare più di 1 indizio).
        % Il motivo è che non cambia GLOBAL_COUNTER e quindi il predicato può valere al più 1 volta
        decrement_hints(GLOBAL_COUNTER)
    );
    true.


% Funzione per giocare una carta
play_card(Player, Index, GLOBAL_COUNTER) :-
    play_card_helper(Player, Index, GLOBAL_COUNTER);
    (
        % Questo è il caso in cui giochiamo una carta ma il suo colore appartiene a uno stack già completato
        not(play_card_helper(Player, Index, GLOBAL_COUNTER)),

        at(Player, Index, Card),
        Card \= -,
        color(Card, Color),
        findall(StackIndex, stack(Color, StackIndex, -), StackIndices),
        StackIndices = [],

        write('Stack is full!! Player "'), write(Player), writeln('" committed a mistake!!! Incrementing mistake counter.'),
        increment_mistakes(GLOBAL_COUNTER),

        % Rimuovi la carta dal fatto at/3, e aggiungila al discarded deck (true)
        write('Player "'), write(Player), writeln('" discards card', Card),
        discard_card(Player, Index, true, GLOBAL_COUNTER)
    );
    true.

play_card_helper(Player, Index, GLOBAL_COUNTER) :-
    (
        at(Player, Index, Card),
        Card \= -, % Mi assicuro che in Index player abbia una carta valida e non vuota
        write('Player "'), write(Player), writeln('" plays card', Card),

        color(Card, Color),

        % Verifico se esiste nello stack un Index relativo a carta vuota; se sì, uso il primo Index per inserire Card
        findall(StackIndex, stack(Color, StackIndex, -), StackIndices),

        % Verifica se c'è almeno un indice valido nello stack
        \+ StackIndices = [],

        % Prendiamo l'indice della prima carta vuota trovata
        nth0(0, StackIndices, FirstEmptyStackIndex),
        rank(Card, CardRank),

        % Se la prima posizione libera nello stack è quella di indice 1, allora devo giocare una carta di rank 1
        ((
            % Nota: i seguenti 3 OR sono mutuamente esclusivi, per cui solo 1 verrà eseguito
            ((
             FirstEmptyStackIndex = 1,
             CardRank = 1
            );
            (
             (FirstEmptyStackIndex = 2; FirstEmptyStackIndex = 3; FirstEmptyStackIndex = 4),
             PreviousPlayedCardIndex is FirstEmptyStackIndex - 1,
             stack(Color, PreviousPlayedCardIndex, PreviousPlayedCard),
             rank(PreviousPlayedCard, PreviousPlayedCardRank),
             % Chiediamoci se la carta corrente abbia CardRank = PreviousPlayedCardRank + 1
             CardRank =:= PreviousPlayedCardRank + 1
            );
            (
             FirstEmptyStackIndex = 5,
             CardRank = 5,
             writeln('Congrats! Player', Player, 'has completed', Color, 'firework!'),
             % Incrementiamo gli indizi disponibili, nel caso in cui gli indizi correnti fossero < 5
             (increment_hints(GLOBAL_COUNTER); true)
            )),

            retract(stack(Color, FirstEmptyStackIndex, -)),
            assertz(stack(Color, FirstEmptyStackIndex, Card)),

            write('Player "'), write(Player), write('" successfully placed card "'), write(Card), writeln('" on top of', Color, 'stack.'),

            % Rimuovi la carta dal fatto at/3, ma non aggiungerla al discarded deck (false)
            discard_card(Player, Index, false, GLOBAL_COUNTER)
        );
        (
            % Siccome ProbLog esegue tutti i rami dell'OR, mi chiedo se la condizione di prima è fallita.
            % In questo modo, so che se è fallita allora posso proseguire, altrimenti mi fermo anche in questo ramo.
            not((
               (
                   FirstEmptyStackIndex = 1,
                   CardRank = 1
               );
               (
                   (FirstEmptyStackIndex = 2; FirstEmptyStackIndex = 3; FirstEmptyStackIndex = 4),
                    PreviousPlayedCardIndex is FirstEmptyStackIndex - 1,
                    stack(Color, PreviousPlayedCardIndex, PreviousPlayedCard),
                    rank(PreviousPlayedCard, PreviousPlayedCardRank),
                    % Chiediamoci se la carta corrente abbia CardRank = PreviousPlayedCardRank + 1
                    CardRank =:= PreviousPlayedCardRank + 1
               );
               (
                   FirstEmptyStackIndex = 5,
                   CardRank = 5
               )
            )),

            % Se sono qui, è stato commesso un mistake, per cui incremento gli errori globali commessi
            write('Player "'), write(Player), writeln('" committed a mistake!!! Incrementing mistake counter.'),
            increment_mistakes(GLOBAL_COUNTER),

            % Rimuovi la carta dal fatto at/3, e aggiungila al discarded deck (true)
            write('Player "'), write(Player), writeln('" discards card', Card),
            discard_card(Player, Index, true, GLOBAL_COUNTER)
        ))
    ).

/* Funzione per pescare una carta.
   L'azione di pescare una nuova carta è consentita solamente quando si
   effettua "play a card" (a prescindere dall'esito) e quando si effettua "discard a card". */
draw_card(Player, GLOBAL_COUNTER) :-
    (
        % Verifica se c'è una carta nel mazzo da pescare, ossia una carta non vuota, \= -
        findall(DeckIndex, (deck(DeckIndex, Card), Card \= -), DeckIndices),
        % Verifica se c'è almeno un indice valido nel deck
        \+ DeckIndices = [],
        % Prendiamo l'indice della prima carta non vuota trovata
        nth0(0, DeckIndices, FirstDeckIndex),

        % Verifica se il giocatore ha almeno una carta = "-"
        findall(PlayerIndex, at(Player, PlayerIndex, -), PlayerIndices),
        % Verifica se c'è almeno un indice valido nel deck
        \+ PlayerIndices = [],
        % Prendiamo l'indice della prima carta non vuota trovata
        nth0(0, PlayerIndices, FirstPlayerIndex),

        % Rimuovi la carta dal mazzo
        deck(FirstDeckIndex, Card),
        retract(deck(FirstDeckIndex, Card)),
        assertz(deck(FirstDeckIndex, -)),

        % Aggiungi la carta alla mano del giocatore
        retract(at(Player, FirstPlayerIndex, -)),
        assertz(at(Player, FirstPlayerIndex, Card)),

        % Non aggiorno le probabilità di knows_at perché in teoria di quello si occuperà il modulo HCIC

        write('Player "'), write(Player), write('" drew card "'), write(Card), write('" and put it in his hand at position '), write(FirstPlayerIndex),
        writeln('. This card was drawn from position', FirstDeckIndex, 'of the deck.')
    );
    true.


% Funzione per scartare una carta. Deve essere richiamata da play_card.
discard_card(Player, Index, AddCardToDiscardedDeck, GLOBAL_COUNTER) :-
    (
        at(Player, Index, Card),
        Card \= -,

        % La carta non è vuota, potrei ora impostare la probabilità a 0.0 di knows_at(Player, (Player, Index, Card))
        % Tuttavia, è il modulo HCIC che si occuperà di visionare quanto accaduto e di aggiornare queste probabilità

        knows_at(Player, (Player, Index, Card)),

        % Non devo cambiare le probabilità di "knows_at" relative alla carta scartata, se ne occupa HCIC

        % Rimuovo il fatto "at" e lo reinizializzo
        retract(at(Player, Index, Card)),
        assertz(at(Player, Index, -)),

        % Se AddCardToDiscardedDeck, allora la carta scartata va aggiunta al discarded deck (altrimenti va nello stack)
        ((AddCardToDiscardedDeck,
         % Aggiorno discarded_deck(CardList[])
         discarded_deck(OldDiscardedDeck),  % Otteniamo la lista attuale delle carte scartate
         retract(discarded_deck(_)),
         append(OldDiscardedDeck, [Card], NewDiscardedDeck),  % Aggiungiamo la nuova carta alla fine della lista
         assertz(discarded_deck(NewDiscardedDeck)),

         % Stampa il nuovo discarded deck
         discarded_deck(TestDiscardedDeck),
         write('New discarded deck is now: '),
         writeln(TestDiscardedDeck)
        ) ; true),

        % Dopo aver scartato una carta, se possibile, pesco una carta.
        draw_card(Player, GLOBAL_COUNTER)
    );

    % Se una delle precedenti condizioni fallisse, noi comunque vogliamo continuare l'esecuzione.
    true.


/* Funzione per scartare una carta. In questa variante, descriviamo l'azione di scartare una carta senza averla giocata,
   ossia una delle possibili 4 azioni. Questa funzione pertanto non deve essere richiamata da play_card.
   Questa azione restituisce un hint token, e pertanto non può essere eseguita se il numero di Hints è già massimo. */
discard_card_action(Player, Index, GLOBAL_COUNTER) :-
    (
        hints_available(Hints),
        Hints < 5,

        % Verifica se c'è una carta nel mazzo da pescare, ossia una carta non vuota, \= -
        findall(DeckIndex, (deck(DeckIndex, Card), Card \= -), DeckIndices),
        % Verifica se c'è almeno un indice valido nel deck
        \+ DeckIndices = [],

        at(Player, Index, Card),
        Card \= -,

        increment_hints(GLOBAL_COUNTER),

        % La carta non è vuota, potrei ora impostare la probabilità a 0.0 di knows_at(Player, (Player, Index, Card))
        % Tuttavia, è il modulo HCIC che si occuperà di visionare quanto accaduto e di aggiornare queste probabilità

        knows_at(Player, (Player, Index, Card)),

        % Non devo cambiare le probabilità di "knows_at" relative alla carta scartata, se ne occupa HCIC

        % Rimuovo il fatto "at" e lo reinizializzo
        retract(at(Player, Index, Card)),
        assertz(at(Player, Index, -)),

        % La carta scartata va aggiunta al discarded deck
        % Aggiorno discarded_deck(CardList[])
        discarded_deck(OldDiscardedDeck),  % Otteniamo la lista attuale delle carte scartate
        retract(discarded_deck(_)),
        append(OldDiscardedDeck, [Card], NewDiscardedDeck),  % Aggiungiamo la nuova carta alla fine della lista
        assertz(discarded_deck(NewDiscardedDeck)),

        % Stampa il nuovo discarded deck
        discarded_deck(TestDiscardedDeck),
        write('New discarded deck is now: '),
        writeln(TestDiscardedDeck),

        % Dopo aver scartato una carta, pesco una carta.
        draw_card(Player, GLOBAL_COUNTER)
    );

    % Se una delle precedenti condizioni fallisse, noi comunque vogliamo continuare l'esecuzione.
    true.


% Funzione che restituisce True se la carta è giocabile su un Firework corrente, False altrimenti.
card_is_playable(Player, Index, GLOBAL_COUNTER) :-
    (
        at(Player, Index, Card),
        Card \= -, % Mi assicuro che in Index player abbia una carta valida e non vuota
        color(Card, Color),

        % Verifico se esiste nello stack un Index relativo a carta vuota; se sì, uso il primo Index per inserire Card
        findall(StackIndex, stack(Color, StackIndex, -), StackIndices),

        % Verifica se c'è almeno un indice valido nello stack
        \+ StackIndices = [],

        % Prendiamo l'indice della prima carta vuota trovata
        nth0(0, StackIndices, FirstEmptyStackIndex),
        rank(Card, CardRank),

        % Mi chiedo semplicemente se CardRank >= FirstEmptyStackIndex. Se sì, allora la carta è giocabile, anche se non necessariamente ora.
        % Nota: CardRank >= FirstEmptyStackIndex e non >, perché se pos.2 ad es. è libera, il rank 2 è giocabile.
        CardRank >= FirstEmptyStackIndex
    ).

card_is_playable_now(Player, Index, GLOBAL_COUNTER) :-
    (
        at(Player, Index, Card),
        Card \= -, % Mi assicuro che in Index player abbia una carta valida e non vuota
        color(Card, Color),

        % Verifico se esiste nello stack un Index relativo a carta vuota; se sì, uso il primo Index per inserire Card
        findall(StackIndex, stack(Color, StackIndex, -), StackIndices),

        % Verifica se c'è almeno un indice valido nello stack
        \+ StackIndices = [],

        % Prendiamo l'indice della prima carta vuota trovata
        nth0(0, StackIndices, FirstEmptyStackIndex),
        rank(Card, CardRank),

        % Mi chiedo semplicemente se CardRank = FirstEmptyStackIndex. Se sì, allora la carta è giocabile, ma solamente per ora.
        CardRank =:= FirstEmptyStackIndex
    ).


% Stampa tutte le carte in mano al giocatore Player
print_hand(Player, GLOBAL_COUNTER) :-
    (
        write('Cards in hand of '), write(Player), write(': '), nl,
        % Non specifico Index e Card, in questo modo il codice da qui in poi verrà eseguito per ogni possibile combinazione
        at(Player, Index, Card),
        Card \= -,
        write('Index '), write(Index), write(': '), write(Card), nl
    );
    true.


% Stampa tutte le carte nel deck
print_deck(GLOBAL_COUNTER) :-
    (
        write('Cards in the deck: '), nl,
        deck(Index, Card),
        Card \= -,
        write(Index, ':', Card), nl
    );
    true.


% Aggiornamento del numero di errori commessi
increment_mistakes(GLOBAL_COUNTER) :-
    (
        mistakes_committed(CurrentMistakes),
        NewMistakes is CurrentMistakes + 1,
        retract(mistakes_committed(_)),
        assertz(mistakes_committed(NewMistakes))
    );
    true.


decrement_hints(GLOBAL_COUNTER) :-
    (
        hints_available(Hints),
        NewHints is Hints - 1,
        retract(hints_available(_)),
        assertz(hints_available(NewHints))
        % writenl('Hints decremented, now there are', NewHints, 'hints left.'), nl.
    );
    true.


increment_hints(GLOBAL_COUNTER) :-
    (
        hints_available(Hints),
        Hints < 5, % Non possiamo aggiungere un Hint se ne abbiamo già 5, il massimo.
        NewHints is Hints + 1,
        retract(hints_available(_)),
        assertz(hints_available(NewHints)),
        writenl('Hints counter incremented, now there are', NewHints, 'hints available.')
    );
    true.

is_game_over :-
    mistakes_committed(CurrentMistakes),
    % Se CurrentMistakes supera 3, allora il gioco è finito
    (CurrentMistakes > 3;
     % Oppure se il CurrentMistakes è <= 3, ma i top stack sono stati riempiti, il gioco è finito
     (
      CurrentMistakes =< 3,
      stack(red, 5, TopRedStack),
      stack(yellow, 5, TopYellowStack),
      TopRedStack \= -,
      TopYellowStack \= -
     )
    );
    % Altrimenti il gioco non è finito
    false.

main :-
    nl, writeln('# -------------------- Hanabi KB -------------------- #'), nl,
    init_hint_and_mistakes.

:- main.


% Predicato per ottenere il numero di carte rimaste nel mazzo.
remaining_deck_size(Size) :-
    findall(DeckIndex, (deck(DeckIndex, Card), Card \= -), DeckIndices),
    length(DeckIndices, Size).

% -----------------------------------------------------------------------------------------------
% Predicati per alterare la probabilità delle azioni in base allo stato del mondo
0.0::alter_hint_color_decksize(0).
0.0::alter_hint_color_decksize(1).
0.0::alter_hint_color_decksize(2).
0.0::alter_hint_color_decksize(3).
0.0::alter_hint_color_decksize(4).
0.1::alter_hint_color_decksize(5).
0.1::alter_hint_color_decksize(6).
0.1::alter_hint_color_decksize(7).
0.1::alter_hint_color_decksize(8).
0.1::alter_hint_color_decksize(9).
0.1::alter_hint_color_decksize(10).
% ---------------------------------
0.0::alter_hint_rank_decksize(0).
0.0::alter_hint_rank_decksize(1).
0.0::alter_hint_rank_decksize(2).
0.0::alter_hint_rank_decksize(3).
0.0::alter_hint_rank_decksize(4).
0.1::alter_hint_rank_decksize(5).
0.1::alter_hint_rank_decksize(6).
0.1::alter_hint_rank_decksize(7).
0.1::alter_hint_rank_decksize(8).
0.1::alter_hint_rank_decksize(9).
0.1::alter_hint_rank_decksize(10).
% ---------------------------------
0.6::alter_play_decksize(0).
0.6::alter_play_decksize(1).
0.4::alter_play_decksize(2).
0.4::alter_play_decksize(3).
0.3::alter_play_decksize(4).
0.3::alter_play_decksize(5).
0.2::alter_play_decksize(6).
0.2::alter_play_decksize(7).
0.1::alter_play_decksize(8).
0.1::alter_play_decksize(9).
0.0::alter_play_decksize(10).
% ---------------------------------
0.0::alter_hint_playablecards(0).
0.05::alter_hint_playablecards(1).
0.1::alter_hint_playablecards(2).
0.1::alter_hint_playablecards(3).
0.2::alter_hint_playablecards(4).
0.2::alter_hint_playablecards(5).
% ---------------------------------
0.0::alter_hint_hinttokens(0).
0.05::alter_hint_hinttokens(1).
0.05::alter_hint_hinttokens(2).
0.1::alter_hint_hinttokens(3).
0.1::alter_hint_hinttokens(4).
0.1::alter_hint_hinttokens(5).
% 0.1::alter_hint_hinttokens(6).
% 0.2::alter_hint_hinttokens(7).
% 0.2::alter_hint_hinttokens(8).
% ---------------------------------
0.2::alter_play_hinttokens(0).
0.18::alter_play_hinttokens(1).
0.15::alter_play_hinttokens(2).
0.08::alter_play_hinttokens(3).
0.05::alter_play_hinttokens(4).
0.03::alter_play_hinttokens(5).
% 0.0::alter_play_hinttokens(6).
% 0.0::alter_play_hinttokens(7).
% 0.0::alter_play_hinttokens(8).
% ---------------------------------
0.2::alter_discard_hinttokens(0).
0.15::alter_discard_hinttokens(1).
0.1::alter_discard_hinttokens(2).
0.05::alter_discard_hinttokens(3).
0.05::alter_discard_hinttokens(4).
0.0::alter_discard_hinttokens(5).
% 0.1::alter_discard_hinttokens(6).
% 0.0::alter_discard_hinttokens(7).
% 0.0::alter_discard_hinttokens(8).
% ---------------------------------
0.0::alter_discard_decksize(0).
0.0::alter_discard_decksize(1).
0.0::alter_discard_decksize(2).
0.1::alter_discard_decksize(3).
0.1::alter_discard_decksize(4).
0.1::alter_discard_decksize(5).
0.15::alter_discard_decksize(6).
0.15::alter_discard_decksize(7).
0.2::alter_discard_decksize(8).
0.2::alter_discard_decksize(9).
0.2::alter_discard_decksize(10).
% ---------------------------------
% Con questo predicato codifichiamo l'idea secondo cui se si scarta una carta che è giocabile, allora si vuole penalizzare
% tale azione. Per farlo, siccome questo predicato è pensato per essere usato con un AND, allora l'idea è di dare
% valori probabilistici più alti per penalizzare meno, e più bassi per penalizzare di più, in quanto AND = Prodotto.
% Per il rank 5, sarebbe sicuramente insensato scartare quella carta, per cui daremo 0.0.
0.85::alter_discard_prob_playable_card(1).  % Di 1 ne abbiamo tre per ciascun colore, penalizziamo di poco.
0.5::alter_discard_prob_playable_card(2).  % Di 2, 3, 4 ce ne sono due per ciascun colore. Dimezziamo la prob. con 0.5
0.5::alter_discard_prob_playable_card(3).
0.5::alter_discard_prob_playable_card(4).
0.0::alter_discard_prob_playable_card(5).  % Di 5 ne abbiamo solamente uno per ciascun colore, non bisogna mai scartarli.
% -----------------------------------------------------------------------------------------------

% red_idx() è dato dalla somma delle probabilità (OR) di knows_at. Più è alta questa probabilità,
% maggiore è probabile che quel giocatore creda effettivamente di possedere un rosso.
% Nota: non è proprio una somma, qui si usa Inferenza a Massima Probabilità (MAP), per cui ad es. 0.1+0.1+0.1 = 1 - (1-0.1)^3 = 0.271
red_idx(Player, Index) :-
    knows_at(Player, (Player, Index, red1));
    knows_at(Player, (Player, Index, red2));
    knows_at(Player, (Player, Index, red3));
    knows_at(Player, (Player, Index, red4));
    knows_at(Player, (Player, Index, red5)).

% Regola generale per verificare se un giocatore sa di avere una carta gialla in un dato indice
yellow_idx(Player, Index) :-
    knows_at(Player, (Player, Index, yellow1));
    knows_at(Player, (Player, Index, yellow2));
    knows_at(Player, (Player, Index, yellow3));
    knows_at(Player, (Player, Index, yellow4));
    knows_at(Player, (Player, Index, yellow5)).

% Predicato per dimezzare una probabilità
0.5::half_prob.

% Valuta quanto si è indecisi relativamente al fatto di avere quel colore suggerito in quell'index
color_uncertainty(Player, Index) :-
    at(Player, Index, Card),
    ((color(Card, red), \+ red_idx(Player, Index));
    (color(Card, yellow), \+ yellow_idx(Player, Index))),
    % Dimezziamo la prob. di red_idx o yellow_idx che è in genere troppo alta
    half_prob.

% Valuta quanto si è indecisi relativamente al fatto di avere quel rank suggerito in quell'index
rank_uncertainty(Player, Index, Rank) :-
    at(Player, Index, Card),
    rank(Card, Rank),
    \+ rank_idx(Player, Index, Rank),
    % Dimezziamo la prob. di rank_idx che è in genere troppo alta
    half_prob.

% Calcola la probabilità (la credenza di Player) di avere una carta di Rank in posizione Index
rank_idx(Player, Index, Rank) :-
    (Rank = 1, at(Player, Index, Card), ((color(Card, red), knows_at(Player, (Player, Index, red1)));
                                         (color(Card, yellow), knows_at(Player, (Player, Index, yellow1)))));
    (Rank = 2, at(Player, Index, Card), ((color(Card, red), knows_at(Player, (Player, Index, red2)));
                                         (color(Card, yellow), knows_at(Player, (Player, Index, yellow2)))));
    (Rank = 3, at(Player, Index, Card), ((color(Card, red), knows_at(Player, (Player, Index, red3)));
                                         (color(Card, yellow), knows_at(Player, (Player, Index, yellow3)))));
    (Rank = 4, at(Player, Index, Card), ((color(Card, red), knows_at(Player, (Player, Index, red4)));
                                         (color(Card, yellow), knows_at(Player, (Player, Index, yellow4)))));
    (Rank = 5, at(Player, Index, Card), ((color(Card, red), knows_at(Player, (Player, Index, red5)));
                                         (color(Card, yellow), knows_at(Player, (Player, Index, yellow5))))).

% Predicato per iterare sugli indici di carte che hanno il colore suggerito e valutarne l'incertezza con un OR (somma)
% check_color_uncertainties(OtherPlayer, [Index | Rest]) :-
%     Index @>= 1,
%     Index @=< 5,
%     (color_uncertainty(OtherPlayer, Index) ; check_color_uncertainties(OtherPlayer, Rest)).

% Predicato per iterare sugli indici di carte che hanno il rank suggerito e valutarne l'incertezza con un OR (somma)
% check_rank_uncertainties(OtherPlayer, [Index | Rest], Rank) :-
%     Index @>= 1,
%     Index @=< 5,
%     (rank_uncertainty(OtherPlayer, Index, Rank) ; check_rank_uncertainties(OtherPlayer, Rest, Rank)).

% Predicato per calcolare il guadagno del dare un hint color.
hint_color_probability(Player, OtherPlayer, Color) :-
    % Ottengo il numero di carte giocabili del colore suggerito.
    get_number_of_hinted_color_cards_playable(OtherPlayer, Color, NumColoredCards),
    % Ottengo il numero di carte rimaste nel mazzo.
    remaining_deck_size(DeckSize),
    % Ottengo il numero di info tokens.
    hints_available(Hints),

    findall(Index, (at(OtherPlayer, Index, Card), color(Card, CardColor), CardColor = Color), Indices),
    nth0(0, Indices, FirstIndex),
    % (check_color_uncertainties(OtherPlayer, Indices);
    (color_uncertainty(OtherPlayer, FirstIndex);
    alter_hint_playablecards(NumColoredCards);
    alter_hint_color_decksize(DeckSize);
    alter_hint_hinttokens(Hints)).

% Predicato per calcolare il guadagno del dare un hint rank.
hint_rank_probability(Player, OtherPlayer, Rank) :-
    % Ottengo il numero di carte giocabili del rank suggerito.
    get_number_of_hinted_rank_cards_playable(OtherPlayer, Rank, NumRankedCards),
    % Ottengo il numero di carte rimaste nel mazzo.
    remaining_deck_size(DeckSize),
    % Ottengo il numero di info tokens.
    hints_available(Hints),

    findall(Index, (at(OtherPlayer, Index, Card), rank(Card, CardRank), CardRank = Rank), Indices),
    nth0(0, Indices, FirstIndex),
    % (check_rank_uncertainties(OtherPlayer, Indices, Rank);
    (rank_uncertainty(OtherPlayer, FirstIndex, Rank);
    alter_hint_playablecards(NumRankedCards);
    alter_hint_rank_decksize(DeckSize);
    alter_hint_hinttokens(Hints)).


get_top_rank_of_firework(Color, LastRank) :-
    findall(StackIndex, (stack(Color, StackIndex, Card), Card \= -), StackIndices),
    ((StackIndices \= [], last(StackIndices, LastRank));
      StackIndices = [], LastRank is 0).

play_card_probability(Player, Index, ID) :-
    % Prima di ragionarci, vediamo innanzitutto se la carta sia immediatamente giocabile
    card_is_playable_now(Player, Index, ID),

    % Ottengo il numero di carte rimaste nel mazzo
    remaining_deck_size(DeckSize),
    % Ottengo il numero di info tokens
    hints_available(Hints),

    % A questo punto, guardiamo nel top dello stack red e yellow e vediamo quali sono le carte giocabili.
    % Ad es., se c'è R2 e Y4 negli stack, allora considererò solamente le probabilità di R3 e Y5 in questo Index.
    get_top_rank_of_firework(red, LastRedRank),
    get_top_rank_of_firework(yellow, LastYellowRank),

    % Almeno uno tra LastRedRank e LastYellowRank non è uguale a 5, altrimenti not(is_game_over) sarebbe stato falso.
    % Se entrambi sono diversi da 5, considero le credenze per entrambi gli stacks, altrimenti solamente per uno.
    (
      (
        (LastRedRank \= 5, LastYellowRank \= 5,
          ((knows_at(Player, (Player, Index, Card)), color(Card, red), rank(Card, CardRank), CardRank =:= LastRedRank + 1);
          (knows_at(Player, (Player, Index, Card)), color(Card, yellow), rank(Card, CardRank), CardRank =:= LastYellowRank + 1))
        );
        (LastRedRank \= 5, LastYellowRank = 5,
          (knows_at(Player, (Player, Index, Card)), color(Card, red), rank(Card, CardRank), CardRank =:= LastRedRank + 1)
        );
        (LastYellowRank \= 5, LastRedRank = 5,
          (knows_at(Player, (Player, Index, Card)), color(Card, yellow), rank(Card, CardRank), CardRank =:= LastYellowRank + 1)
        )
      );
      % Alteriamo ora la probabilità ottenuta con questi due fatti probabilistici
      alter_play_hinttokens(Hints);
      alter_play_decksize(DeckSize)
    ).


discard_card_probability(Player, Index, ID) :-
    % Ottengo il numero di carte rimaste nel mazzo
    remaining_deck_size(DeckSize),
    % Ottengo il numero di info tokens
    hints_available(Hints),

    % A questo punto, guardiamo nel top dello stack red e yellow e vediamo quali sono le carte giocabili
    get_top_rank_of_firework(red, LastRedRank),
    get_top_rank_of_firework(yellow, LastYellowRank),

    % Come per play_card_probability(), anche qui almeno uno tra LastRedRank e LastYellowRank non è uguale a 5
    (
      (
        (LastRedRank \= 5, LastYellowRank \= 5,
          (((knows_at(Player, (Player, Index, red1)),
           % Se il rank che voglio scartare non è giocabile, nessun problema. Se è giocabile, penalizzo in base al rank.
           % La penalizzazione avviene con l'and, che consiste in un prodotto che abbasserà la probabilità corrente.
           (1 =< LastRedRank; alter_discard_prob_playable_card(1)));
           (knows_at(Player, (Player, Index, red2)),
           (2 =< LastRedRank; alter_discard_prob_playable_card(2)));
           (knows_at(Player, (Player, Index, red3)),
           (3 =< LastRedRank; alter_discard_prob_playable_card(3)));
           (knows_at(Player, (Player, Index, red4)),
           (4 =< LastRedRank; alter_discard_prob_playable_card(4)))),
            % Penalizzo in AND in base a quanto è probabile che ho un rank 5. Siccome tanto più è alto il numero più
            % il prodotto penalizza, allora considero il complemento di questa probabilità.
            \+ knows_at(Player, (Player, Index, red5))
          );
          (((knows_at(Player, (Player, Index, yellow1)),
           (1 =< LastYellowRank; alter_discard_prob_playable_card(1)));
           (knows_at(Player, (Player, Index, yellow2)),
           (2 =< LastYellowRank; alter_discard_prob_playable_card(2)));
           (knows_at(Player, (Player, Index, yellow3)),
           (3 =< LastYellowRank; alter_discard_prob_playable_card(3)));
           (knows_at(Player, (Player, Index, yellow4)),
           (4 =< LastYellowRank; alter_discard_prob_playable_card(4)))),
            \+ knows_at(Player, (Player, Index, yellow5))
          )
        );
        (LastRedRank \= 5, LastYellowRank = 5,
          (((knows_at(Player, (Player, Index, red1)),
           % Se il rank che voglio scartare non è giocabile, nessun problema. Se è giocabile, penalizzo in base al rank.
           % La penalizzazione avviene con l'and, che consiste in un prodotto che abbasserà la probabilità corrente.
           (1 =< LastRedRank; alter_discard_prob_playable_card(1)));
           (knows_at(Player, (Player, Index, red2)),
           (2 =< LastRedRank; alter_discard_prob_playable_card(2)));
           (knows_at(Player, (Player, Index, red3)),
           (3 =< LastRedRank; alter_discard_prob_playable_card(3)));
           (knows_at(Player, (Player, Index, red4)),
           (4 =< LastRedRank; alter_discard_prob_playable_card(4)))),
            \+ knows_at(Player, (Player, Index, red5))  % Penalizzo in AND in base a quanto è probabile che ho un rank 5
          )
        );
        (LastYellowRank \= 5, LastRedRank = 5,
          (((knows_at(Player, (Player, Index, yellow1)),
           (1 =< LastYellowRank; alter_discard_prob_playable_card(1)));
           (knows_at(Player, (Player, Index, yellow2)),
           (2 =< LastYellowRank; alter_discard_prob_playable_card(2)));
           (knows_at(Player, (Player, Index, yellow3)),
           (3 =< LastYellowRank; alter_discard_prob_playable_card(3)));
           (knows_at(Player, (Player, Index, yellow4)),
           (4 =< LastYellowRank; alter_discard_prob_playable_card(4)))),
            \+ knows_at(Player, (Player, Index, yellow5))
          )
        )
      );
      % Alteriamo ora la probabilità ottenuta con questi due fatti probabilistici
      alter_discard_hinttokens(Hints);
      alter_discard_decksize(DeckSize)
    ).


/*
Dobbiamo scegliere la miglior azione da eseguire:
    - HINT: dobbiamo capire se ci conviene dare un indizio, per farlo cerchiamo di capire l'utilità di darne uno.
       - HINT RANK: qui vediamo quante carte (ranks) consigliamo al giocatore 2, tuttavia non ci limitiamo a questo;
                    possiamo considerare le probabilità di HCIC e calcolare con qualche formula l'utilità o il guadagno
                    dato dal suggerire dei rank a quel giocatore, considerate le probabilità che lui crede di avere
                    sulla base delle osservazioni del gioco (HCIC G2). Il guadagno è inversamente proporzionale
                    alle probabilità, ossia più ha probabilità basse per un certo rank che però è realmente nella sua
                    mano, maggiore sarà il guadagno probabilisticamente parlando di dare quell'indizio. Aumentare lo score
                    in modo inversamente proporzionale a quante carte sono rimaste nel deck, perché meno carte restano
                    più è preferibile suggerire i ranks.
       - HINT COLOR: qui vediamo quante carte di quel colore sono effettivamente nella mano di G2, ma anche qui non
                     ci limitiamo a questo; possiamo considerare le probabilità di HCIC e calcolare con qualche formula
                     l'utilità o il guadagno dato dal suggerire quel colore a quel giocatore, considerate le probabilità
                     che lui crede di avere sulla base delle osservazioni del gioco (HCIC G2). Il guadagno è
                     inversamente proporzionale alle probabilità, ossia più ha probabilità basse per un certo colore
                     che però è realmente nella sua mano, maggiore sarà il guadagno probabilisticamente parlando
                     di dare quell'indizio, in quanto non sapeva di avere quel colore nella sua mano. Diminuire lo score
                     in modo inversamente proporzionale a quante carte sono rimaste nel deck, perché meno carte restano
                     più è preferibile suggerire i ranks che i colori; di ranks ne abbiamo 5, di colori solo 2, e inoltre
                     la metà delle carte sono di quel colore per cui scartare un rosso o giallo è meno problematico di
                     scartare un certo rank.
    - PLAY: qui consideriamo le probabilità di HCIC, vogliamo calcolare il guadagno probabilistico
            del giocare una certa carta, che dovrà essere direttamente proporzionale alla probabilità di quella carta,
            ossia il guadagno è più alto se quella carta ha una probabilità di occorrenza abbastanza alta e se è
            chiaramente realmente giocabile con i fireworks correnti. Inoltre, potremmo considerare
            nella nostra formula anche quanti hints sono stati dati, poiché essendo questo un gioco cooperativo dovremmo
            dare priorità al dare info ai giocatori se ad esempio ci sono molti segnalini hint disponibili ancora,
            abbassando così l'utility di PLAY. Inoltre, aumentare lo score in modo inversamente proporzionale a quante
            carte restano nel deck, questo perché quando restano poche carte da pescare conviene giocare le proprie,
            laddove possibile.
    - DISCARD: come per PLAY, qui usiamo le probabilità di HCIC per vedere se siamo abbastanza certi che la carta
            che stiamo scartando sia realmente ciò che pensiamo che sia. Tuttavia qui dobbiamo capire se la carta
            sia a tutti gli effetti inutile da tenere nella nostra mano. Siccome questa azione ci restituisce un
            segnalino hint se disponibile, allora come per play anche qui se ci sono molti segnalini hints dovremmo
            dare priorità prima al scambiare qualche informazione con l'altro giocatore. Aumentare lo score quando
            ci sono molte carte nel deck, poiché conviene scartare solamente quando ci sono molte potenziali carte
            utili nel deck.
            NOTA: qui si considera l'utlità di una carta al presente ma anche al futuro. Mentre per play basta
            vedere se la carta da giocare è giocabile ORA, per Discard devo valutare il futuro.
            Ad es. se c'è R2 su red stack, e voglio scartare R4, allora non va bene scartarla, mi servirà.
            Inoltre, siccome c'è un solo Rank 5 per ogni colore, scartare una carta che ha una certa probabilità
            di essere di rank 5, deve essere penalizzato. Più è alta la probabilità, minore deve essere l'utility di Discard.
*/

% Azioni disponibili: prenderò una singola decisione ad ogni iterazione, in base allo stato del gioco.

% TODO: Vedi se puoi rimuovere ID da queste azioni
suggest_color_action_prob(Player, OtherPlayer, Color, ID) :-
    % Parte di validazione
    not(is_game_over),
    Player \= OtherPlayer,
    hints_available(HintCount),
    HintCount > 0,
    % Fine validazione, inizio conteggio utility
    hint_color_probability(Player, OtherPlayer, Color).

suggest_rank_action_prob(Player, OtherPlayer, Rank, ID) :-
    not(is_game_over),
    Player \= OtherPlayer,
    hints_available(HintCount),
    HintCount > 0,
    hint_rank_probability(Player, OtherPlayer, Rank).

play_card_action_prob(Player, Index, ID) :-
    not(is_game_over),
    Index > 0, Index < 6,
    at(Player, Index, Card),
    Card \= -,
    play_card_probability(Player, Index, ID).

discard_card_action_prob(Player, Index, ID) :-
    not(is_game_over),
    Index > 0, Index < 6,
    at(Player, Index, Card),
    Card \= -,
    discard_card_probability(Player, Index, ID).


% #########################################################
get_number_of_hinted_color_cards_playable(OtherPlayer, Color, Count) :-
    findall(PlayableIndex, (card_is_playable_now(OtherPlayer, PlayableIndex, _), at(OtherPlayer, PlayableIndex, Card), color(Card, CardColor), CardColor = Color), PlayableIndices),
    length(PlayableIndices, Count).

get_number_of_hinted_rank_cards_playable(OtherPlayer, Rank, Count) :-
    findall(PlayableIndex, (card_is_playable_now(OtherPlayer, PlayableIndex, _), at(OtherPlayer, PlayableIndex, Card), rank(Card, CardRank), CardRank = Rank), PlayableIndices),
    length(PlayableIndices, Count).
% #########################################################
