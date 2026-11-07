package workbench.nio.l04;

import io.netty.channel.ChannelHandler;

/** The pipeline of the payment link. */
public final class PaymentCodec {
    /** The largest frame we accept, counting the length field: 4 + 1 + body. */
    public static final int MAX_FRAME = 1024;

    private PaymentCodec() { }

    /**
     * The handlers in pipeline order:
     * <ol>
     *   <li>{@code new LengthFieldBasedFrameDecoder(MAX_FRAME, 0, 4, 0, 4)}: whole frames, length stripped</li>
     *   <li>{@link PaymentFrameDecoder}</li>
     *   <li>{@link PaymentFrameEncoder}</li>
     *   <li>{@code business}</li>
     * </ol>
     */
    public static ChannelHandler[] handlers(ChannelHandler business) {
        throw new UnsupportedOperationException("TODO: return the four handlers in order");
    }
}
