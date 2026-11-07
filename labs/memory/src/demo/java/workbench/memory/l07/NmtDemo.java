package workbench.memory.l07;

import workbench.memory.Jvm;

import javax.management.ObjectName;
import java.lang.management.ManagementFactory;
import java.nio.ByteBuffer;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Native Memory Tracking from inside a child JVM: the summary before and after a 64 MiB direct buffer
 * and 100 extra threads. Then a direct buffer that doesn't fit under -XX:MaxDirectMemorySize.
 */
public class NmtDemo {
    static final Pattern CATEGORY = Pattern.compile("^-?\\s*(Total|[A-Z][\\w ]+?):? \\(?reserved=(\\d+)MB, committed=(\\d+)MB");

    static String nativeMemory() throws Exception {                      // the same as: jcmd <pid> VM.native_memory summary scale=MB
        return (String) ManagementFactory.getPlatformMBeanServer().invoke(
                new ObjectName("com.sun.management:type=DiagnosticCommand"), "vmNativeMemory",
                new Object[] {new String[] {"summary", "scale=MB"}}, new String[] {String[].class.getName()});
    }

    static void print(String title) throws Exception {
        System.out.println(title);
        for (String line : nativeMemory().lines().toList()) {
            Matcher m = CATEGORY.matcher(line);
            if (m.find()) System.out.printf("  %-20s committed %,5d MB  (reserved %,5d MB)%n", m.group(1), Long.parseLong(m.group(3)), Long.parseLong(m.group(2)));
        }
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 0) {
            Jvm.run(List.of("-Xmx256m", "-XX:NativeMemoryTracking=summary"), NmtDemo.class.getName(), "track");
            Jvm.run(List.of("-Xmx256m", "-XX:MaxDirectMemorySize=32m"), NmtDemo.class.getName(), "limit");
            return;
        }
        if (args[0].equals("limit")) {
            try {
                ByteBuffer.allocateDirect(64 * 1024 * 1024);
            } catch (OutOfMemoryError e) {
                System.out.println("with -XX:MaxDirectMemorySize=32m: " + e);
            }
            return;
        }
        print("at startup");
        ByteBuffer direct = ByteBuffer.allocateDirect(64 * 1024 * 1024);   // what Netty does for socket buffers
        CountDownLatch never = new CountDownLatch(1);
        for (int i = 0; i < 100; i++) {
            Thread t = new Thread(() -> { try { never.await(); } catch (InterruptedException e) { } });
            t.setDaemon(true);
            t.start();
        }
        print("after a 64 MiB direct buffer and 100 more threads");
        System.out.println("buffer " + direct.capacity());
    }
}
