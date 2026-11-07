package workbench.quotes.l01;

import io.netty.channel.ChannelHandler;
import io.netty.handler.codec.LineBasedFrameDecoder;
import io.netty.handler.codec.string.StringDecoder;
import io.netty.handler.codec.string.StringEncoder;
import io.netty.handler.flow.FlowControlHandler;

import static java.nio.charset.StandardCharsets.UTF_8;

/** The handlers of one connection, in pipeline order. */
public final class QuotePipeline {
    private QuotePipeline() {}

    public static ChannelHandler[] handlers(QuoteSource source) {
        return new ChannelHandler[] {
            new LineBasedFrameDecoder(QuoteProtocol.MAX_LINE),   // bytes in, one line out; a longer line fails
            new StringDecoder(UTF_8),                            // line bytes to String
            new StringEncoder(UTF_8),                            // outbound String to bytes
            new FlowControlHandler(),                            // with auto-read off, hold the lines already decoded
            new QuoteHandler(source),                            // a new handler per connection: it has state
        };
    }
}
