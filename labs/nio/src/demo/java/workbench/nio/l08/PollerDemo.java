package workbench.nio.l08;

import java.io.IOException;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Collectors;

/**
 * N virtual threads each block in Socket.read(). Which platform threads exist meanwhile?
 * Args: [N, default 2000] [seconds to hold before releasing them, default 0]
 */
public class PollerDemo {
    public static void main(String[] args) throws Exception {
        int n = args.length > 0 ? Integer.parseInt(args[0]) : 2_000;
        int holdSeconds = args.length > 1 ? Integer.parseInt(args[1]) : 0;
        System.out.println("java " + System.getProperty("java.version") + ", cpus=" + Runtime.getRuntime().availableProcessors()
                + ", pid=" + ProcessHandle.current().pid());
        try (ServerSocket server = new ServerSocket(0, n, InetAddress.getLoopbackAddress());
             ExecutorService readers = Executors.newVirtualThreadPerTaskExecutor()) {
            CountDownLatch connected = new CountDownLatch(n), done = new CountDownLatch(n);
            for (int i = 0; i < n; i++) {
                readers.submit(() -> {
                    try (Socket s = new Socket(InetAddress.getLoopbackAddress(), server.getLocalPort())) {
                        connected.countDown();
                        s.getInputStream().read();                    // parks this virtual thread on the JDK poller
                    } catch (IOException e) {
                        e.printStackTrace();
                    } finally {
                        done.countDown();
                    }
                });
            }
            List<Socket> accepted = new ArrayList<>();
            for (int i = 0; i < n; i++) accepted.add(server.accept());
            connected.await();
            Thread.sleep(300);                                        // let every reader reach read()

            Map<String, Long> platform = Thread.getAllStackTraces().keySet().stream()   // platform threads only
                    .collect(Collectors.groupingBy(t -> t.getName().replaceAll("\\d+", "N"), TreeMap::new, Collectors.counting()));
            System.out.println(n + " virtual threads blocked in read(); platform threads: "
                    + platform.values().stream().mapToLong(Long::longValue).sum());
            platform.forEach((name, count) -> System.out.println("   " + count + " x " + name));
            if (holdSeconds > 0) {
                System.out.println("holding " + holdSeconds + " s: try jcmd " + ProcessHandle.current().pid() + " Thread.dump_to_file -format=json dump.json");
                Thread.sleep(holdSeconds * 1_000L);
            }

            long t0 = System.nanoTime();
            for (Socket s : accepted) s.getOutputStream().write(1);   // data arrives: the poller unparks each reader
            done.await();
            System.out.printf("wrote 1 byte to each socket: all %,d readers woke and finished in %d ms%n",
                    n, (System.nanoTime() - t0) / 1_000_000);
            for (Socket s : accepted) s.close();
        }
    }
}
