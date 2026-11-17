package workbench.generics.l05.demo;

import java.util.List;

/**
 * Java twin of BinDemo.kt. Java has no `in` on a declaration, so Bin<T> stays invariant, and the
 * method that wants "a bin for apples, or for anything more general" says so at the use site: ? super.
 * Fruit and Apple are the Kotlin types from BinDemo.kt.
 */
public class BinDemoJava {

    interface Bin<T> {
        void drop(T item);
    }

    static final Bin<Fruit> COMPOST = f -> System.out.println("compost: " + f + ", " + f.getGrams() + " g");

    // ? super Apple: "a Bin of Apple or of some supertype". Without it, the compost bin would not fit.
    static void throwOut(List<Apple> apples, Bin<? super Apple> into) {
        for (Apple a : apples) into.drop(a);
    }

    public static void main(String[] args) {
        throwOut(List.of(new Apple("Gala", 180), new Apple("Fuji", 150)), COMPOST);

        Bin<? super Apple> appleBin = COMPOST;      // the Java spelling of Kotlin's Bin<Apple>
        appleBin.drop(new Apple("Fuji", 140));

        // Wrong move. Uncomment, predict the error, then run.
        // Bin<Apple> strict = COMPOST;
    }
}
