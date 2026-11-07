package workbench.memory.l06;

import workbench.memory.Jvm;

import java.lang.management.BufferPoolMXBean;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.nio.ByteBuffer;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.CountDownLatch;

/**
 * A child JVM with -Xmx256m that does what services do: a 64 MiB direct buffer (think Netty) and 50
 * threads. It then compares what the JVM reports with what the operating system says it uses.
 */
public class FootprintDemo {
    static final long MB = 1024 * 1024;

    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            // AlwaysPreTouch touches every heap page at startup, like a service that has run for a while
            Jvm.run(List.of("-Xmx256m", "-Xms256m", "-XX:+AlwaysPreTouch"), FootprintDemo.class.getName(), "child");
            return;
        }
        ByteBuffer direct = ByteBuffer.allocateDirect((int) (64 * MB));
        CountDownLatch never = new CountDownLatch(1);
        for (int i = 0; i < 50; i++) {
            Thread t = new Thread(() -> { try { never.await(); } catch (InterruptedException e) { } });
            t.setDaemon(true);
            t.start();
        }
        MemoryMXBean memory = ManagementFactory.getMemoryMXBean();
        long directBytes = ManagementFactory.getPlatformMXBeans(BufferPoolMXBean.class).stream()
                .filter(p -> p.getName().equals("direct")).mapToLong(BufferPoolMXBean::getMemoryUsed).sum();
        System.out.printf("heap committed      %,5d MB  (-Xmx256m)%n", memory.getHeapMemoryUsage().getCommitted() / MB);
        System.out.printf("non-heap committed  %,5d MB  (metaspace, class space, code cache)%n", memory.getNonHeapMemoryUsage().getCommitted() / MB);
        System.out.printf("direct buffers      %,5d MB%n", directBytes / MB);
        System.out.printf("live threads        %,5d     (each with its own stack)%n", ManagementFactory.getThreadMXBean().getThreadCount());
        Path status = Path.of("/proc/self/status");
        if (Files.exists(status)) {                                  // Linux only
            Files.readAllLines(status).stream().filter(l -> l.startsWith("VmRSS")).forEach(l ->
                    System.out.printf("resident in RAM     %,5d MB  (what the container limit counts)%n", Long.parseLong(l.replaceAll("\\D+", "")) / 1024));
        } else {
            System.out.println("resident in RAM     not available here (/proc is Linux only)");
        }
        System.out.println("buffer " + direct.capacity());
    }
}
