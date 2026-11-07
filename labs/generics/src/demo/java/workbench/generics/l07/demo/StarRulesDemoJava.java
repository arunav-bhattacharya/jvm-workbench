package workbench.generics.l07.demo;

/** Java twin of StarRulesDemo.kt. Java's ? keeps the declared bound, like Kotlin's *. */
public class StarRulesDemoJava {

    interface Source<T extends Number> { T next(); }
    interface Sink<T> { void accept(T item); }
    static final class Box<T> {
        T item;
        Box(T item) { this.item = item; }
    }

    static Number peek(Source<?> source) { return source.next(); }   // the bound survives the ?
    static Object peek(Box<?> box) { return box.item; }

    public static void main(String[] args) {
        Source<Integer> amounts = () -> 1_200;
        Sink<String> audit = item -> System.out.println("audit " + item);
        Box<String> box = new Box<>("EUR");

        System.out.println("peek(source) = " + peek(amounts) + ", peek(box) = " + peek(box));

        audit.accept("pay_0");                      // through the real type: fine
        Sink<?> anySink = audit;                    // through ?: only null can be passed in
        anySink.accept(null);                       // Java lets null through a ?; Kotlin's * does not
        Box<?> anyBox = box;
        System.out.println("a Box<?> still reads: " + anyBox.item);

        // Wrong moves. Uncomment one at a time, predict the error, then run.
        // anySink.accept("pay_1");                // 1
        // anyBox.item = "USD";                    // 2
        // Integer n = peek(amounts);              // 3
    }
}
