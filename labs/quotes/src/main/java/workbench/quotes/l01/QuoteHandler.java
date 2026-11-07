package workbench.quotes.l01;

import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;

import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletionException;

/**
 * Answers quote requests on one connection. Every method here runs on the channel's event loop.
 *
 * <p>This is a first draft. It answers correctly, one request at a time, and it is broken in four ways:
 * <ol>
 *   <li>{@code channelRead0} waits for the quote with {@code join()}, on the event loop. Every other
 *       channel on that loop stops until the provider answers. Make it return at once: keep the future
 *       in a set of in-flight requests, and write the reply in {@code whenCompleteAsync(..., ctx.executor())},
 *       so the callback runs back on this channel's loop.</li>
 *   <li>Nothing limits what one client can make us hold. Read only while the channel is writable AND
 *       fewer than {@link QuoteProtocol#MAX_IN_FLIGHT} requests are in flight: set auto-read from that
 *       rule after each new request, after each reply, and in {@code channelWritabilityChanged}.</li>
 *   <li>When the client hangs up, its pending quotes keep running. Cancel them in {@code channelInactive}.</li>
 *   <li>A line longer than {@link QuoteProtocol#MAX_LINE} arrives here as a {@code TooLongFrameException}.
 *       Reply {@code "ERR line too long\n"}, then close the connection once that write is done (QUIT shows how).</li>
 * </ol>
 */
public final class QuoteHandler extends SimpleChannelInboundHandler<String> {
    private final QuoteSource source;

    public QuoteHandler(QuoteSource source) {
        this.source = source;
    }

    @Override
    protected void channelRead0(ChannelHandlerContext ctx, String line) {
        if (line.equals("QUIT")) {
            ctx.writeAndFlush("BYE\n").addListener(ChannelFutureListener.CLOSE);   // close once BYE is out
            return;
        }
        QuoteProtocol.Request r = QuoteProtocol.parse(line);
        if (r == null) {
            ctx.writeAndFlush("ERR bad request\n");
            return;
        }
        try {
            Quote q = source.quote(r.symbol()).join();               // BUG: blocks the event loop
            ctx.writeAndFlush(QuoteProtocol.ok(r.id(), q));
        } catch (CompletionException | CancellationException e) {
            ctx.writeAndFlush(QuoteProtocol.error(r.id(), e));
        }
    }

    @Override
    public void channelWritabilityChanged(ChannelHandlerContext ctx) {
        // TODO: backpressure (point 2)
        ctx.fireChannelWritabilityChanged();
    }

    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        // TODO: cancel what is still in flight (point 3)
        ctx.fireChannelInactive();
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        ctx.close();                                                  // TODO: answer a too-long line first (point 4)
    }
}
