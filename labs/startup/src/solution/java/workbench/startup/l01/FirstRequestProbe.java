package workbench.startup.l01;

import java.io.IOException;
import java.net.ConnectException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/**
 * Measures time to first request from outside the process: keep asking until the service
 * answers 200. This is the clock a load balancer or a Kubernetes readiness probe sees.
 */
public final class FirstRequestProbe {

    /**
     * What the probe saw. {@code outcomes} has one entry per attempt, in order: the HTTP status
     * as a string ("503", "200"), or "refused" when nothing was listening on the port yet.
     */
    public record Result(List<String> outcomes, Duration elapsed) {
        public boolean ready() {
            return !outcomes.isEmpty() && outcomes.get(outcomes.size() - 1).equals("200");
        }
    }

    private FirstRequestProbe() {
    }

    /** Sends {@code GET uri} until it answers 200 or {@code maxAttempts} attempts have run. */
    public static Result await(HttpClient client, URI uri, int maxAttempts, Duration pause)
            throws InterruptedException {
        HttpRequest request = HttpRequest.newBuilder(uri).timeout(Duration.ofSeconds(2)).GET().build();
        List<String> outcomes = new ArrayList<>();
        long start = System.nanoTime();
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                // 1. one GET; the body doesn't matter, only that the service answered
                int status = client.send(request, HttpResponse.BodyHandlers.discarding()).statusCode();
                outcomes.add(Integer.toString(status));
                if (status == 200) {
                    break;                                  // 2. ready: stop the clock here
                }
            } catch (ConnectException e) {
                outcomes.add("refused");                    // 3. nothing listening yet: not an error
            } catch (IOException e) {
                outcomes.add("io-error");                   //    reset mid-start-up and similar
            }
            if (attempt < maxAttempts) {
                Thread.sleep(pause);                        // 4. pause between attempts only
            }
        }
        return new Result(List.copyOf(outcomes), Duration.ofNanos(System.nanoTime() - start));
    }
}
