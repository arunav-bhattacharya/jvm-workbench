package workbench.quotes.l01;

import io.netty.channel.ChannelHandler;

/** The handlers of one connection, in pipeline order. */
public final class QuotePipeline {
    private QuotePipeline() {}

    /**
     * Return a new set of handlers for one connection, in this order:
     * <ol>
     *   <li>{@code LineBasedFrameDecoder(QuoteProtocol.MAX_LINE)}: bytes in, one line out</li>
     *   <li>{@code StringDecoder(UTF_8)}</li>
     *   <li>{@code StringEncoder(UTF_8)}</li>
     *   <li>{@code FlowControlHandler()}: while auto-read is off, it holds lines that were already decoded</li>
     *   <li>{@code new QuoteHandler(source)}</li>
     * </ol>
     */
    public static ChannelHandler[] handlers(QuoteSource source) {
        throw new UnsupportedOperationException("TODO: return the five handlers in order");
    }
}
