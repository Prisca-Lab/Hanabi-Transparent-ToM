/*
 * Webworker:
 * composite a bunch of bubbles into a bitmap
 * for a bokeh effect.
 */

self.addEventListener('message', doBubbleBlend);

function doBubbleBlend(e) {
    "use strict";
    var i = 0, j = 0, k = 0, x = 0, y = 0, xpos = 0, ypos = 0, stride = 0, strideBubble = 0, alpha = 0.0, alphaScaled = 0.0, a = 0, b = 0;
    var data = e.data;

    var numBubbles = data.numBubbles;
    var bubbleList = data.bubbleList;
    var targetBuffer = data.targetBuffer;
    var sourceBuffer = data.sourceBuffer;

    for (k = 0; k < numBubbles; k++) {
        // select a random bubble
        var bubble = bubbleList[Math.floor(Math.random()*bubbleList.length)];

        // put ourselves in the upper left corder of the random bubble for painting
        x = Math.round(Math.random()*targetBuffer.width - bubble.width/2);
        y = Math.round(Math.random()*targetBuffer.height - bubble.height/2);

        // duplicate the bubble
        // don't use the border pixel 'cause it causes problems on some browsers...
        for (j = 0; j < bubble.height - 1; j++) {
            for (i = 0; i < bubble.width - 1; i++) {
                xpos = x + i;
                ypos = y + j;
                if (xpos < 0 || ypos < 0) {
                    continue;
                }

                stride = ypos*targetBuffer.width*4 + xpos*4;
                strideBubble = j*bubble.width*4 + i*4;

                alpha = bubble.data[strideBubble + 3]/255;
                // if there is nothing to blend, do nothing
                if (alpha === 0) {
                    continue;
                }
                alphaScaled = -alpha*(alpha-2);

                // do screen blend the bubbles onto the target buffer
                a = targetBuffer.data[stride + 0]/255;
                b = alphaScaled*bubble.data[strideBubble + 0]/255;
                targetBuffer.data[stride + 0] = 255*(1-(1-a)*(1-b));
                a = targetBuffer.data[stride + 1]/255;
                b = alphaScaled*bubble.data[strideBubble + 1]/255;
                targetBuffer.data[stride + 1] = 255*(1-(1-a)*(1-b));
                a = targetBuffer.data[stride + 2]/255;
                b = alphaScaled*bubble.data[strideBubble + 2]/255;
                targetBuffer.data[stride + 2] = 255*(1-(1-a)*(1-b));
                // copy the alpha channel directly
                a = targetBuffer.data[stride + 3]/255;
                b = bubble.data[strideBubble + 3]/255;
                targetBuffer.data[stride + 3] = 255*(a + b - a*b);

            }
        }
    }
    for (j = 0; j < targetBuffer.height; j++) {
        for (i = 0; i < targetBuffer.width; i++) {
            stride = j*targetBuffer.width*4 + i*4;

            alpha = targetBuffer.data[stride + 3]/255;
            // if there is nothing to blend, do nothing
            if (alpha === 0) {
                continue;
            }
            alphaScaled = -alpha*(alpha-2);

            // do screen blending with the sourceBuffer but leave the alpha channel alone
            a = targetBuffer.data[stride + 0]/255 + alphaScaled/4;
            b = sourceBuffer.data[stride + 0]/255;
            targetBuffer.data[stride + 0] = 255*(1-(1-a)*(1-b));
            a = targetBuffer.data[stride + 1]/255 + alphaScaled/4;
            b = sourceBuffer.data[stride + 1]/255;
            targetBuffer.data[stride + 1] = 255*(1-(1-a)*(1-b));
            a = targetBuffer.data[stride + 2]/255 + alphaScaled/4;
            b = sourceBuffer.data[stride + 2]/255;
            targetBuffer.data[stride + 2] = 255*(1-(1-a)*(1-b));
        }
    }

    // the computation is done, emit the target
    self.postMessage({targetBuffer: targetBuffer});
}
