package workbench.quotes.l03;

import io.netty.channel.ChannelFutureListener;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.codec.TooLongFrameException;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CompletableFuture;

/** Answers quote requests on one connection. Every method here runs on the channel's event loop. */
public final class QuoteHandler extends SimpleChannelInboundHandler<String> {
    private final QuoteSource source;
    // only the event loop touches this set, so a plain HashSet is enough: the loop is the lock
    private final Set<CompletableFuture<Quote>> inFlight = new HashSet<>();

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
        CompletableFuture<Quote> quote = source.quote(r.symbol());   // 1. returns at once
        inFlight.add(quote);
        updateReading(ctx);                                           // 2. too many waiting? stop reading
        quote.whenCompleteAsync((q, e) -> {                           // 3. finish on this channel's loop
            inFlight.remove(quote);
            if (ctx.channel().isActive()) {
                ctx.writeAndFlush(e == null ? QuoteProtocol.ok(r.id(), q) : QuoteProtocol.error(r.id(), e));
            }
            updateReading(ctx);                                       // 4. a slot is free: maybe read again
        }, ctx.executor());
    }

    @Override
    public void channelWritabilityChanged(ChannelHandlerContext ctx) {
        updateReading(ctx);                                           // the client stopped or started reading
        ctx.fireChannelWritabilityChanged();
    }

    // auto-read is the only tap we control: open it only while replies can leave and slots are free
    private void updateReading(ChannelHandlerContext ctx) {
        boolean read = ctx.channel().isWritable() && inFlight.size() < QuoteProtocol.MAX_IN_FLIGHT;
        ctx.channel().config().setAutoRead(read);
    }

    @Override
    public void channelInactive(ChannelHandlerContext ctx) {
        for (CompletableFuture<Quote> f : List.copyOf(inFlight)) {
            f.cancel(true);                                           // nobody is left to read the answer
        }
        inFlight.clear();
        ctx.fireChannelInactive();
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        if (cause instanceof TooLongFrameException) {
            ctx.writeAndFlush("ERR line too long\n").addListener(ChannelFutureListener.CLOSE);
        } else {
            ctx.close();
        }
    }
}
