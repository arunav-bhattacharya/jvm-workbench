package workbench.patterns.l06;

import java.util.ArrayList;
import java.util.List;

/** A fee plan as a tree. Leaves and groups share one sealed type, so one switch prices them all. */
public class CompositeDemo {
    sealed interface Rule permits Flat, Percent, AllOf {}
    record Flat(long minor) implements Rule {}
    record Percent(int bps) implements Rule {}
    record AllOf(List<Rule> rules) implements Rule {
        AllOf { rules = List.copyOf(rules); }          // copy what we were given: the tree stays immutable
    }

    static long fee(Rule r, long amountMinor) {
        return switch (r) {                             // no default: a new node type breaks the build
            case Flat f -> f.minor();
            case Percent p -> amountMinor * p.bps() / 10_000;
            case AllOf a -> a.rules().stream().mapToLong(x -> fee(x, amountMinor)).sum();
        };
    }

    static String describe(Rule r) {
        return switch (r) {
            case Flat f -> Long.toString(f.minor());
            case Percent p -> String.format("%d.%02d%%", p.bps() / 100, p.bps() % 100);
            case AllOf a -> "(" + String.join(" + ", a.rules().stream().map(CompositeDemo::describe).toList()) + ")";
        };
    }

    public static void main(String[] args) {
        List<Rule> bundle = new ArrayList<>(List.of(new Flat(5)));
        Rule plan = new AllOf(List.of(new Flat(30), new Percent(290), new AllOf(bundle)));
        System.out.println("plan: " + describe(plan));
        System.out.println("fee on 100.00: " + fee(plan, 10_000));
        System.out.println("fee on 1,000.00: " + fee(plan, 100_000));

        bundle.add(new Flat(1_000));                    // someone edits the list they passed in
        System.out.println("after editing the source list: " + describe(plan));
    }
}
