package workbench.memory.l01;

import java.lang.management.BufferPoolMXBean;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryPoolMXBean;
import java.nio.ByteBuffer;

/** Lists the memory areas this JVM reports, heap and non-heap, then adds a 64 MiB direct buffer. */
public class MemoryAreasDemo {
    static final long MB = 1024 * 1024;

    public static void main(String[] args) {
        System.out.printf("max heap (-Xmx or its default): %,d MB%n", Runtime.getRuntime().maxMemory() / MB);
        for (MemoryPoolMXBean pool : ManagementFactory.getMemoryPoolMXBeans()) {
            System.out.printf("%-9s %-32s used %,6d KB  committed %,7d KB%n",
                    pool.getType() == java.lang.management.MemoryType.HEAP ? "heap" : "non-heap",
                    pool.getName(), pool.getUsage().getUsed() / 1024, pool.getUsage().getCommitted() / 1024);
        }
        System.out.println("live threads: " + ManagementFactory.getThreadMXBean().getThreadCount() + ", each with a stack outside the heap");

        ByteBuffer direct = ByteBuffer.allocateDirect((int) (64 * MB));      // off-heap: not in any pool above
        for (BufferPoolMXBean p : ManagementFactory.getPlatformMXBeans(BufferPoolMXBean.class)) {
            if (p.getName().equals("direct")) {
                System.out.printf("direct buffers: %d, %,d MB, outside the heap%n", p.getCount(), p.getMemoryUsed() / MB);
            }
        }
        System.out.println("buffer capacity " + direct.capacity());
    }
}
