package workbench.generics.l04.demo;

/**
 * Java twin of PositionsDemo.kt. Java cannot mark a declaration `out`, so the same rule shows up
 * where you USE the type: through a `? extends` reference you may call methods that return T,
 * and javac refuses calls that pass a T in.
 */
public class PositionsDemoJava {

    interface Producer<T> {
        T produce();
        void consume(T item);                // allowed in the declaration: Java checks the use site
    }

    public static void main(String[] args) {
        Producer<String> strings = new Producer<>() {
            String last = "EUR";
            public String produce() { return last; }
            public void consume(String item) { last = item; }
        };
        Producer<? extends Object> view = strings;     // the Java spelling of "used as Producer<out Any>"
        Object out = view.produce();                    // fine: out-position
        System.out.println("produced " + out);

        // Wrong move. Uncomment, predict the error, then run.
        // view.consume("USD");
    }
}
