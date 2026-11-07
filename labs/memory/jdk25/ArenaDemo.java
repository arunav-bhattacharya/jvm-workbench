// JDK 22 or later: the Foreign Function and Memory API is final since JDK 22 (JEP 454). Written for JDK 25.
// Not part of the Gradle build, because the labs compile for JDK 21, where this API is a preview. From labs/:
//     java memory/jdk25/ArenaDemo.java
//     java -XX:MaxDirectMemorySize=16m memory/jdk25/ArenaDemo.java

import java.lang.foreign.Arena;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.ValueLayout;
import java.lang.management.BufferPoolMXBean;
import java.lang.management.ManagementFactory;

public class ArenaDemo {
    public static void main(String[] args) {
        MemorySegment escaped;
        try (Arena arena = Arena.ofConfined()) {                          // 1. one owner thread, closed by try-with-resources
            MemorySegment ledger = arena.allocate(32L * 1024 * 1024);      // 2. 32 MiB outside the heap
            for (long i = 0; i < ledger.byteSize() / Long.BYTES; i++) {
                ledger.setAtIndex(ValueLayout.JAVA_LONG, i, i * 100);      //    4 million longs, and no objects
            }
            System.out.println("entry 1,000 holds " + ledger.getAtIndex(ValueLayout.JAVA_LONG, 1_000));
            System.out.println("inside the arena: " + direct());
            escaped = ledger;
        }                                                                 // 3. freed here, not by the GC
        System.out.println("after close():    " + direct());
        try {
            escaped.getAtIndex(ValueLayout.JAVA_LONG, 0);                 // 4. use after free is an exception, not a crash
        } catch (IllegalStateException e) {
            System.out.println("reading after close() throws: " + e.getMessage());
        }
    }

    // native segments count against the same limit as direct ByteBuffers
    static String direct() {
        return ManagementFactory.getPlatformMXBeans(BufferPoolMXBean.class).stream()
                .filter(p -> p.getName().equals("direct"))
                .map(p -> p.getCount() + " direct allocation(s), " + (p.getMemoryUsed() >> 20) + " MiB")
                .findFirst().orElse("?");
    }
}
