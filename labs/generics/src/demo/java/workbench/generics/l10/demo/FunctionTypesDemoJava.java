package workbench.generics.l10.demo;

import java.math.BigDecimal;
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
        Function<String, Long> toGrams = s -> new BigDecimal(s).movePointRight(3).longValueExact();   // kilograms to grams
        Function<Object, String> describe = x -> "<" + x + ">";
        Function<String, CharSequence> pipeline = andThen(toGrams, describe);
        System.out.println("pipeline(\"1.25\") = " + pipeline.apply("1.25"));
        System.out.println("JDK andThen: " + toGrams.andThen(describe).apply("0.35"));

        List<Apple> none = Collections.emptyList();            // generic method: T inferred as Apple
        long strict = Long.parseLong("180");
        System.out.println("none = " + none + ", strict = " + strict);

        Consumer<Apple> signWriter = a -> System.out.println("sign for " + a.getName());   // no type aliases in Java
        signWriter.accept(new Apple("Gala", 180));
    }
}
