package workbench.generics.l08.demo;

/**
 * Java twin of ClassTokenDemo.kt. It calls the Kotlin functions in ClassTokenDemo.kt directly:
 * the Class-token version works from Java, and the reified one does not exist for javac.
 */
public class ClassTokenDemoJava {
    public static void main(String[] args) {
        Apple apple = ClassTokenDemoKt.defaultOf(Apple.class);
        Lemon lemon = ClassTokenDemoKt.defaultOf(Lemon.class);
        String blank = ClassTokenDemoKt.defaultOf(String.class);
        System.out.println("apple = " + apple + ", lemon = " + lemon + ", blank = '" + blank + "'");

        // Java has the same primitive trap: int.class and Integer.class are different Class objects.
        System.out.println("int.class = " + int.class + ", Integer.class = " + Integer.class);

        // Wrong move. Uncomment, predict the error, then run.
        // Apple viaReified = ClassTokenDemoKt.<Apple>defaultOf();
    }
}
