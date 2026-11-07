package workbench.nio.l01;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * Opens N idle connections to a blocking server and counts what they cost.
 * Args: [clients, default 2000] [seconds to hold the connections open, default 0]
 */
public class ThreadPerConnectionDemo {
    public static void main(String[] args) throws Exception {
        int clients = args.length > 0 ? Integer.parseInt(args[0]) : 2_000;
        int holdSeconds = args.length > 1 ? Integer.parseInt(args[1]) : 0;
        run("platform thread per connection", Executors.newCachedThreadPool(), clients, holdSeconds);
        run("virtual thread per connection", Executors.newVirtualThreadPerTaskExecutor(), clients, holdSeconds);
    }

    static void run(String label, ExecutorService handlers, int clients, int holdSeconds) throws Exception {
        ThreadMXBean mx = ManagementFactory.getThreadMXBean();   // counts platform threads only
        int before = mx.getThreadCount();
        List<Thread> handlerThreads = new CopyOnWriteArrayList<>();
        try (ServerSocket server = new ServerSocket(0, clients, InetAddress.getLoopbackAddress())) {
            Thread acceptor = new Thread(() -> {
                try {
                    while (true) {
                        Socket s = server.accept();
                        handlers.execute(() -> {
                            handlerThreads.add(Thread.currentThread());
                            try (s) {
                                s.getInputStream().read();      // blocks until the client sends a byte or closes
                            } catch (IOException ignored) { }
                        });
                    }
                } catch (IOException serverClosed) { }
            }, "acceptor");
            acceptor.setDaemon(true);
            acceptor.start();

            long t0 = System.nanoTime();
            List<Socket> open = new ArrayList<>();
            for (int i = 0; i < clients; i++) open.add(new Socket(InetAddress.getLoopbackAddress(), server.getLocalPort()));
            while (handlerThreads.size() < clients) Thread.sleep(10);
            System.out.printf("%s: %,d idle clients connected in %,d ms%n", label, clients, (System.nanoTime() - t0) / 1_000_000);
            System.out.printf("   platform threads: %d before, %d now%n", before, mx.getThreadCount());
            System.out.printf("   a handler blocked in read() reports state %s%n", handlerThreads.get(0).getState());
            if (holdSeconds > 0) {
                System.out.printf("   holding the connections for %d s (pid %d)%n", holdSeconds, ProcessHandle.current().pid());
                Thread.sleep(holdSeconds * 1_000L);
            }
            for (Socket s : open) s.close();
        }
        handlers.shutdown();
        handlers.awaitTermination(5, TimeUnit.SECONDS);
    }
}
