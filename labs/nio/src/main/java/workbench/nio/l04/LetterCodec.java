package workbench.nio.l04;

import io.netty.channel.ChannelHandler;

/** The pipeline of the letter link. */
public final class LetterCodec {
    /** The largest frame we accept, counting the length field: 4 + 1 + body. */
    public static final int MAX_FRAME = 1024;

    private LetterCodec() { }

    /**
     * The handlers in pipeline order:
     * <ol>
     *   <li>{@code new LengthFieldBasedFrameDecoder(MAX_FRAME, 0, 4, 0, 4)}: whole frames, length stripped</li>
     *   <li>{@link LetterFrameDecoder}</li>
     *   <li>{@link LetterFrameEncoder}</li>
     *   <li>{@code business}</li>
     * </ol>
     */
    public static ChannelHandler[] handlers(ChannelHandler business) {
        throw new UnsupportedOperationException("TODO: return the four handlers in order");
    }
}
