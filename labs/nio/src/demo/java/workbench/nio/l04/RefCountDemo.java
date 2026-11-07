package workbench.nio.l04;

import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufAllocator;
import io.netty.buffer.CompositeByteBuf;
import io.netty.buffer.Unpooled;
import io.netty.util.IllegalReferenceCountException;

import static java.nio.charset.StandardCharsets.US_ASCII;

/** A ByteBuf's two indexes and its reference count, step by step. */
public class RefCountDemo {
    public static void main(String[] args) {
        System.out.println("default allocator: " + ByteBufAllocator.DEFAULT.getClass().getSimpleName());
        ByteBuf b = ByteBufAllocator.DEFAULT.buffer(16);
        System.out.println("buffer(16): " + b.getClass().getSimpleName() + " direct=" + b.isDirect()
                + " readerIndex=" + b.readerIndex() + " writerIndex=" + b.writerIndex() + " refCnt=" + b.refCnt());
        b.writeInt(42).writeLong(7);
        System.out.println("after writeInt+writeLong: writerIndex=" + b.writerIndex() + " readableBytes=" + b.readableBytes());
        b.readInt();
        System.out.println("after readInt: readerIndex=" + b.readerIndex() + " readableBytes=" + b.readableBytes() + " (no flip)");
        b.retain();
        System.out.println("retain(): refCnt=" + b.refCnt());
        System.out.println("release() -> " + b.release() + ", refCnt=" + b.refCnt());
        System.out.println("release() -> " + b.release() + ", refCnt=" + b.refCnt() + " (memory goes back to the allocator)");
        try {
            b.readLong();
        } catch (IllegalReferenceCountException e) {
            System.out.println("readLong() after release -> " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }

        ByteBuf header = Unpooled.copiedBuffer("HDR:", US_ASCII);
        ByteBuf body = Unpooled.copiedBuffer("payload", US_ASCII);
        CompositeByteBuf frame = Unpooled.compositeBuffer();
        frame.addComponents(true, header, body);                 // no bytes copied; frame now owns both parts
        body.setByte(0, 'P');
        System.out.println("composite: " + frame.toString(US_ASCII) + " (sees the change to body: shared memory)");
        frame.release();
        System.out.println("composite.release(): header.refCnt=" + header.refCnt() + " body.refCnt=" + body.refCnt());
    }
}
