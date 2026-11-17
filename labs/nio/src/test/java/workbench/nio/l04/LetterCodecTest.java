package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufAllocator;
import io.netty.buffer.ByteBufUtil;
import io.netty.buffer.Unpooled;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.embedded.EmbeddedChannel;
import io.netty.handler.codec.TooLongFrameException;
import io.netty.util.ResourceLeakDetector;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.Timeout;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@Timeout(20)
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class LetterCodecTest {
    static final List<String> leaks = new CopyOnWriteArrayList<>();

    @BeforeAll
    static void paranoid() {
        ResourceLeakDetector.setLevel(ResourceLeakDetector.Level.PARANOID);   // track every buffer, not 1 in 128
        ByteBufUtil.setLeakListener((type, records) -> leaks.add(type + "\n" + records));
    }

    @AfterAll
    static void reset() {
        ByteBufUtil.setLeakListener(null);
        ResourceLeakDetector.setLevel(ResourceLeakDetector.Level.SIMPLE);
    }

    /** Answers every letter with a receipt: type RECEIPT and the same body. */
    static final class ReceiptDesk extends SimpleChannelInboundHandler<Letter> {
        @Override
        protected void channelRead0(ChannelHandlerContext ctx, Letter m) {
            ctx.writeAndFlush(new Letter(Letter.RECEIPT, m.body()));
        }
    }

    static ByteBuf encode(Letter... messages) {
        EmbeddedChannel enc = new EmbeddedChannel(new LetterFrameEncoder());
        ByteBuf all = Unpooled.buffer();
        for (Letter m : messages) {
            enc.writeOutbound(m);
            ByteBuf b = enc.readOutbound();
            all.writeBytes(b);
            b.release();
        }
        enc.finishAndReleaseAll();
        return all;
    }

    @Test
    @Order(1)
    @DisplayName("the encoder writes [length][type][UTF-8 body], and the length counts the type byte")
    void encoderWritesFrame() {
        ByteBuf wire = encode(new Letter(Letter.NOTE, "note-1"));
        assertThat(ByteBufUtil.hexDump(wire)).isEqualTo("00000007" + "01" + "6e6f74652d31");
        wire.release();
    }

    @Test
    @Order(2)
    @DisplayName("the decoder waits for whole frames, however the bytes are split")
    void decoderReassemblesFragments() {
        ByteBuf wire = encode(new Letter(Letter.NOTE, "note-1"),
                new Letter(Letter.PARCEL, "parcel-1"));   // 11 bytes + 13 bytes
        EmbeddedChannel ch = new EmbeddedChannel(LetterCodec.handlers(new ReceiptDesk()));
        assertThat(ch.writeInbound(wire.retainedSlice(0, 3))).as("half a length field").isFalse();
        assertThat(ch.writeInbound(wire.retainedSlice(3, 6))).as("frame 1 still incomplete").isFalse();
        ch.writeInbound(wire.retainedSlice(9, 5));                         // ends frame 1, starts frame 2
        ch.writeInbound(wire.retainedSlice(14, wire.readableBytes() - 14));
        wire.release();

        EmbeddedChannel decode = new EmbeddedChannel(LetterCodec.handlers(new SimpleChannelInboundHandler<Letter>() {
            @Override protected void channelRead0(ChannelHandlerContext ctx, Letter m) {
                ctx.fireChannelRead(m);   // let the test read the decoded replies
            }
        }));
        ByteBuf reply;
        while ((reply = ch.readOutbound()) != null) decode.writeInbound(reply);
        assertThat((Letter) decode.readInbound()).isEqualTo(new Letter(Letter.RECEIPT, "note-1"));
        assertThat((Letter) decode.readInbound()).isEqualTo(new Letter(Letter.RECEIPT, "parcel-1"));
        assertThat((Object) decode.readInbound()).isNull();
        assertThat(ch.finish()).as("no bytes left over").isFalse();
        decode.finishAndReleaseAll();
    }

    @Test
    @Order(3)
    @DisplayName("a frame longer than MAX_FRAME is rejected before its body arrives")
    void oversizedFrameIsRejected() {
        EmbeddedChannel ch = new EmbeddedChannel(LetterCodec.handlers(new ReceiptDesk()));
        ByteBuf hostile = Unpooled.buffer().writeInt(5_000).writeByte(Letter.NOTE);
        assertThatThrownBy(() -> ch.writeInbound(hostile))
                .isInstanceOf(TooLongFrameException.class)
                .hasMessage("Adjusted frame length exceeds 1024: 5004 - discarded");
        ch.finishAndReleaseAll();
    }

    @Test
    @Order(4)
    @DisplayName("CountingTap counts the bytes and passes the same buffer on, so it can be released")
    void auditTapPassesOwnershipOn() {
        CountingTap tap = new CountingTap();
        EmbeddedChannel ch = new EmbeddedChannel(tap);
        ByteBuf in = ByteBufAllocator.DEFAULT.buffer(16).writeInt(42).writeLong(7);
        ch.writeInbound(in);
        ByteBuf passedOn = ch.readInbound();
        assertThat(tap.bytesSeen()).isEqualTo(12);
        passedOn.release();                                   // the next handler (here: the test) releases it
        assertThat(in.refCnt()).as("refCnt of the buffer that arrived").isZero();
        ch.finishAndReleaseAll();
    }

    @Test
    @Order(5)
    @DisplayName("PARANOID leak detection finds no leaked buffer in the whole pipeline")
    void noLeaksUnderParanoid() throws Exception {
        for (int i = 0; i < 10; i++) {
            EmbeddedChannel ch = new EmbeddedChannel();
            ch.pipeline().addLast(new CountingTap());
            ch.pipeline().addLast(LetterCodec.handlers(new ReceiptDesk()));
            ByteBuf frame = ByteBufAllocator.DEFAULT.buffer();
            frame.writeBytes(encode(new Letter(Letter.NOTE, "note-" + i)));   // test-owned copy
            ch.writeInbound(frame);
            ch.finishAndReleaseAll();
        }
        // leaks are found when a buffer is garbage-collected without release(), and reported on a later allocation
        for (int i = 0; i < 40 && leaks.isEmpty(); i++) {
            System.gc();
            Thread.sleep(20);
            ByteBufAllocator.DEFAULT.buffer(8).release();
        }
        assertThat(leaks).as("LEAK reports").isEmpty();
    }
}
