package workbench.nio.l02;

import java.nio.ByteBuffer;

import static java.nio.charset.StandardCharsets.US_ASCII;

/** Walks a ByteBuffer through put, flip, get, compact and clear, printing its cursor after each step. */
public class BufferDemo {
    static void show(String step, ByteBuffer b) {
        System.out.printf("%-20s pos=%-2d lim=%-2d cap=%-2d remaining=%d%n",
                step, b.position(), b.limit(), b.capacity(), b.remaining());
    }

    public static void main(String[] args) {
        ByteBuffer b = ByteBuffer.allocate(16);
        show("allocate(16)", b);
        b.put("hello".getBytes(US_ASCII));
        show("put(\"hello\")", b);
        b.flip();                                   // write mode -> read mode: limit = position, position = 0
        show("flip()", b);
        byte[] two = new byte[2];
        b.get(two);
        show("get(2) -> \"" + new String(two, US_ASCII) + "\"", b);
        b.compact();                                // move the unread "llo" to the front, back to write mode
        show("compact()", b);
        b.put("XY".getBytes(US_ASCII));
        show("put(\"XY\")", b);
        b.flip();
        show("flip()", b);
        byte[] rest = new byte[b.remaining()];
        b.get(rest);
        System.out.println("readable content: \"" + new String(rest, US_ASCII) + "\"");

        ByteBuffer forgot = ByteBuffer.allocate(8);
        forgot.put((byte) 1).put((byte) 2);         // no flip() before handing it to write()
        System.out.println("forgot flip(): remaining()=" + forgot.remaining()
                + ", so a write would send 6 stale bytes, not the 2 you put");

        ByteBuffer heap = ByteBuffer.allocate(64), direct = ByteBuffer.allocateDirect(64);
        System.out.println("heap:   isDirect=" + heap.isDirect() + " hasArray=" + heap.hasArray() + " " + heap.getClass().getName());
        System.out.println("direct: isDirect=" + direct.isDirect() + " hasArray=" + direct.hasArray() + " " + direct.getClass().getName());
    }
}
