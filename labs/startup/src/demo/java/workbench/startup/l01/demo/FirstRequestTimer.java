package workbench.startup.l01.demo;

import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * Launches a tiny HTTP service in a second JVM and reads three clocks: the JVM's own
 * "Create VM" line (pass -Xlog:startuptime), the service's "started in" line, and the time
 * to the first 200, measured from outside. Then it reads the service's RSS.
 */
public class FirstRequestTimer {
    public static void main(String[] args) throws Exception {
        if (args.length > 1 && args[0].equals("--serve")) {
            serve(Integer.parseInt(args[1]));
            return;
        }
        int port;
        try (ServerSocket s = new ServerSocket(0, 1, InetAddress.getLoopbackAddress())) {
            port = s.getLocalPort();                     // a free port for the service
        }
        List<String> cmd = new ArrayList<>();
        cmd.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        cmd.addAll(List.of(args));                       // e.g. -Xlog:startuptime, -Xshare:off
        cmd.addAll(List.of("-cp", System.getProperty("java.class.path"),
                FirstRequestTimer.class.getName(), "--serve", Integer.toString(port)));

        // 1. warm up our own HTTP client (nothing listens yet), then start the clock and the service
        HttpClient client = HttpClient.newBuilder().proxy(HttpClient.Builder.NO_PROXY).build();
        HttpRequest hello = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/hello")).build();
        try {
            client.send(hello, HttpResponse.BodyHandlers.ofString());
        } catch (IOException expected) {
            // refused: good, the client's own classes are loaded now
        }
        long t0 = System.nanoTime();
        Process service = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        List<String> serviceLog = new CopyOnWriteArrayList<>();
        Thread.ofPlatform().daemon().start(() -> service.inputReader().lines().forEach(serviceLog::add));

        // 2. poll from outside every 2 ms until the first 200
        int attempts = 0;
        long firstOk = -1;
        while (firstOk < 0 && System.nanoTime() - t0 < Duration.ofSeconds(8).toNanos()) {
            attempts++;
            try {
                if (client.send(hello, HttpResponse.BodyHandlers.ofString()).statusCode() == 200) {
                    firstOk = System.nanoTime() - t0;
                }
            } catch (IOException notUpYet) {
                Thread.sleep(2);
            }
        }

        // 3. footprint of the whole process, as the OS sees it, and the JVM's own accounting
        String rss = rss(service.pid());
        List<String> nmt = List.of(args).stream().anyMatch(a -> a.startsWith("-XX:NativeMemoryTracking"))
                ? nmt(service.pid()) : List.of();
        service.destroy();
        service.waitFor();

        System.out.printf("JDK %s, flags %s%n", Runtime.version(), List.of(args));
        serviceLog.stream().filter(l -> l.contains("Create VM") || l.contains("started in"))
                .forEach(l -> System.out.println("  log      : " + l));
        System.out.printf("  first 200: %d ms after launch, measured outside (%d attempts)%n",
                firstOk / 1_000_000, attempts);
        System.out.println("  RSS      : " + rss);
        nmt.forEach(l -> System.out.println("  NMT      : " + l));
    }

    /** Asks the running service for its Native Memory Tracking summary (needs -XX:NativeMemoryTracking=summary). */
    static List<String> nmt(long pid) throws Exception {
        String jcmd = Path.of(System.getProperty("java.home"), "bin", "jcmd").toString();
        Process p = new ProcessBuilder(jcmd, Long.toString(pid), "VM.native_memory", "summary", "scale=MB")
                .redirectErrorStream(true).start();
        try (var lines = p.inputReader().lines()) {
            return lines.filter(l -> l.contains("Total:") || l.contains("Java Heap ("))
                    .map(l -> l.replace("-", "").trim()).toList();
        }
    }

    /** RSS from /proc on Linux, from ps elsewhere. Both count the whole process, not just the heap. */
    static String rss(long pid) throws Exception {
        Path status = Path.of("/proc", Long.toString(pid), "status");
        if (Files.exists(status)) {
            List<String> keep = Files.readAllLines(status).stream()
                    .filter(l -> l.startsWith("VmRSS") || l.startsWith("RssAnon") || l.startsWith("RssFile"))
                    .map(l -> l.replaceAll("\\s+", " "))
                    .toList();
            return String.join(", ", keep);
        }
        Process ps = new ProcessBuilder("ps", "-o", "rss=", "-p", Long.toString(pid)).start();
        return new String(ps.getInputStream().readAllBytes(), StandardCharsets.UTF_8).trim() + " kB (ps)";
    }

    /** The service: one endpoint, and a Quarkus-style "started in" line, from the JVM's uptime. */
    static void serve(int port) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), port), 0);
        server.createContext("/hello", exchange -> {
            byte[] body = "{\"status\":\"AUTHORIZED\",\"amountMinor\":1250}".getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, body.length);
            exchange.getResponseBody().write(body);
            exchange.close();
        });
        server.start();
        long uptimeMs = ManagementFactory.getRuntimeMXBean().getUptime();   // since the JVM started
        System.out.printf("started in %.3fs. Listening on: http://127.0.0.1:%d%n", uptimeMs / 1000.0, port);
    }
}
