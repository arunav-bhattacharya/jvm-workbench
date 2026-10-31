package workbench.generics.l01.demo;

/** Java twin of AnyBoxDemo.kt: a settings box that holds Object. It compiles, and fails far from the bug. */
public class AnyBoxDemoJava {

    static class AnyBox {
        Object value;
        AnyBox(Object value) { this.value = value; }
    }

    // "module A": sets up the merchant's settlement currency
    static void configure(AnyBox box) {
        box.value = 978;                          // the bug: the ISO numeric code instead of "EUR"
    }

    // "module B": reads the setting much later, in another class, maybe another team's code
    static String currencyLabel(AnyBox box) {
        String code = (String) box.value;         // the cast fails HERE, not where 978 went in
        return "Settles in " + code;
    }

    public static void main(String[] args) {
        AnyBox box = new AnyBox("EUR");
        configure(box);
        System.out.println("configure() returned. Nothing has failed yet.");
        try {
            System.out.println(currencyLabel(box));
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
            System.out.println("thrown in: " + e.getStackTrace()[0]);
        }
    }
}
