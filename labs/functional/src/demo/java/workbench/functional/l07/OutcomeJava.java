package workbench.functional.l07;

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

    sealed interface PayErr {}
    record Invalid(String why) implements PayErr {}
    record Declined() implements PayErr {}

    record Req(long amountMinor, String currency) {}

    static Outcome<PayErr, Req> validate(Req r) {
        System.out.println("  validate");
        return r.amountMinor() > 0 ? new Ok<>(r) : new Err<>(new Invalid("amount<=0"));
    }

    static Outcome<PayErr, String> authorise(Req r) {
        System.out.println("  authorise");
        return r.amountMinor() < 10_000 ? new Ok<>("auth-1") : new Err<>(new Declined());
    }

    static Outcome<PayErr, String> capture(String auth) {
        System.out.println("  capture");
        return new Ok<>("cap-of-" + auth);
    }

    static Outcome<PayErr, String> pay(Req r) {
        return validate(r).andThen(OutcomeJava::authorise).andThen(OutcomeJava::capture).map(String::toUpperCase);
    }

    public static void main(String[] args) {
        for (Req r : List.of(new Req(500, "EUR"), new Req(-1, "EUR"), new Req(50_000, "EUR"))) {
            System.out.println(r + ":");
            System.out.println("  -> " + pay(r));
        }
    }
}
