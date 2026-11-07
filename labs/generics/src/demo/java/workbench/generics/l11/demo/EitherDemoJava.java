package workbench.generics.l11.demo;

import java.util.function.Function;

/**
 * Java twin of EitherDemo.kt, with a sealed interface and records (Java 21 pattern matching).
 * Java has no Nothing, so Left must carry an R it never uses, and mapLeft must build a new Right.
 */
public class EitherDemoJava {

    sealed interface Either<L, R> permits Left, Right {}
    record Left<L, R>(L value) implements Either<L, R> {}
    record Right<L, R>(R value) implements Either<L, R> {}

    static <L, R, L2> Either<L2, R> mapLeft(Either<L, R> e, Function<? super L, ? extends L2> f) {
        return switch (e) {
            case Left<L, R> l -> new Left<>(f.apply(l.value()));
            case Right<L, R> r -> new Right<>(r.value());        // can't reuse r: it is an Either<L, R>
        };
    }

    static <L, R, T> T fold(Either<L, R> e, Function<? super L, ? extends T> onLeft, Function<? super R, ? extends T> onRight) {
        return switch (e) {
            case Left<L, R> l -> onLeft.apply(l.value());
            case Right<L, R> r -> onRight.apply(r.value());
        };
    }

    static Either<String, Long> parseCents(String text) {
        try {
            return new Right<>(Long.parseLong(text));
        } catch (NumberFormatException ex) {
            return new Left<>("not a number: " + text);
        }
    }

    public static void main(String[] args) {
        Either<String, Long> ok = parseCents("1200");
        Either<String, Long> bad = parseCents("12,00");
        System.out.println(EitherDemoJava.<String, Long, String>fold(ok, l -> "error: " + l, r -> "cents: " + r));
        System.out.println(mapLeft(bad, String::toUpperCase));

        Either<? extends Object, ? extends Number> wider = ok;     // Java: wildcards at the use site
        System.out.println("wider = " + wider);
    }
}
