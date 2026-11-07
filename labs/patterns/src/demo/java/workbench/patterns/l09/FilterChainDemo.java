package workbench.patterns.l09;

import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** An OkHttp-style interceptor chain in front of a charge endpoint. The order of the list is behavior. */
public class FilterChainDemo {
    record Request(String path, Map<String, String> headers) {}
    record Response(int status, String body) {}

    interface Chain { Response proceed(Request r); }
    interface Interceptor { Response intercept(Request r, Chain next); }

    // fold the interceptors into one chain, from the last to the first
    static Chain chain(List<Interceptor> interceptors, Chain terminal) {
        Chain next = terminal;
        for (int i = interceptors.size() - 1; i >= 0; i--) {
            Interceptor ic = interceptors.get(i);
            Chain rest = next;
            next = r -> ic.intercept(r, rest);
        }
        return next;
    }

    public static void main(String[] args) {
        int[] charges = {0};
        Set<String> seenKeys = new HashSet<>();

        Interceptor logging = (r, next) -> {
            Response res = next.proceed(r);                                   // in: nothing; out: log the status
            System.out.println("  log: " + r.path() + " -> " + res.status());
            return res;
        };
        Interceptor auth = (r, next) -> r.headers().containsKey("Authorization")
                ? next.proceed(r)
                : new Response(401, "no token");                              // short-circuit: stop here
        Interceptor idempotency = (r, next) -> seenKeys.add(r.headers().get("Idempotency-Key"))
                ? next.proceed(r)
                : new Response(409, "duplicate");
        Chain handler = r -> { charges[0]++; return new Response(200, "charged"); };

        Chain pipeline = chain(List.of(logging, auth, idempotency), handler);

        String token = "Bearer t0k";
        System.out.println(pipeline.proceed(new Request("/pay", Map.of("Authorization", token, "Idempotency-Key", "order-7781"))));
        System.out.println(pipeline.proceed(new Request("/pay", Map.of("Authorization", token, "Idempotency-Key", "order-7781"))));
        System.out.println(pipeline.proceed(new Request("/pay", Map.of("Idempotency-Key", "order-7782"))));   // token missing
        System.out.println(pipeline.proceed(new Request("/pay", Map.of("Authorization", token, "Idempotency-Key", "order-7782"))));   // fixed and retried
        System.out.println("charges: " + charges[0]);
    }
}
