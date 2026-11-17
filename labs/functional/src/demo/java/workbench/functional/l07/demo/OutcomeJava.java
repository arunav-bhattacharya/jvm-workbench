package workbench.functional.l07.demo;

import java.util.List;
import java.util.function.Function;

/** The same result type in Java 21. Without declaration-site variance and Nothing, Err must be rebuilt each step. */
public class OutcomeJava {
    sealed interface Outcome<E, A> {
        default <B> Outcome<E, B> map(Function<? super A, ? extends B> f) {
            return switch (this) {
                case Ok<E, A> ok -> new Ok<>(f.apply(ok.value()));
                case Err<E, A> err -> new Err<>(err.error());      // a new Err with a new type
            };
        }

        default <B> Outcome<E, B> andThen(Function<? super A, Outcome<E, B>> f) {
            return switch (this) {
                case Ok<E, A> ok -> f.apply(ok.value());
                case Err<E, A> err -> new Err<>(err.error());
            };
        }
    }
    record Ok<E, A>(A value) implements Outcome<E, A> {}
    record Err<E, A>(E error) implements Outcome<E, A> {}

    sealed interface BakeErr {}
    record Invalid(String why) implements BakeErr {}
    record BowlTooSmall() implements BakeErr {}

    record Batter(int flourGrams) {}

    static Outcome<BakeErr, Batter> check(Batter b) {
        System.out.println("  check");
        return b.flourGrams() > 0 ? new Ok<>(b) : new Err<>(new Invalid("flour<=0"));
    }

    static Outcome<BakeErr, String> mix(Batter b) {
        System.out.println("  mix");
        return b.flourGrams() <= 1_000 ? new Ok<>("dough") : new Err<>(new BowlTooSmall());
    }

    static Outcome<BakeErr, String> bake(String dough) {
        System.out.println("  bake");
        return new Ok<>("loaf from " + dough);
    }

    static Outcome<BakeErr, String> makeLoaf(Batter b) {
        return check(b).andThen(OutcomeJava::mix).andThen(OutcomeJava::bake).map(String::toUpperCase);
    }

    public static void main(String[] args) {
        for (Batter b : List.of(new Batter(500), new Batter(-1), new Batter(5_000))) {
            System.out.println(b + ":");
            System.out.println("  -> " + makeLoaf(b));
        }
    }
}
