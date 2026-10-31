package workbench.patterns.l03;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/** A record with a small builder: the record validates, the builder only collects. */
public class RecordBuilderDemo {

    record IssuerCall(String url, String method, Map<String, String> headers, Duration timeout, int maxRetries) {
        IssuerCall {                                         // every path to an IssuerCall runs this
            Objects.requireNonNull(url, "url");
            headers = Map.copyOf(headers);                   // really immutable
            if (maxRetries < 0) throw new IllegalArgumentException("maxRetries must be >= 0, was " + maxRetries);
        }

        IssuerCall withTimeout(Duration t) {                 // a hand-written "wither"
            return new IssuerCall(url, method, headers, t, maxRetries);
        }

        IssuerCall withMaxRetries(int n) {
            return new IssuerCall(url, method, headers, timeout, n);
        }

        static Builder builder(String url) { return new Builder(url); }

        static final class Builder {
            private final String url;
            private String method = "GET";
            private final Map<String, String> headers = new LinkedHashMap<>();
            private Duration timeout = Duration.ofSeconds(2);
            private int maxRetries = 0;

            private Builder(String url) { this.url = url; }
            Builder method(String m) { method = m; return this; }
            Builder header(String k, String v) { headers.put(k, v); return this; }
            Builder timeout(Duration t) { timeout = t; return this; }
            Builder maxRetries(int n) { maxRetries = n; return this; }
            IssuerCall build() { return new IssuerCall(url, method, headers, timeout, maxRetries); }
        }
    }

    public static void main(String[] args) {
        IssuerCall call = IssuerCall.builder("https://issuer.example/authorize")
                .method("POST")
                .header("Idempotency-Key", "auth-7731")
                .maxRetries(2)
                .build();
        System.out.println("built:        " + call);
        System.out.println("faster copy:  " + call.withTimeout(Duration.ofMillis(800)).timeout());

        try {
            call.headers().put("X-Debug", "1");
        } catch (UnsupportedOperationException e) {
            System.out.println("headers:      unmodifiable");
        }

        try {
            call.withMaxRetries(-1);                          // the wither can't skip validation either
        } catch (IllegalArgumentException e) {
            System.out.println("wither:       " + e.getMessage());
        }
    }
}
