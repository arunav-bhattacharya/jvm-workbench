package workbench.generics.l01.demo;

/** Java twin of AnyBoxDemo.kt: a storeroom box that holds Object. It compiles, and fails far from the bug. */
public class AnyBoxDemoJava {

    static class AnyBox {
        Object value;
        AnyBox(Object value) { this.value = value; }
    }

    // the back room: restocks the box before the shop opens
    static void restock(AnyBox box) {
        box.value = 12;                             // the bug: how many apples, not which variety
    }

    // the counter: reads the box much later, in another part of the program
    static String signFor(AnyBox box) {
        String variety = (String) box.value;        // the cast fails HERE, not where 12 went in
        return "Today's apple: " + variety;
    }

    public static void main(String[] args) {
        AnyBox box = new AnyBox("Gala");
        restock(box);
        System.out.println("restock() returned. Nothing has failed yet.");
        try {
            System.out.println(signFor(box));
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
            System.out.println("thrown in: " + e.getStackTrace()[0]);
        }
    }
}
