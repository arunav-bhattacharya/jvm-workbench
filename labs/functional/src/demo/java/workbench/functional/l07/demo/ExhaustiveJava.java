package workbench.functional.l07.demo;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/** The same closed set of failures with Java 21 sealed interfaces, records and an exhaustive switch. */
public class ExhaustiveJava {
    sealed interface JarFailure {}
    record InvalidAmount(int grams) implements JarFailure {}
    record PastBestBefore() implements JarFailure {}
    record NotEnough(int shortByGrams) implements JarFailure {}
    // Uncomment the next line and run again.
    // record JarMissing() implements JarFailure {}

    sealed interface TakeResult {}
    record Taken(int leftGrams) implements TakeResult {}
    record Refused(JarFailure reason) implements TakeResult {}

    static TakeResult takeFlour(int grams, int leftGrams, LocalDate bestBefore, LocalDate today) {
        if (grams <= 0) return new Refused(new InvalidAmount(grams));
        if (today.isAfter(bestBefore)) return new Refused(new PastBestBefore());
        if (grams > leftGrams) return new Refused(new NotEnough(grams - leftGrams));
        return new Taken(leftGrams - grams);
    }

    /** The one place that knows what to tell the cook: an exhaustive switch with no default branch. */
    static String advice(JarFailure failure) {
        return switch (failure) {
            case InvalidAmount a -> "check the amount";
            case PastBestBefore p -> "open a new bag";
            case NotEnough n -> "buy more flour";
        };
    }

    public static void main(String[] args) {
        LocalDate today = LocalDate.of(2026, 3, 10);
        LocalDate fresh = LocalDate.of(2026, 3, 31);
        LocalDate old = LocalDate.of(2026, 2, 28);
        List<Map.Entry<Integer, LocalDate>> attempts =
                List.of(Map.entry(200, fresh), Map.entry(-5, fresh), Map.entry(200, old), Map.entry(1_000, fresh));
        for (var a : attempts) {
            String line = switch (takeFlour(a.getKey(), 700, a.getValue(), today)) {
                case Taken t -> "ok: " + t.leftGrams() + " g left";
                case Refused r -> advice(r.reason()) + ": " + r.reason();
            };
            System.out.println(line);
        }
    }
}
