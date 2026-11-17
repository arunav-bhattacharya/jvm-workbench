package workbench.patterns.l03;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/**
 * The Java twin of DslScope.kt. Java has no lambdas with receivers, so each block is a Consumer
 * that gets its builder as a named parameter.
 */
public class DslScopeJava {
    record Stop(String orderId, int parcels) {}
    record Round(String driver, List<Stop> stops) {}

    static final class StopsBuilder {
        private final List<Stop> stops = new ArrayList<>();
        StopsBuilder stop(String orderId, int parcels) { stops.add(new Stop(orderId, parcels)); return this; }
        List<Stop> build() { return List.copyOf(stops); }
    }

    static final class RoundBuilder {
        private String driver = "unassigned";
        private List<Stop> stops = List.of();
        RoundBuilder driver(String d) { driver = d; return this; }
        RoundBuilder stops(Consumer<StopsBuilder> block) {
            StopsBuilder b = new StopsBuilder();
            block.accept(b);
            stops = b.build();
            return this;
        }
        Round build() { return new Round(driver, stops); }
    }

    static Round round(Consumer<RoundBuilder> block) {
        RoundBuilder b = new RoundBuilder();
        block.accept(b);
        return b.build();
    }

    public static void main(String[] args) {
        Round r = round(rb -> {
            rb.driver("Sam");
            rb.stops(s -> {
                s.stop("o-101", 2);
                s.stop("o-102", 3);
                // rb.driver("oops");   // step 4 of the Try it: this compiles, but you have to name rb
            });
        });
        System.out.println(r);
        System.out.println("parcels on the van: " + r.stops().stream().mapToInt(Stop::parcels).sum());
    }
}
