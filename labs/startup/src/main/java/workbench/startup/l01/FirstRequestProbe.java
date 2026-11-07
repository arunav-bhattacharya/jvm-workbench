package workbench.startup.l01;

import java.net.URI;
import java.net.http.HttpClient;
import java.time.Duration;
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

    /**
     * Sends {@code GET uri} until it answers 200 or {@code maxAttempts} attempts have run.
     *
     * <p>TODO:
     * <ul>
     *   <li>record one outcome per attempt (see {@link Result}),</li>
     *   <li>stop as soon as an attempt gets 200,</li>
     *   <li>a refused connection ({@code java.net.ConnectException}) means "not up yet":
     *       record "refused" and try again, never let it escape,</li>
     *   <li>sleep {@code pause} between attempts (not after the last one),</li>
     *   <li>{@code elapsed} is the time from the first send to the last answer.</li>
     * </ul>
     */
    public static Result await(HttpClient client, URI uri, int maxAttempts, Duration pause)
            throws InterruptedException {
        throw new UnsupportedOperationException("TODO: poll the URI until it answers 200");
    }
}
