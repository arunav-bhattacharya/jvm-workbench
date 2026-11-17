package workbench.generics.l09.demo;

/** Java twin of ClassApiDemo.kt: the same checks and names, on java.lang.Class. */
public class ClassApiDemoJava {
    public static void main(String[] args) {
        Fruit fruit = new Apple("Gala", 180);

        Class<Apple> c = Apple.class;
        System.out.println("c.getSimpleName() = " + c.getSimpleName() + ", fruit.getClass() == c: " + (fruit.getClass() == c));

        System.out.println("isInstance: " + c.isInstance(fruit) + ", cast(...).getGrams(): " + c.cast(fruit).getGrams()
            + ", no safeCast in Java: " + (Lemon.class.isInstance(fruit) ? Lemon.class.cast(fruit) : null));
        try {
            Lemon.class.cast(fruit);
        } catch (ClassCastException e) {
            System.out.println("cast failed: " + e.getMessage());
        }

        System.out.println("getSimpleName = " + c.getSimpleName() + ", getName = " + c.getName());
        System.out.println("int.class = " + int.class + ", Integer.class = " + Integer.class);
    }
}
