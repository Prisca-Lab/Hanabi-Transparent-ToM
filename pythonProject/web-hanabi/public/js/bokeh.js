/*********************************
 * class to create a bokeh effect
 * parallax-scrolling background
 *
 * to use do:
 *      bokeh = new Bokeh;
 *      // this operation could take a while
 *      bokeh.initialize();
 *********************************/
var Bokeh = (function () {
    "use strict";
    // some helper functions

    // add stops to a gradient that look like a rainbow
    function addRainbowStops(grad) {
        grad.addColorStop(1.00, 'rgb(000,169,078)');
        grad.addColorStop(0.80, 'rgb(255,232,000)');
        grad.addColorStop(0.60, 'rgb(255,050,047)');
        grad.addColorStop(0.40, 'rgb(255,000,127)');
        grad.addColorStop(0.20, 'rgb(127,000,145)');
        grad.addColorStop(0.00, 'rgb(000,167,225)');
        return grad;
    }

    // add stops to a gradient to impersinate a blurry bubble
    function addBubbleStops (grad, perimiterPercentage, blurFactor) {
        var fill = 'rgba(40,40,40,.4)';
        var stroke = 'rgba(80,80,80,.7)';
        var pp = perimiterPercentage, bf = blurFactor;

        grad.addColorStop(0, fill);
        grad.addColorStop(1-2*(1-pp), fill);
        grad.addColorStop(pp - (1-pp)*bf, stroke);
        grad.addColorStop(pp + (1-pp)*bf, stroke);
        grad.addColorStop(1, 'rgba(100,100,100,0)');

        return grad;
    }

    // the init function
    function Bokeh() {
        var boundingRect = document.body.getBoundingClientRect()
        this.width = boundingRect.width;
        this.height = boundingRect.height;

        this.container = document.createElement('div');
        this.container.id = 'bokeh-container';

        this.scratchCanvases = [];
        this.scratchCanvases.push(document.createElement('canvas'));
        this.scratchCanvases.push(document.createElement('canvas'));
        this.scratchCanvases.push(document.createElement('canvas'));

        this.layers = [];
        this.layers.push(document.createElement('canvas'));
        this.layers.push(document.createElement('canvas'));
        this.layers.push(document.createElement('canvas'));
    }
    // render the bokeh object when youre happy with it and
    // attach it to the window
    Bokeh.prototype.initialize = function () {
        this.resizeCanvases();
        this.drawBubbles();
        this.drawBackground();
        this.setupContainer();
        this.initializeListeners();
        // create the CSS
        var styleElm = document.createElement('style');
        styleElm.type = 'text/css';
        styleElm.innerHTML = '#bokeh-container { position: absolute; left: 0px; top: 0px; overflow: hidden; width: 100%; height: 100%; z-index: -1; }';
        document.head.appendChild(styleElm);
        document.body.appendChild(this.container);
    };
    Bokeh.prototype.initializeListeners = function () {
        var _this = this;
        function mouseMove(e) {
            var x, y, margin;
            x = e.clientX;
            y = e.clientY;

            // translate the two paralax layers
            margin = .25*_this.width;
            _this.layers[1].style.transform = 'translate('+ (x/8 - margin) +'px, '+ (y/20 - margin/2) +'px)';
            _this.layers[2].style.transform = 'translate('+ (x/4 - margin) +'px, '+ (y/10 - margin/2) +'px)';
        }
        window.addEventListener('mousemove', mouseMove);
        window.addEventListener('touchmove', mouseMove);
    };
    Bokeh.prototype.setupContainer = function () {
        var i;
        for (i = 0; i < this.layers.length; i++) {
            this.container.appendChild(this.layers[i]);
            this.layers[i].style.position = 'absolute';
            this.layers[i].style.left = 0;
            this.layers[i].style.right = 0;
        }
    };

    // resize all the canvases so they are ready for drawing
    Bokeh.prototype.resizeCanvases = function () {
        var i;
        var width = this.width, height = this.height;
        // the canvases that move around need to be bigger than the actual size of the screen
        var bigWidth = width*1.25, bighHeight = height*1.25;

        this.layers[0].width = width;
        this.layers[0].height = height;
        for (i = 1; i < this.layers.length; i++) {
            this.layers[i].width = bigWidth;
            this.layers[i].height = bighHeight;
        }
        for (i = 0; i < this.scratchCanvases.length; i++) {
            this.scratchCanvases[i].width = bigWidth;
            this.scratchCanvases[i].height = bighHeight;
        }
    };

    Bokeh.prototype.drawBubbles = function () {
        // to draw the bubbles that will be moving around, we first
        // need to draw a gradient and some bubbles, apply the screen
        // mask to lighten up the bubbles, then copy the bubbles using
        // destination-in into our final canvas.

        var _this = this;
        var NUM_BUBBLES = 28, r = 20, thickness = 10, blurFactor = .5, targetBuffer, sourceBuffer, worker;
        var grad;
        var width = this.scratchCanvases[0].width;
        var height = this.scratchCanvases[0].height;
        var canv0 = this.scratchCanvases[0];
        var canv1 = this.scratchCanvases[1];
        var ctx0 = canv0.getContext('2d');
        var ctx1 = canv1.getContext('2d');

        // draw the rainbow backing
        function drawBack () {
            grad = ctx0.createLinearGradient(0, 0, width, 0);
            grad = addRainbowStops(grad);
            ctx0.clearRect(0, 0, width, height);
            ctx0.globalCompositeOperation = 'source-over';
            ctx0.fillStyle = grad;
            ctx0.fillRect(0, 0, width, height);
        }

        // draw random bubbles
        function drawBubble () {
            var i, rad;

            rad = r*(1-Math.random()/3);

            ctx1.clearRect(0, 0, 2*rad, 2*rad);
            ctx1.globalCompositeOperation = 'source-over';

            // draw the actual bubble
            grad = ctx1.createRadialGradient(rad, rad, 0, rad, rad, rad);
            grad = addBubbleStops(grad, 1-thickness/rad, blurFactor);
            ctx1.fillStyle = grad;
            ctx1.fillRect(0, 0, 2*rad, 2*rad);

            return ctx1.getImageData(0, 0, 2*rad, 2*rad);
        }

        function drawBubblesInWorkerThread(target) {
            var bubbleList = [null, null, null].map(drawBubble);

            // set up a web worker to render the bubbles in another thread
            worker = new Worker('/js/bokeh-webworker.js');
            worker.addEventListener('message', function(e) {
                var data = e.data;
                target.getContext('2d').putImageData(data.targetBuffer, 0, 0);
            });
            worker.postMessage({
                numBubbles: NUM_BUBBLES,
                bubbleList: bubbleList,
                targetBuffer: targetBuffer,
                sourceBuffer: sourceBuffer,
            });
        }

        drawBack();
        ctx1.clearRect(0, 0, width, height);
        targetBuffer = ctx1.getImageData(0, 0, width, height);
        sourceBuffer = ctx0.getImageData(0, 0, width, height);


        // draw the background bubbles
        r = 35;
        thickness = 10;
        blurFactor = .6;
        drawBubblesInWorkerThread(this.layers[1]);

        // draw the foreground bubbles
        r = 60;
        thickness = 20;
        blurFactor = .2;
        drawBubblesInWorkerThread(this.layers[2]);
    };

    Bokeh.prototype.makeFilmGrainPattern = function () {
        var width = 50, height = 100, i = 0, j = 0, stride = 0;
        var canv = this.scratchCanvases[2];
        canv.width = width;
        canv.height = height;
        var ctx = canv.getContext('2d');
        var imageData = ctx.getImageData(0, 0, width, height);

        // render the noise
        for (j = 0; j < imageData.height; j++) {
            for (i = 0; i < imageData.width; i++) {
                stride = j*imageData.width*4 + i*4;

                imageData.data[stride + 0] = 255*(Math.random()/5);
                imageData.data[stride + 1] = 255*(Math.random()/5);
                imageData.data[stride + 2] = 255*(Math.random()/5);
                imageData.data[stride + 3] = 200;
            }
        }

        canv.getContext('2d').putImageData(imageData, 0, 0);
        console.log(canv, imageData.data, ctx.getImageData(0,0,1,1).data)
        return canv;
    };

    Bokeh.prototype.drawBackground = function () {
        var grad, i, j;
        var canv = this.layers[0];
        var width = canv.width;
        var height = canv.height;
        var ctx = canv.getContext('2d');

        // draw a rainbow background
        grad = ctx.createLinearGradient(0, 0, width, 0);
        grad = addRainbowStops(grad);
        ctx.globalCompositeOperation = 'source-over';
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, width, height);

        // add film grain
        var grainPattern = ctx.createPattern(this.makeFilmGrainPattern(), 'repeat');
        ctx.fillStyle = grainPattern;
        ctx.globalCompositeOperation = 'screen';
        // if we're not on a device that support screen blend mode, do nothing
        if (ctx.globalCompositeOperation == 'screen') {
            ctx.fillRect(0, 0, width, height);
        }

        // add the vingette
        var maxDim = Math.max(width, height);
        grad = ctx.createRadialGradient(width/2, height/2, 0, width/2, height/2, maxDim/1.3);
        grad.addColorStop(0, 'rgba(0,0,0,0)');
        grad.addColorStop(.5, 'rgba(0,0,0,.2)');
        grad.addColorStop(1, 'rgba(0,0,0,1)');
        ctx.fillStyle = grad;
        ctx.globalCompositeOperation = 'source-over';
        ctx.fillRect(0, 0, width, height);
    };

    return Bokeh;
})();
