package workbench.nio.l04;

import io.netty.channel.ChannelHandler;
import io.netty.handler.codec.LengthFieldBasedFrameDecoder;

public final class LetterCodec {
    public static final int MAX_FRAME = 1024;

    private LetterCodec() { }

    public static ChannelHandler[] handlers(ChannelHandler business) {
        return new ChannelHandler[] {
                // maxFrameLength, lengthFieldOffset, lengthFieldLength, lengthAdjustment, initialBytesToStrip
                new LengthFieldBasedFrameDecoder(MAX_FRAME, 0, 4, 0, 4),
                new LetterFrameDecoder(),   // a ByteToMessageDecoder keeps state: one instance per channel
                new LetterFrameEncoder(),
                business,
        };
    }
}
