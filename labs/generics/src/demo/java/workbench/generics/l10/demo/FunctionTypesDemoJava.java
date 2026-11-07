package workbench.generics.l10.demo;

import java.util.Collections;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Function;

/**
 * Java twin of FunctionTypesDemo.kt. Java's Function<T, R> is invariant, so the JDK writes the
 * variance into andThen's signature: andThen(Function<? super R, ? extends V> after).
 */
public class FunctionTypesDemoJava {

    static <A, B, C> Function<A, C> andThen(Function<A, ? extends B> first, Function<? super B, ? extends C> second) {
        return a -> second.apply(first.apply(a));
    }

    static <T> T fail(String reason) { throw new IllegalArgumentException(reason); }   // no Nothing: fake it with T

    public static void main(String[] args) {
        Function<String, Long> parseCents = s -> Long.parseLong(s.replace(".", ""));
        Function<Object, String> describe = x -> "<" + x + ">";
        Function<String, CharSequence> pipeline = andThen(parseCents, describe);
        System.out.println("pipeline(\"12.50\") = " + pipeline.apply("12.50"));
        System.out.println("JDK andThen: " + parseCents.andThen(describe).apply("3.50"));

        List<CardAuth> none = Collections.emptyList();         // generic method: T inferred as CardAuth
        long strict = Long.parseLong("1200");
        System.out.println("none = " + none + ", strict = " + strict);

        Consumer<CardAuth> audit = a -> System.out.println("audit " + a.getId());   // no type aliases in Java
        audit.accept(new CardAuth("pay_1"));
    }
}
